INET_INCLUDES="-I${INET_HOME}/src \
-I${INET_HOME}/src/base \
-I${INET_HOME}/src/linklayer/contract \
-I${INET_HOME}/src/linklayer/ethernet \
-I${INET_HOME}/src/networklayer/arp \
-I${INET_HOME}/src/networklayer/common \
-I${INET_HOME}/src/networklayer/contract \
-I${INET_HOME}/src/networklayer/ipv4 \
-I${INET_HOME}/src/transport/contract \
-I${INET_HOME}/src/transport/udp \
-I${INET_HOME}/src/transport/tcp \
-I${INET_HOME}/src/transport/tcp_common \
-I${INET_HOME}/src/status \
-I${INET_HOME}/src/util \
-I../homatransport/src/ \
"

CPPLSTM_INCLUDE="-I${OPT_HOME}/include \
-I${OPT_HOME}/include/TH \
-I${OPT_HOME}/include/THNN \
-I${OPT_HOME}/include/THCUNN \
-I${CUDA_HOME}/include \
-I${OPT_HOME}/anaconda3/include \
-lhdf5 \
-lhdf5_cpp \
"

PYTHON_INCLUDE="`pkg-config --cflags --libs python3`"

if [ -z "$1" ]; then
    echo "Usage: ./makemake.sh python|cuda"
    exit 1
elif [ "$1" == "python" ]; then
    LSTM_ENGINE=ENABLE_PYTHON_LSTM
    opp_makemake -f --deep --make-so -X test -o approx -O out -pAPPROX ${INET_INCLUDES} ${PYTHON_INCLUDE}
elif [ "$1" == "cuda" ]; then
    LSTM_ENGINE=ENABLE_CUDA_LSTM
    ATEN_CUDA_LIB="-L${OPT_HOME}/lib -lATen_cuda"
    CUDA_LIB="-L${CUDA_HOME}/lib64 -lcudart"
    opp_makemake -f --deep --make-so -X test -o approx -O out -pAPPROX ${INET_INCLUDES} ${PYTHON_INCLUDE} ${CPPLSTM_INCLUDE} ${ATEN_CUDA_LIB} ${CUDA_LIB}
else
    echo "Error: Invalid LSTM engine"
    exit 1
fi

if [ -z "$2" ]; then
    MODE=release
else
    MODE="$2"
fi

make CFLAGS+="-g -std=c++14 -fPIC -D${LSTM_ENGINE} -Wno-deprecated-declarations" LDFLAGS+="-Wl,--allow-shlib-undefined" MODE=${MODE}
