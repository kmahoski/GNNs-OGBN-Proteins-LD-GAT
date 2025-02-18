# The LD+GAT Method for OGBN-Proteins

This is a slightly modified version of the original implementation of the Label Deconvolution (LD) method.

Only the pieces of the original implementation's code that are relevant to the OGBN-Proteins dataset remain in this version.

Additionally, there is some refactoring and adjustments to allow for easier experimentation with different protein language models that are used as node encoders.
- There are 3 sets of scripts (for 3 different versions of the node encoder model).
- For easier troubleshooting, print statements are added to each step of the main procedure (in *transformer/main_bertgnn.py*).

Currently, only ESM-2 models are being used as node encoders. The next step is to experiment with the newer, ESM Cambrian (ESM C) models.

- [Original implementation of LD (GitHub)](https://github.com/MIRALab-USTC/LD)

- [Original LD paper (arXiv)](http://arxiv.org/abs/2309.14907)

## Dataset

The OGBN-Proteins dataset is part of Stanford's Open Graph Benchmark (OGB). It is a protein-protein association network represented as an undirected weighted graph, typed according to species. Each node represents a specific protein, and each edge represents a specific biologically meaningful association between two proteins (physical interaction, co-expression, or homology).

- [Description (OGB Website)](https://ogb.stanford.edu/docs/nodeprop/#ogbn-proteins)

- [Original OGB paper (arXiv)](https://arxiv.org/pdf/2005.00687)

## Node Encoders

One of the key aspects of the LD+GAT method is the use of the **ESM-2 650M** model as a **node encoder**.

### ESM-2 Models

**Evolutionary Scale Modeling (ESM)**, with **ESM-2** and **ESMFold**, is a family of **transformer protein language models** from Meta AI's Fundamental AI Research Team.

- [Implementation (GitHub)](https://github.com/facebookresearch/esm)

- [Documentation (Hugging Face)](https://huggingface.co/docs/transformers/en/model_doc/esm)

#### Model Versions

These are the pre-trained models available on Hugging Face.

| Name                | Layers     | Parameters |
| :------------------ | :--------: | :--------: |
| [esm2_t48_15B_UR50D](https://huggingface.co/facebook/esm2_t48_15B_UR50D)  | 48         | 15B        |
| [esm2_t36_3B_UR50D](https://huggingface.co/facebook/esm2_t36_3B_UR50D)   | 36         | 3B         |
| [esm2_t33_650M_UR50D](https://huggingface.co/facebook/esm2_t33_650M_UR50D) | 33         | 650M       |
| [esm2_t30_150M_UR50D](https://huggingface.co/facebook/esm2_t30_150M_UR50D) | 30         | 150M       |
| [esm2_t12_35M_UR50D](https://huggingface.co/facebook/esm2_t12_35M_UR50D)  | 12         | 35M        |
| [esm2_t6_8M_UR50D](https://huggingface.co/facebook/esm2_t6_8M_UR50D)    | 6          | 8M         |

### ESM Cambrian Models

**ESM Cambrian** (or **ESM C**) is the newer family of models, that can be used as a *drop-in replacement* for ESM-2 models.

According to the developer of the model, [EvolutionaryScale](https://www.evolutionaryscale.ai):

> ESM C is designed as a drop-in replacement for ESM-2 and comes with major performance benefits. The 300M parameter ESM C delivers similar performance to ESM-2 650M with dramatically reduced memory requirements and faster inference. The 600M parameter ESM C rivals the 3B parameter ESM-2 and approaches the capabilities of the 15B model, delivering frontier performance with far greater efficiency. The 6B parameter ESM C outperforms the best ESM-2 models by a wide margin.

- [Blog article (EvolutionaryScale Website)](https://www.evolutionaryscale.ai/blog/esm-cambrian)

- [Implementation (GitHub)](https://github.com/evolutionaryscale/esm?tab=readme-ov-file#esm-c-)

- [Pre-trained models (Hugging Face)](https://huggingface.co/EvolutionaryScale)

#### Model Versions

These are the pre-trained models available on Hugging Face.
 
| Name                    | Parameters |
| :---------------------- | :--------: |
| [esmc-600m-2024-12](https://huggingface.co/EvolutionaryScale/esmc-600m-2024-12)  | 600M       |
| [esmc-300m-2024-12](https://huggingface.co/EvolutionaryScale/esmc-300m-2024-12)  | 300M       |

## Experimental Setup

### Operating System

Linux\
(kernel version 6.12.10-200.fc41.x86_64)

### Relevant Hardware and Drivers

**GPU:**\
Nvidia\
(originally tested with Quadro P1000)

**GPU Drivers:**\
Proprietary Nvidia drivers\
(X.Org X11) from *rpmfusion* (with CUDA support)

**CUDA Version:**\
Build cuda_12.8.r12.8

### Environment

Conda (version 25.1.1)

Main required packages:

- python=3.12.2
- ogb=1.3.6
- numpy=1.26.4
- dgl=2.4.0.th24.cu124
- pytorch=2.4.1
- pyg=2.6.1
- hydra-core=1.3.2

There are additional packages for the dependencies. An extensive list, along with a more detailed info is provided in *conda-environment-packages.txt*.

#### Notes on the Folder Structure

Git ignores the directory: *protein/data/*
- This directory should contain the protein sequences from the STRING database (one of the following versions).
  - [STRING v11.5 protein sequences](https://stringdb-downloads.org/download/protein.sequences.v11.5.fa.gz)
  - [STRING v12.0 protein sequences](https://stringdb-downloads.org/download/protein.sequences.v12.0.fa.gz)

The other important directories are:
- *OGB*
  - This directory should contain the OGBN-Proteins dataset.
  - In the config files, the dataset path is set to */home/\<USER\>/Desktop/OGB/ogbn_proteins/*.
  - This directory also contains the tokens generated by the ESM model, in */home/\<USER\>/Desktop/OGB/ogbn_proteins/token/facebook/\<MODEL_NAME\>/*.
    - The original authors of the LD method have provided the [tokens for esm2_t33_650M_UR50D](https://drive.google.com/drive/folders/107wQOd2YWyWofvPixWjM7YnTgaXUPGuR).
- *Models*
  - This directory should contain the node encoder (ESM) models.
  - In the config files, the model paths are set to */home/\<USER\>/Desktop/Models/\<MODEL_NAME\>/*.

## Running the Experiments

- ESM-2 650M (default)

```
cd transformer
bash scripts/shell_protein_gat.sh
```

- ESM-2 35M

```
cd transformer
bash scripts/shell_protein_gat_35M.sh
```

- ESM-2 8M

```
cd transformer
bash scripts/shell_protein_gat_8M.sh
```
