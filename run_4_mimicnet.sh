#!/bin/bash

set -e

if [ $# -lt 3 ]; then
    echo "Usage ./run_4_mimicnet.sh variant ingress_model egress_model
                          [simulate_options]"
    exit 1
fi

. /etc/profile.d/mimicnet.sh

set -x

BASE_DIR=`pwd`
VARIANT="${1}"
INGRESS_MODEL="${2}"
EGRESS_MODEL="${3}"

echo "Running MimicNet simulation..."
cd simulate/simulate_mimic_${VARIANT}
exec 5>&1
RESULTS_DIR=$(./run.sh RecordEval ${INGRESS_MODEL} ${EGRESS_MODEL} ${@:4} | tee /dev/fd/5 | tail -n 1)

echo "Parsing results..."
if [[ ${RESULTS_DIR} =~ /sw([0-9]+)_ ]]; then
	NUM_SWITCHES=${BASH_REMATCH[1]}
else
	echo "ERROR: unable to extract switch count from ${RESULTS_DIR}"
	exit 1
fi

cd ${BASE_DIR}
prepare/parse_pdmps.sh ${RESULTS_DIR} ${NUM_SWITCHES}
