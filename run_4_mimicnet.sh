#!/bin/bash

set -e

if [ $# -lt 5 ]; then
    echo "Usage ./run_4_mimicnet.sh variant ingress_model egress_model intermimic_model num_clusters [simulate_options]"
    exit 1
fi

set -x

. /etc/profile.d/mimicnet.sh

BASE_DIR=`pwd`
VARIANT="${1}"
INGRESS_MODEL="${BASE_DIR}/${2}"
EGRESS_MODEL="${BASE_DIR}/${3}"
INTERMIMIC_MODEL="${BASE_DIR}/${4}"
NUM_CLUSTERS="${5}"

echo "Running MimicNet simulation..."
cd simulate/simulate_mimic_${VARIANT}
exec 5>&1
RESULTS_DIR=$(./run.sh RecordEval ${INGRESS_MODEL} ${EGRESS_MODEL} ${INTERMIMIC_MODEL} -c ${NUM_CLUSTERS} ${@:6} | tee /dev/fd/5 | tail -n 1)

echo "Parsing results..."
cd ${BASE_DIR}
prepare/parse_pdmps.sh simulate/simulate_mimic_${VARIANT}/${RESULTS_DIR} ${NUM_CLUSTERS}
