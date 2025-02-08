from typing import Tuple

import torch
import torch_geometric.transforms as T
from torch_geometric.data import Data, Batch

import ogb
from ogb.nodeproppred import PygNodePropPredDataset, DglNodePropPredDataset
from ogb.linkproppred import PygLinkPropPredDataset, DglLinkPropPredDataset

from bert.wrapper.data_wrapper import PygNodeDataWrapper, DglDataWrapper, PygLinkDataWrapper, DglLinkDataWrapper

def index2mask(idx: torch.Tensor, size: int) -> torch.Tensor:
    mask = torch.zeros(size, dtype=torch.bool, device=idx.device)
    mask[idx] = True
    return mask

def get_proteins_dgl(root: str):
    dataset = DglNodePropPredDataset(root=f'{root}/OGB', name='ogbn-proteins')

    graph, labels = dataset[0]
    split_idx = dataset.get_idx_split()
    graph.ndata["labels"] = labels.float()

    evaluator = ogb.nodeproppred.Evaluator(name='ogbn-proteins')
    evaluator_wrapper = lambda pred, labels: evaluator.eval({"y_pred": pred, "y_true": labels})

    graph.ndata.pop('species')

    graph.ndata['train_mask'] = index2mask(split_idx['train'], graph.number_of_nodes())
    graph.ndata['val_mask'] = index2mask(split_idx['valid'], graph.number_of_nodes())
    graph.ndata['test_mask'] = index2mask(split_idx['test'], graph.number_of_nodes())
    
    return DglDataWrapper(graph), 0, labels.shape[1], evaluator_wrapper, "rocauc"

def get_proteins_pyg(root: str) -> Tuple[Data, int, int]:
    dataset = PygNodePropPredDataset('ogbn-proteins', f'{root}/OGB',
                                     pre_transform=T.ToSparseTensor())
    data = dataset[0]
    data.node_species = None
    split_idx = dataset.get_idx_split()
    data.train_mask = index2mask(split_idx['train'], data.num_nodes)
    data.val_mask = index2mask(split_idx['valid'], data.num_nodes)
    data.test_mask = index2mask(split_idx['test'], data.num_nodes)
    data.y = data.y.float()

    evaluator = ogb.nodeproppred.Evaluator(name='ogbn-proteins')
    evaluator_wrapper = lambda pred, labels: evaluator.eval({"y_pred": pred, "y_true": labels})

    return PygNodeDataWrapper(data), dataset.num_features, data.y.shape[1], evaluator_wrapper, "rocauc"

def get_data(root: str, name: str, mode='pyg') -> Tuple[Data, int, int]:
    if mode in ['pyg']:
        if name.lower() in ['ogbn-proteins', 'proteins']:
            return get_proteins_pyg(root)
        else:
            raise NotImplementedError
    elif mode in ['dgl']:
        if name.lower() in ['ogbn-proteins', 'proteins']:
            return get_proteins_dgl(root)
        else:
            raise NotImplementedError
    else:
        raise NotImplementedError
