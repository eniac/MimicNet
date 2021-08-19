#!/bin/bash

set -e
set -x

if [[ -z ${1} ]]; then
    echo "Usage: run_all.sh variant [simulate_options]"
    exit 1
fi

VARIANT=${1}

./run_1_compile.sh

exec 6>&1
RESULTS_DIR=$(./run_2_generate.sh $@ | tee /dev/fd/6 | tail -n 1)

exec 7>&1
MODEL_STR=$(./run_3_hypertrain.sh ${VARIANT} train/lstm/train_lstm_${VARIANT}.py \
                    ${RESULTS_DIR} tune/hp_configs/lstm_${VARIANT}.json \
                    | tee /dev/fd/7 | tail -n 1)

./run_4_mimicnet.sh ${VARIANT} ${MODEL_STR} ${@:2}
