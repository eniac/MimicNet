#! /bin/bash

# 1. Base
# 2. RecordTraining
# 3. RecordEval
# 4. RecordAll

set -e

. /etc/profile.d/mimicnet.sh

INET_INCLUDES="-I${INET_HOME}/src \
-I${INET_HOME}/src/base \
-I${INET_HOME}/src/linklayer \
-I${INET_HOME}/src/linklayer/contract \
-I${INET_HOME}/src/linklayer/ethernet \
-I${INET_HOME}/src/linklayer/queue \
-I${INET_HOME}/src/networklayer/common \
-I${INET_HOME}/src/networklayer/contract \
-I${INET_HOME}/src/networklayer/ipv4 \
-I${INET_HOME}/src/transport/contract \
-I${INET_HOME}/src/transport/tcp \
-I${INET_HOME}/src/transport/tcp_common \
-I${INET_HOME}/src/status \
"

PROJECT_INCLUDES="-I../common \
-I../src \
-I../src/ipv4flow \
-I../src/ipv4flow/ecmp \
"

NEDPATH="-n ${INET_HOME}/src/:../src/:../common/clusters/:out/:."

USAGE="Usage: ./run.sh Base|RecordTraining|RecordEval|RecordAll [-s seed] [-r routing] [-l load] [-a servers_per_rack] [-b degree (# of ToRs/Aggs/AggUplinks)] [-c total_clusters] [-d release|debug] [-v tcp_variant (TCPNewReno|TCPWestwood|DCTCP)] [-k marking_threshold] [-S simulation_length] [-L link_speed]"

cleanup() {
    rm -f out/lock
    rm -rf out/lock2
}

trap cleanup EXIT

# Parse Args

if [[ "$1" != "Base" && "$1" != "RecordTraining" && "$1" != "RecordEval" && "$1" != "RecordAll" ]]; then
    echo $USAGE
    exit 1
else
    VARIANT=$1
fi

shift

SEED=0
SIMU_LEN=20
ROUTING="ecmp"
TCPVAR="DCTCP"
CLUSTERS=2
SERVERS=4
DEGREE=2
LOAD=0.70
MODE="release"
MARK_THRES=100
LINK_SPEED=100e6

ORIG_ARGS=${@}
while getopts "s:S:r:l:a:b:c:d:k:L:" opt; do
  case ${opt} in
    s ) # seed
      SEED="$OPTARG"
      ;;
    S ) # simulation length
      SIMU_LEN="$OPTARG"
      ;;
    r ) # routing
      ROUTING="$OPTARG"
      ;;
    l ) # load
      LOAD="$OPTARG"
      ;;
    a ) #servers per rack
      SERVERS="$OPTARG"
      ;;
    b ) #ToR/Agg switches per cluster
      DEGREE="$OPTARG"
      ;;
    c ) # clusters
      if [ "$OPTARG" -lt "2" ]; then
        echo "ERROR: total_clusters too small"
        exit 1
      fi
      CLUSTERS="$OPTARG"
      ;;
    d ) # mode
      MODE="$OPTARG"
      ;;
    k ) # marking threshold
      MARK_THRES="$OPTARG"
      ;;
    L ) # Link speed
      LINK_SPEED="$OPTARG"
      ;;
    \? )
      echo $USAGE
      exit 1
      ;;
  esac
done
shift $((OPTIND -1))

echo -e "Simulation begin time: "
date +"%Y-%m-%d %T.%6N"

echo -e "\e[34mConfiguration: ${VARIANT}\e[0m"

UNIQUE_NAME="sw${DEGREE}_sv${SERVERS}_l${LOAD}_L${LINK_SPEED}_s${SEED}_qThresholdMarkerQueue_K${MARK_THRES}_vDCTCP_S${SIMU_LEN}"

mkdir -p out
rm -rf out/${UNIQUE_NAME}*
cp omnetpp.ini.template out/${UNIQUE_NAME}.ini

