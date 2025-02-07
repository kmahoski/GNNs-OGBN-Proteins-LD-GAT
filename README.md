# LD+GAT for OGBN-Proteins

Original implementation
[GitHub](https://github.com/MIRALab-USTC/LD)


Original paper on LD
[arxiv](http://arxiv.org/abs/2309.14907)

This is a slightly modified version of the original implementation of the Label Deconvolution (LD) method. Primarily, only the parts of the code that are relevant to the OGBN-Proteins dataset are left.

Additionally, there is some refactoring and adjustments to allow for easier experimentation with different protein language models that are used as node encoders.

Currently, models from the ESM2 family are being used, but in the future we can experiment with the newer, ESM C models.

## Dataset

[OGBN-Proteins](https://ogb.stanford.edu/docs/nodeprop/#ogbn-proteins)

Original OGB paper
[arxiv](https://arxiv.org/pdf/2005.00687)

## Node Encoders

One of the key aspects of the LD+GAT method is the use of a protein language model (from the ESM2 family) as a node encoder.

The authors use the 650M version of the model, but there are some smaller and larger versions.

[ESM on Hugging Face](https://huggingface.co/docs/transformers/en/model_doc/esm)

ESM2 Models

| Name                | Layers     | Parameters |
|---------------------|------------|------------|
| [esm2_t48_15B_UR50D](https://huggingface.co/facebook/esm2_t48_15B_UR50D)  | 48         | 15B        |
| [esm2_t36_3B_UR50D](https://huggingface.co/facebook/esm2_t36_3B_UR50D)   | 36         | 3B         |
| [esm2_t33_650M_UR50D](https://huggingface.co/facebook/esm2_t33_650M_UR50D) | 33         | 650M       |
| [esm2_t30_150M_UR50D](https://huggingface.co/facebook/esm2_t30_150M_UR50D) | 30         | 150M       |
| [esm2_t12_35M_UR50D](https://huggingface.co/facebook/esm2_t12_35M_UR50D)  | 12         | 35M        |
| [esm2_t6_8M_UR50D](https://huggingface.co/facebook/esm2_t6_8M_UR50D)    | 6          | 8M         |

## Environment

OS: Linux 6.12.10-200.fc41.x86_64

GPU: Nvidia

GPU Drivers: Proprietary, from X.Org (with CUDA)

CUDA Version: Build cuda_12.8.r12.8

Conda environment

Required packages:

- python=3.9.12
- ogb=1.3.3
- numpy=1.26.4
- dgl=2.4.0.th24.cu124
- pytorch=2.4.0+cu124
- pyg=2.6.1
- hydra-core=1.3.1

There are additional packages for the dependencies. An extensive list, along with a more detailed info is provided in conda-environment-packages.txt.






#### **ogbn-proteins**

- Default (ESM2 650M)

```
cd transformer
bash scripts/shell_protein_gat.sh
```

- ESM2 8M

```
cd transformer
bash scripts/shell_protein_gat_8M.sh
```

- ESM2 35M

```
cd transformer
bash scripts/shell_protein_gat_35M.sh
```
