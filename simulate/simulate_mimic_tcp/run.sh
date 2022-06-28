#! /bin/bash

# 1. Base
# 2. RecordEval
# 3. RecordAll

set -e

. /etc/profile.d/mimicnet.sh

INET_INCLUDES="-I${INET_HOME}/src \
-I${INET_HOME}/src/base \
-I${INET_HOME}/src/linklayer/contract \
-I${INET_HOME}/src/linklayer/ethernet \
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

PYTHON_INCLUDE="`pkg-config --cflags --libs python3`"

NEDPATH="-n ${INET_HOME}/src/:../src/:../common/clusters/:out/:."

USAGE="Usage: ./run.sh (Base | RecordEval | RecordAll)
                <ingress_model> <egress_model> <intermimic_model>
                [-s <seed>] [-r <routing>] [-l <load>] [-L <link_speed>]
                [-q (DropTailQueue | REDQueue)] [-v (TCPNewReno | TCPWestwood)]
                [-a <servers_per_rack>] [-c <total_clusters>]
                [-b <degree> /* # of ToRs/Aggs/AggUplinks */]
                [-d (release | debug)] [-p (off | on) /* parallelism */]
                [-S <simulation_length>]
                [-m /* include_intra_mimic_traffic */]
                [-n /* include_inter_mimic_traffic */]"

cleanup() {
    rm -f out/lock
    rm -rf out/lock2
}

trap cleanup EXIT

# Parse Args

if [[ "$1" != "Base" && "$1" != "RecordEval" && "$1" != "RecordAll" ]]; then
    echo ${USAGE}
    exit 1
else
    VARIANT=$1
fi
shift

if [[ $# -lt 2 ]]; then
    echo ${USAGE}
    exit 1
fi
ING_MODEL=$1
shift
EGR_MODEL=$1
shift
INTER_MODEL=$1
shift

SEED=0
SIMU_LEN=20
ROUTING="ecmp"
QUEUE="DropTailQueue"
TCPVAR="TCPNewReno"
CLUSTERS=2
SERVERS=4
DEGREE=2
LOAD=0.70
INTRA_MIMIC_FLAG=""
INTER_MIMIC_FLAG=""
MODE="release"
PARALLEL_FLAG=""
MIMIC_TYPE="lstm"
LINK_SPEED=100e6

while getopts "s:r:q:v:l:c:a:b:d:p:L:S:mn" opt; do
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
    q ) # queue policy
      QUEUE="$OPTARG"
      ;;
    v ) # tcp variant
      TCPVAR="$OPTARG"
      ;;
    l ) # load
      LOAD="$OPTARG"
      ;;
    m ) # intraMimicTrafficFlag
      INTRA_MIMIC_FLAG="--includeIntraMimicTraffic"
      ;;
    n ) # interMimicTrafficFlag
      INTER_MIMIC_FLAG="--includeInterMimicTraffic"
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
    p ) # parallelism
      if [ "$OPTARG" = "on" ]; then
        PARALLEL_FLAG="--parallel"
      fi
      ;;
    L ) # Link speed
      LINK_SPEED="$OPTARG"
      ;;
    \? )
    echo ${USAGE}
    exit 1
    ;;
  esac
done
shift $((OPTIND -1))

echo -e "Simulation begin time: "
date +"%Y-%m-%d %T.%6N"

echo -e "\e[34mConfiguration: ${VARIANT}\e[0m"

UNIQUE_NAME="sw${DEGREE}_sv${SERVERS}_l${LOAD}_L${LINK_SPEED}_s${SEED}_q${QUEUE}_v${TCPVAR}_S${SIMU_LEN}"
APPROX_LIB_PATH=../src/out/gcc-${MODE}
APPROX_LIB=approx

mkdir -p out
rm -rf out/${UNIQUE_NAME}*
cp omnetpp.ini.template out/${UNIQUE_NAME}.ini


# Generate seeded traffic pattern based on args [.traffic]
let CORES=${DEGREE}\*${DEGREE}
python ../common/generate_traffic.py ${SEED} \
    out/${UNIQUE_NAME}.traffic --load ${LOAD} ${INTRA_MIMIC_FLAG} \
    ${INTER_MIMIC_FLAG} --numClusters ${CLUSTERS} --numCores ${CORES} \
    --numToRs ${DEGREE} --numServers ${SERVERS} --length ${SIMU_LEN} --linkSpeed ${LINK_SPEED}
sed -i "s/<TRAFFIC_CONFIG>/${UNIQUE_NAME}\.traffic/" out/${UNIQUE_NAME}.ini

# Generate flow information for omitted flows, and include in ini [.flow]
python ../common/determine_inter_mimic_intervals.py ${SEED} out/ \
    --load ${LOAD} ${INTRA_MIMIC_FLAG} ${INTER_MIMIC_FLAG} \
    --num_clusters ${CLUSTERS} --degree ${DEGREE} \
    --num_servers ${SERVERS} --linkSpeed ${LINK_SPEED}