# Generate seeded traffic pattern based on args [.traffic]
let CORES=${DEGREE}\*${DEGREE}
python ../common/generate_traffic.py ${SEED} \
    out/${UNIQUE_NAME}.traffic --load ${LOAD} --includeIntraMimicTraffic \
    --includeInterMimicTraffic --numClusters ${CLUSTERS} --numCores ${CORES} \
    --numToRs ${DEGREE} --numServers ${SERVERS} --length ${SIMU_LEN} \
    --linkSpeed ${LINK_SPEED}
sed -i "s/<TRAFFIC_CONFIG>/${UNIQUE_NAME}\.traffic/" out/${UNIQUE_NAME}.ini


# Generate parameter-dependent ini config [.cluster]
python ../common/generate_config.py ${SEED} out/${UNIQUE_NAME}.cluster \
    out/${UNIQUE_NAME}.route results/${UNIQUE_NAME}_dctcp --numClusters ${CLUSTERS} \
    --numToRsAndUplinks ${DEGREE} --numServers ${SERVERS}
sed -i "s/<CLUSTER_CONFIG>/${UNIQUE_NAME}\.cluster/" out/${UNIQUE_NAME}.ini


# Generate routing config [.route]
python ../common/generate_routes.py out/${UNIQUE_NAME}.route \
    --numClusters ${CLUSTERS} --serversPerRack ${SERVERS} \
    --numToRsAndUplinks ${DEGREE}
# the .cluster file will specify route files

# Configure the queue type and TCP variant
sed -i "s/<TCP_VARIANT>/${TCPVAR}/" out/${UNIQUE_NAME}.ini
sed -i "s/<SIMU_LEN>/${SIMU_LEN}/" out/${UNIQUE_NAME}.ini
sed -i "s/<MARK_THRES>/${MARK_THRES}/" out/${UNIQUE_NAME}.ini


# Generate results directory and config
mkdir -p results/${UNIQUE_NAME}_dctcp
if [[ "${VARIANT}" == "RecordTraining" || "${VARIANT}" == "RecordAll" ]]; then
    mkdir -p results/${UNIQUE_NAME}_dctcp/hosts${CLUSTERS}
    mkdir -p results/${UNIQUE_NAME}_dctcp/edges${CLUSTERS}
fi
if [[ "${VARIANT}" == "RecordEval" || "${VARIANT}" == "RecordAll" ]]; then
    mkdir -p results/${UNIQUE_NAME}_dctcp/eval${CLUSTERS}
fi


# Use a file lock to ensure that multiple runs don't override one another
(

if flock 200; then
    if mkdir out/lock2 &> /dev/null; then
        #generate ECMP router
        python ../common/generate_my_router.py ${ROUTING}

        opp_makemake -f ${PROJECT_INCLUDES} -DINET_IMPORT ${INET_INCLUDES} \
            -L${INET_HOME}/src/out/gcc-${MODE} -linet \
            -L../homatransport/out/gcc-${MODE} -lhomatransport \
            -L../src/out/gcc-${MODE} -lapprox
        make MODE=${MODE}
    fi
fi

) 200> out/lock

echo -e "Simulation runtime begin time: "
date +"%Y-%m-%d %T.%6N"

# Run Simulation
echo -e "\e[34mRunning simulate_dctcp\e[0m"
./simulate_dctcp out/${UNIQUE_NAME}.ini -u Cmdenv -c ${VARIANT} ${NEDPATH}
echo -e "${ORIG_ARGS}" > results/${UNIQUE_NAME}_dctcp/params.txt
echo -e "${SEED}" >> results/${UNIQUE_NAME}_dctcp/params.txt
echo -e "${DEGREE}" >> results/${UNIQUE_NAME}_dctcp/params.txt

# FIXME: in fact it should be removed only after all scripts starts running the
# previous line, but this would be true in practice
rm -rf out/lock2

echo -e "Simulation end time: "
date +"%Y-%m-%d %T.%6N"
echo -e "\e[34mComplete! Results are in the following directory:\e[0m"
echo "results/${UNIQUE_NAME}_dctcp"
