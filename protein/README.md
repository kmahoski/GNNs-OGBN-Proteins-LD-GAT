```
mkdir data/
cd data

# Download the STRING database (v11.5):
wget https://stringdb-downloads.org/download/protein.sequences.v11.5.fa.gz

# Alternatively, to download v12.0 of the database:
# wget https://stringdb-downloads.org/download/protein.sequences.v12.0.fa.gz
# NOTE: In that case, the reference in the protein/process_proteins.py would need to be updated accordingly.

cd ..
OGB_PATH=/home/kliment/Desktop/OGB/
python process_proteins.py --dataset_folder $OGB_PATH
python generate_token.py LM.params.proteins.token_folder=$OGB_PATH/ogbn_proteins/mapping/nodeidx2proteinid_seq.csv conf.LM.params.proteins.token_fold=$OGB_PATH/ogbn_proteins/token/
```