for i in `seq 1 $( expr ${CLUSTERS} - 1)`;
do
    sed -i "/#INTERMIMIC_TRAFFIC#/a **.cluster[${i}].mimicDCN.egress_traffic_file = \"out/cl${i}_departing_flows.flow\"" out/${UNIQUE_NAME}.ini
    sed -i "/#INTERMIMIC_TRAFFIC#/a **.cluster[${i}].mimicDCN.ingress_traffic_file = \"out/cl${i}_arriving_flows.flow\"" out/${UNIQUE_NAME}.ini
done

# Generate parameter-dependent ini config [.cluster]
python ../common/generate_config.py ${SEED} out/${UNIQUE_NAME}.cluster \
    out/${UNIQUE_NAME}.route results/${UNIQUE_NAME}_mimic_tcp --numClusters ${CLUSTERS} \
    --numToRsAndUplinks ${DEGREE} --numServers ${SERVERS} \
    --mimic ${PARALLEL_FLAG}
sed -i "s/<CLUSTER_CONFIG>/${UNIQUE_NAME}\.cluster/" out/${UNIQUE_NAME}.ini

# Generate routing config [.route]
python ../common/generate_routes.py out/${UNIQUE_NAME}.route \
    --numClusters ${CLUSTERS} --serversPerRack ${SERVERS} \
    --numToRsAndUplinks ${DEGREE} --mimic ${PARALLEL_FLAG}
# the .cluster file will specify route files

# Configure the queue type and TCP variant
sed -i "s/<TCP_VARIANT>/${TCPVAR}/" out/${UNIQUE_NAME}.ini
sed -i "s/<QUEUE_TYPE>/${QUEUE}/" out/${UNIQUE_NAME}.ini
sed -i "s/<SIMU_LEN>/${SIMU_LEN}/" out/${UNIQUE_NAME}.ini

# Configure the model prefixes
sed -i "s@<ING_MODEL>@${ING_MODEL}@" out/${UNIQUE_NAME}.ini
sed -i "s@<EGR_MODEL>@${EGR_MODEL}@" out/${UNIQUE_NAME}.ini
sed -i "s@<INTER_MODEL>@${INTER_MODEL}@" out/${UNIQUE_NAME}.ini

# Generate results directory and config
mkdir -p results/${UNIQUE_NAME}_mimic_tcp
if [[ "${VARIANT}" == "RecordEval" ]]; then
    mkdir -p results/${UNIQUE_NAME}_mimic_tcp/eval${CLUSTERS}
fi
if [[ "${VARIANT}" == "RecordAll" ]]; then
    mkdir -p results/${UNIQUE_NAME}_mimic_tcp/eval${CLUSTERS}
    mkdir -p results/${UNIQUE_NAME}_mimic_tcp/debug${CLUSTERS}
fi


# Set parallelism
if [[ "${PARALLEL_FLAG}" == "--parallel" ]]; then
    PARALLEL_CONFIG='parallel-simulation=true\n'
    PARALLEL_CONFIG+='parsim-communications-class = "cMPICommunications"\n'
    PARALLEL_CONFIG+='parsim-synchronization-class = "cNullMessageProtocol"\n'
    sed -i "s/<PARALLEL_CONFIG>/${PARALLEL_CONFIG}/" out/${UNIQUE_NAME}.ini

    export HOST=`uname -n`
    EXE="mpirun --mca orte_base_help_aggregate 0 -mca btl ^openib -np $(( 1 + ${CLUSTERS} )) ./simulate_mimic_tcp"
else
    sed -i "s/<PARALLEL_CONFIG>//" out/${UNIQUE_NAME}.ini
    EXE="./simulate_mimic_tcp"
fi


# Use a file lock to ensure that multiple runs don't override one another
(

if flock 200; then
    if mkdir out/lock2 &> /dev/null; then
        #generate ECMP router
        python ../common/generate_my_router.py ${ROUTING}

        opp_makemake -f ${PYTHON_INCLUDE} ${PROJECT_INCLUDES} -DINET_IMPORT \
            ${INET_INCLUDES} -L${INET_HOME}/src/out/gcc-${MODE} \
            -linet -L../homatransport/out/gcc-${MODE} -lhomatransport \
            -L${APPROX_LIB_PATH} -l${APPROX_LIB}
        make LDFLAGS+='-Wl,--allow-shlib-undefined' MODE=${MODE}
    fi
fi

) 200> out/lock

echo -e "Simulation runtime begin time: "
date +"%Y-%m-%d %T.%6N"

# Run Simulation
echo -e "\e[34mRunning simulate_mimic_tcp\e[0m"
${EXE} out/${UNIQUE_NAME}.ini -u Cmdenv -c ${VARIANT} ${NEDPATH}

# FIXME: in fact it should be removed only after all scripts starts running the
# previous line, but this would be true in practice
rm -rf out/lock2

echo -e "Simulation end time: "
date +"%Y-%m-%d %T.%6N"
echo -e "\e[34mComplete! Results are in the following directory:\e[0m"
echo "results/${UNIQUE_NAME}_mimic_tcp"
