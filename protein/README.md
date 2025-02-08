```
mkdir data/
cd data
wget https://stringdb-downloads.org/download/protein.sequences.v11.5.fa.gz
% An alternative is to use v12.0, but the file name in protein/process_proteins.py would need to be changed accordingly.
# wget https://stringdb-downloads.org/download/protein.sequences.v12.0.fa.gz
cd ..

$OGB_PATH=/datasets/OGB/
python process_proteins.py --dataset_folder $OGB_PATH
python generate_token.py LM.params.proteins.token_folder=$OGB_PATH/ogbn_proteins/mapping/nodeidx2proteinid_seq.csv conf.LM.params.proteins.token_fold=$OGB_PATH/ogbn_proteins/token/
```
