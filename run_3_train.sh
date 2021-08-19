#!/bin/bash

set -e
set -x

if [ $# -lt 3 ]; then
    echo "Usage ./run_3_train.sh variant train_script data_path
                       [train_options]"
    exit 1
fi

VARIANT="${1}"
TRAIN_SCRIPT="${2}"
DATA_PATH="${3}"            # path_to_dataset: path to local directory

echo "Using data set ${DATA_PATH}"
train/intermimic/train_intermimic_${VARIANT}.py ${DATA_PATH} 1.1. &
python ${TRAIN_SCRIPT} ${DATA_PATH}/in_data.pkl 2 --model_name ${DATA_PATH}/in_model --direction "INGRESS" ${@:4}
python ${TRAIN_SCRIPT} ${DATA_PATH}/in_data.pkl 2 --model_name ${DATA_PATH}/in_model --direction "EGRESS" ${@:4}

