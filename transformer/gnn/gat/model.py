import math
from functools import partial

import dgl.function as fn
import dgl.nn.pytorch as dglnn
import torch
import torch.nn as nn
import torch.nn.functional as F
from dgl import function as fn
from dgl._ffi.base import DGLError
from dgl.base import ALL
from dgl.nn.pytorch.utils import Identity
from dgl.ops import edge_softmax
from dgl.utils import expand_as_pair
from torch.nn import init
from torch.utils.checkpoint import checkpoint

from bert.bert_model import NodeClassifier
from gnn.gamlp.gamlp_utils import dgl_neighbor_average_features


class GATBertNodeClassifier(NodeClassifier):
    def inverse_label(self, graph,):
        # num_propagation = self.gnn_model.n_layers
        num_propagation = self.gnn_model.ld_layers

        xs = dgl_neighbor_average_features(self.label_emb, graph, num_propagation+1)
        xs = [self.label_emb.clone(),]+xs
        self.inv_label_emb = torch.stack(xs, dim=-1)
    
    def build_aggr_weight(self,):
        # self.aggr_weight = nn.Parameter(torch.ones(self.gnn_model.n_layers+1)/(self.gnn_model.n_layers+1))
        self.aggr_weight = nn.Parameter(torch.ones(self.gnn_model.ld_layers + 1)/self.gnn_model.ld_layers + 1)

    def gnn_inference(self, n_id_in, n_id_out, gnn_batch, cls_token_emb=None, lm_batch_id=None):
        gnn_x = self.hist_emb.pull(n_id_in.cpu())
        gnn_x = self.dropout(gnn_x)
        if cls_token_emb is not None and lm_batch_id is not None:
            gnn_x[lm_batch_id] = cls_token_emb

        gnn_batch[0].srcdata['feat'] = gnn_x
        
        logits = self.gnn_model(gnn_batch)

        labels = gnn_batch[-1].dstdata['labels']
        mask = gnn_batch[-1].dstdata['train_mask']

        loss = self.loss_func(logits[mask], labels[mask])
        return loss, logits, labels


