#!/bin/bash

set -e
set -x

if [ $# -lt 4 ]; then
    echo "Usage ./run_3_hypertrain.sh variant train_script data_path search_space_file [hyperopt_options]"
    exit 1
fi

. /etc/profile.d/mimicnet.sh

VARIANT="${1}"
TRAIN_SCRIPT="${2}"
DATA_PATH="${3}"            # path_to_dataset: path to local directory
SEARCH_SPACE_FILE="${4}"    # search_space_file: File containing JSON

TIMESTAMP=`date +%Y%m%d_%H%M%S`
RESULTS_DIR="data/${TIMESTAMP}"
mkdir -p ${RESULTS_DIR}

echo "Using data set ${DATA_PATH}"
train/intermimic/train_intermimic_${VARIANT}.py ${DATA_PATH} 1.1. &
python3 tune/bayes_hyper_opt.py ${VARIANT} ${TRAIN_SCRIPT} \
        ${DATA_PATH} ${RESULTS_DIR} ${SEARCH_SPACE_FILE} ${@:5}
