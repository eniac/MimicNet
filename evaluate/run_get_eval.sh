#!/bin/bash

set -e

if [[ $# -lt 3 ]]; then
	echo "Usage: run_get_eval.sh variant num_clusters existing_directory [options]"
	exit 1
fi


BASE_DIR=`pwd`
VARIANT=${1}
NUM_CLUSTERS=${2}
EXISTING=${3}
mkdir -p ${BASE_DIR}/data

echo "Starting simulation..."
cd simulate/simulate_${VARIANT}

exec 5>&1
RESULTS_DIR=$(./run.sh RecordEval ${@:4} -c ${NUM_CLUSTERS} | tee /dev/fd/5 | tail -n 1)
RESULTS_FILE=${RESULTS_DIR##*/}
cp -rlf ${RESULTS_DIR}/eval* ${BASE_DIR}/${EXISTING}
rm -r ${RESULTS_DIR}

cd ${BASE_DIR}
prepare/parse_pdmps.sh ${BASE_DIR}/${EXISTING} ${NUM_CLUSTERS}
find ${BASE_DIR}/${EXISTING} -path *.dump -delete

echo "Evaluation data generated!"