class GATConv(nn.Module):
    def __init__(
        self,
        node_feats,
        edge_feats,
        out_feats,
        n_heads=1,
        attn_drop=0.0,
        edge_drop=0.0,
        negative_slope=0.2,
        residual=True,
        activation=None,
        use_attn_dst=True,
        allow_zero_in_degree=True,
        use_symmetric_norm=False,
    ):
        super(GATConv, self).__init__()
        self._n_heads = n_heads
        self._in_src_feats, self._in_dst_feats = expand_as_pair(node_feats)
        self._out_feats = out_feats
        self._allow_zero_in_degree = allow_zero_in_degree
        self._use_symmetric_norm = use_symmetric_norm

        # feat fc
        self.src_fc = nn.Linear(self._in_src_feats, out_feats * n_heads, bias=False)
        if residual:
            self.dst_fc = nn.Linear(self._in_src_feats, out_feats * n_heads)
            self.bias = None
        else:
            self.dst_fc = None
            self.bias = nn.Parameter(out_feats * n_heads)

        # attn fc
        self.attn_src_fc = nn.Linear(self._in_src_feats, n_heads, bias=False)
        if use_attn_dst:
            self.attn_dst_fc = nn.Linear(self._in_src_feats, n_heads, bias=False)
        else:
            self.attn_dst_fc = None
        if edge_feats > 0:
            self.attn_edge_fc = nn.Linear(edge_feats, n_heads, bias=False)
        else:
            self.attn_edge_fc = None

        self.attn_drop = nn.Dropout(attn_drop)
        self.edge_drop = edge_drop
        self.leaky_relu = nn.LeakyReLU(negative_slope, inplace=True)
        self.activation = activation
        self.fc_adjs = nn.Linear(out_feats * n_heads, out_feats * n_heads)
        self.fc_adjs2 = nn.Linear(out_feats * n_heads, out_feats * n_heads)

        self.reset_parameters()

    def reset_parameters(self):
        gain = nn.init.calculate_gain("relu")
        nn.init.xavier_normal_(self.src_fc.weight, gain=gain)
        if self.dst_fc is not None:
            nn.init.xavier_normal_(self.dst_fc.weight, gain=gain)

        nn.init.xavier_normal_(self.attn_src_fc.weight, gain=gain)
        if self.attn_dst_fc is not None:
            nn.init.xavier_normal_(self.attn_dst_fc.weight, gain=gain)
        if self.attn_edge_fc is not None:
            nn.init.xavier_normal_(self.attn_edge_fc.weight, gain=gain)

        if self.bias is not None:
            nn.init.zeros_(self.bias)

        nn.init.xavier_normal_(self.fc_adjs.weight, gain=gain)
        nn.init.xavier_normal_(self.fc_adjs2.weight, gain=gain)

    def set_allow_zero_in_degree(self, set_value):
        self._allow_zero_in_degree = set_value

    def pure_lin(self, feat_src):
        feat_src_fc = self.src_fc(feat_src)
        rst = feat_src_fc

        rst = rst.reshape(rst.shape[0], -1)
        rst = self.fc_adjs(rst)
        rst = F.relu(rst)
        rst = self.fc_adjs2(rst)
        rst = F.relu(rst)
        rst = rst.reshape(rst.shape[0], self._n_heads, -1)

        # residual
        if self.dst_fc is not None:
            rst = rst + self.dst_fc(feat_src).view(-1, self._n_heads, self._out_feats)
        else:
            rst = rst + self.bias

        # activation
        if self.activation is not None:
            rst = self.activation(rst, inplace=True)
        return rst

    def forward(self, graph, feat_src, feat_edge=None):
        with graph.local_scope():
            if not self._allow_zero_in_degree:
                if (graph.in_degrees() == 0).any():
                    assert False

            if graph.is_block:
                feat_dst = feat_src[: graph.number_of_dst_nodes()]
            else:
                feat_dst = feat_src

            if self._use_symmetric_norm:
                degs = graph.srcdata["deg"]
                # degs = graph.out_degrees().float().clamp(min=1)
                norm = torch.pow(degs, -0.5)
                shp = norm.shape + (1,) * (feat_src.dim() - 1)
                norm = torch.reshape(norm, shp)
                feat_src = feat_src * norm

            feat_src_fc = self.src_fc(feat_src).view(-1, self._n_heads, self._out_feats)
            feat_dst_fc = self.dst_fc(feat_dst).view(-1, self._n_heads, self._out_feats)
            attn_src = self.attn_src_fc(feat_src).view(-1, self._n_heads, 1)
            # NOTE: GAT paper uses "first concatenation then linear projection"
            # to compute attention scores, while ours is "first projection then
            # addition", the two approaches are mathematically equivalent:
            # We decompose the weight vector a mentioned in the paper into
            # [a_l || a_r], then
            # a^T [Wh_i || Wh_j] = a_l Wh_i + a_r Wh_j
            # Our implementation is much efficient because we do not need to
            # save [Wh_i || Wh_j] on edges, which is not memory-efficient. Plus,
            # addition could be optimized with DGL's built-in function u_add_v,
            # which further speeds up computation and saves memory footprint.
            graph.srcdata.update({"feat_src_fc": feat_src_fc, "attn_src": attn_src})

            if self.attn_dst_fc is not None:
                attn_dst = self.attn_dst_fc(feat_dst).view(-1, self._n_heads, 1)
                graph.dstdata.update({"attn_dst": attn_dst})
                graph.apply_edges(fn.u_add_v("attn_src", "attn_dst", "attn_node"))
            else:
                graph.apply_edges(fn.copy_u("attn_src", "attn_node"))

            e = graph.edata["attn_node"]
            if feat_edge is not None:
                attn_edge = self.attn_edge_fc(feat_edge).view(-1, self._n_heads, 1)
                graph.edata.update({"attn_edge": attn_edge})
                e += graph.edata["attn_edge"]
            e = self.leaky_relu(e)

            if self.training and self.edge_drop > 0:
                perm = torch.randperm(graph.number_of_edges(), device=e.device)
                bound = int(graph.number_of_edges() * self.edge_drop)
                eids = perm[bound:]
                graph.edata["a"] = torch.zeros_like(e)
                graph.edata["a"][eids] = self.attn_drop(edge_softmax(graph, e[eids], eids=eids))
            else:
                graph.edata["a"] = self.attn_drop(edge_softmax(graph, e))

            # message passing
            graph.update_all(fn.u_mul_e("feat_src_fc", "a", "m"), fn.sum("m", "feat_src_fc"))

            rst = graph.dstdata["feat_src_fc"]
            if self._use_symmetric_norm:
                degs = graph.dstdata["deg"]
                # degs = graph.in_degrees().float().clamp(min=1)
                norm = torch.pow(degs, 0.5)
                shp = norm.shape + (1,) * (feat_dst.dim())
                norm = torch.reshape(norm, shp)
                rst = rst * norm

            rst = rst.reshape(rst.shape[0],-1)
            rst = self.fc_adjs(rst)
            rst = F.relu(rst)
            rst = self.fc_adjs2(rst)
            rst = F.relu(rst)
            rst = rst.reshape(rst.shape[0], self._n_heads, -1)

            # residual
            if self.dst_fc is not None:
                rst = rst + feat_dst_fc
            else:
                rst = rst + self.bias

            # activation
            if self.activation is not None:
                rst = self.activation(rst, inplace=True)

            return rst


