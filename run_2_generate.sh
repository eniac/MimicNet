#!/bin/bash

set -e

if [[ -z ${1} ]]; then
    echo "Usage: run_2_generate.sh variant [simulate_options]"
    exit 1
fi

. /etc/profile.d/mimicnet.sh

set -x

BASE_DIR=`pwd`
VARIANT=${1}
mkdir -p ${BASE_DIR}/data

echo "Starting simulation..."
cd simulate/simulate_${VARIANT}

exec 5>&1
RESULTS_DIR=$(./run.sh RecordAll ${@:2} | tee /dev/fd/5 | tail -n 1)
RESULTS_FILE=${RESULTS_DIR##*/}
rsync -a ${RESULTS_DIR}/ ${BASE_DIR}/data/${RESULTS_FILE}
rm -r ${RESULTS_DIR}

if [[ ${RESULTS_DIR} =~ /sw([0-9]+)_ ]]; then
    NUM_SWITCHES=${BASH_REMATCH[1]}
else
    echo "ERROR: unable to extract switch count from ${RESULTS_DIR}"
    exit 1
fi
if [[ ${RESULTS_DIR} =~ _s([0-9]+)_ ]]; then
    SEED=${BASH_REMATCH[1]}
else
    echo "ERROR: unable to extract seed from ${RESULTS_DIR}"
    exit 1
fi

cd ${BASE_DIR}
prepare/run_prepare.sh data/${RESULTS_FILE} ${SEED} ${NUM_SWITCHES}

echo "Generate complete! Results are in the following directory:"
echo "data/${RESULTS_FILE}"
