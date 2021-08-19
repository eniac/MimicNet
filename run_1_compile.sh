#! /bin/bash

set -e

if [[ -z $1 || ("$1" != "GPU" && "$1" != "CPU") ]]; then
    if [[ -f ".mimictype" ]]; then
        TYPE=`cat .mimictype`
        echo "GPU/CPU not specified, but inferring: ${TYPE}"
    else
        echo "Usage run_1_compile.sh GPU|CPU"
        exit 1
    fi
else
    TYPE=$1
fi

if [[ "${TYPE}" == "GPU" && -z "${CUDA_HOME}" ]]; then
    echo "CUDA_HOME path not set"
    exit 1
fi

BASE_DIR=`pwd`

. /etc/profile.d/mimicnet.sh
export LIBRARY_PATH=${LD_LIBRARY_PATH}


set -x

cd ${BASE_DIR}/simulate/src
if [ "${TYPE}" == "GPU" ]; then
    ./makemake.sh cuda
else
    ./makemake.sh python
fi

cd ${BASE_DIR}/simulate/homatransport
./makemake.sh

echo ${TYPE} > ${BASE_DIR}/.mimictype
echo "Compile complete!"