class GAT(nn.Module):
    def __init__(
        self,
        node_feats,
        edge_feats,
        ld_layers,
        n_classes,
        n_layers,
        n_heads,
        n_hidden,
        edge_emb,
        activation,
        dropout,
        input_drop,
        attn_drop,
        edge_drop,
        use_attn_dst=True,
        allow_zero_in_degree=False,
    ):
        super().__init__()
        self.n_layers = n_layers
        self.ld_layers = ld_layers
        self.n_heads = n_heads
        self.n_hidden = n_hidden
        self.n_classes = n_classes

        self.convs = nn.ModuleList()
        self.norms = nn.ModuleList()

        self.node_encoder = nn.Linear(node_feats, n_hidden)
        if edge_emb > 0:
            self.edge_encoder = nn.ModuleList()

        for i in range(n_layers):
            in_hidden = n_heads * n_hidden if i > 0 else n_hidden
            out_hidden = n_hidden
            # bias = i == n_layers - 1

            if edge_emb > 0:
                self.edge_encoder.append(nn.Linear(edge_feats, edge_emb))
            self.convs.append(
                GATConv(
                    in_hidden,
                    edge_emb,
                    out_hidden,
                    n_heads=n_heads,
                    attn_drop=attn_drop,
                    edge_drop=edge_drop,
                    use_attn_dst=use_attn_dst,
                    allow_zero_in_degree=allow_zero_in_degree,
                    use_symmetric_norm=False,
                )
            )
            self.norms.append(nn.BatchNorm1d(n_heads * out_hidden))

        self.pred_linear = nn.Linear(n_heads * n_hidden, n_classes)

        self.input_drop = nn.Dropout(input_drop)
        self.dropout = nn.Dropout(dropout)
        self.activation = activation

    def forward_lin(self, h):
        h = self.node_encoder(h)
        h = F.relu(h, inplace=True)
        h = self.input_drop(h)

        h_last = None

        for i in range(self.n_layers):

            h = self.convs[i].pure_lin(h,).flatten(1, -1)

            if h_last is not None:
                h += h_last

            h_last = h

            h = self.norms[i](h)
            h = self.activation(h, inplace=True)
            h = self.dropout(h)

        h = self.pred_linear(h)

        return h

    def forward(self, g):
        if not isinstance(g, list):
            subgraphs = [g] * self.n_layers
        else:
            subgraphs = g

        h = subgraphs[0].srcdata["feat"]
        h = self.node_encoder(h)
        h = F.relu(h, inplace=True)
        h = self.input_drop(h)

        h_last = None

        for i in range(self.n_layers):
            if self.edge_encoder is not None:
                efeat = subgraphs[i].edata["feat"]
                efeat_emb = self.edge_encoder[i](efeat)
                efeat_emb = F.relu(efeat_emb, inplace=True)
            else:
                efeat_emb = None

            h = self.convs[i](subgraphs[i], h, efeat_emb).flatten(1, -1)

            if h_last is not None:
                h += h_last[: h.shape[0], :]

            h_last = h
            h = self.norms[i](h)
            h = self.activation(h, inplace=True)
            h = self.dropout(h)
        h = self.pred_linear(h)

        return h


def get_model(conf, bert_model, out_channels):
    in_channels = int(conf.LM.params.feat_shrink) if conf.LM.params.feat_shrink else bert_model.config.hidden_size
    gnn_model = GAT(
        node_feats=in_channels,
        edge_feats=8,
        n_classes=out_channels,
        activation=F.relu,
        **conf.model.params.architecture
    )

    return gnn_model

