#!/bin/bash

# 1. Source the conda setup script directly
# source /home/r_james/miniconda3/etc/profile.d/conda.sh

# 2. Activate your environment
# conda init
conda activate paper_pipeline

# 3. Run your python script
python /home/r_james/code/trader/data/paper_data_pipeline/src/main.py


# conda deactivate