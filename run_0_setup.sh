#!/bin/bash

set -e

if [ -z "$DISPLAY" ]; then
    echo "DISPLAY not set.  Please ssh with -Y"
    exit 1
fi

if [[ -z $1  || ("$1" != "GPU" && "$1" != "CPU") ]]; then
    echo "Must run with GPU or CPU as first argument"
    exit 1
fi

if [[ "$1" == "GPU" && -z "${CUDA_HOME}" ]]; then
    echo "CUDA_HOME path not set"
    exit 1
fi

BASE_DIR=`pwd`
echo "Starting MimicNet setup in ${BASE_DIR}..."

touch ~/.Xauthority

echo "Setting environment variables..."
sudo rm -f /etc/profile.d/mimicnet.sh
echo "export TCL_LIBRARY=/usr/share/tcltk/tcl8.6" | sudo tee -a /etc/profile.d/mimicnet.sh

echo "" | sudo tee -a /etc/profile.d/mimicnet.sh
echo "export MIMICNET_HOME=${BASE_DIR}/MimicNet" | sudo tee -a /etc/profile.d/mimicnet.sh
echo "export INET_HOME=${BASE_DIR}/parallel-inet" | sudo tee -a /etc/profile.d/mimicnet.sh
echo "export OPT_HOME=${BASE_DIR}/opt" | sudo tee -a /etc/profile.d/mimicnet.sh
echo "export PATH=\$PATH:${BASE_DIR}/parallel-inet-omnet/bin" | sudo tee -a /etc/profile.d/mimicnet.sh
echo "export LD_LIBRARY_PATH=\$LD_LIBRARY_PATH:${BASE_DIR}/parallel-inet-omnet/lib" | sudo tee -a /etc/profile.d/mimicnet.sh

echo "" | sudo tee -a /etc/profile.d/mimicnet.sh
# Anaconda goes first!
echo "export PATH=${BASE_DIR}/opt/anaconda3/bin:\$PATH" | sudo tee -a /etc/profile.d/mimicnet.sh
echo "export CMAKE_PREFIX_PATH=\$CMAKE_PREFIX_PATH:${BASE_DIR}/opt/anaconda3" | sudo tee -a /etc/profile.d/mimicnet.sh
echo "export PKG_CONFIG_PATH=\$PKG_CONFIG_PATH:${BASE_DIR}/opt/anaconda3/lib/pkgconfig" | sudo tee -a /etc/profile.d/mimicnet.sh
echo "export LD_LIBRARY_PATH=\$LD_LIBRARY_PATH:${BASE_DIR}/opt/anaconda3/lib" | sudo tee -a /etc/profile.d/mimicnet.sh

echo "" | sudo tee -a /etc/profile.d/mimicnet.sh
echo "export CMAKE_INCLUDE_PATH=\$CMAKE_INCLUDE_PATH:${BASE_DIR}/opt/include" | sudo tee -a /etc/profile.d/mimicnet.sh

if [ "$1" == "GPU" ]; then
    echo "" | sudo tee -a /etc/profile.d/mimicnet.sh
    echo "export PATH=\$PATH:${CUDA_HOME}/bin" | sudo tee -a /etc/profile.d/mimicnet.sh
    echo "export LD_LIBRARY_PATH=\$LD_LIBRARY_PATH:${CUDA_HOME}/lib64" | sudo tee -a /etc/profile.d/mimicnet.sh
fi

echo "" | sudo tee -a /etc/profile.d/mimicnet.sh
echo "export LD_LIBRARY_PATH=\$LD_LIBRARY_PATH:${BASE_DIR}/opt/lib" | sudo tee -a /etc/profile.d/mimicnet.sh
source /etc/profile.d/mimicnet.sh


echo "Installing prereqs..."
sudo apt-get update
sudo apt-get install -y build-essential gcc g++ bison flex perl \
    qt5-default libqt5opengl5-dev tcl-dev tk-dev libxml2-dev \
    zlib1g-dev default-jre doxygen graphviz libwebkitgtk-1.0
sudo apt-get install -y openmpi-bin libopenmpi-dev
sudo apt-get install -y libpcap-dev

if [[ ! -d "MimicNet" ]]; then
    echo "Getting MimicNet code..."
    GIT_SSH_COMMAND="ssh -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no" git clone https://github.com/eniac/MimicNet.git
fi

echo "Installing OMNET++..."
cp -r ${MIMICNET_HOME}/third_party/parallel-inet-omnet .
cd parallel-inet-omnet
mkdir -p bin
./configure
make MODE=release -j
cd ..


echo "Installing INET..."
cp -r ${MIMICNET_HOME}/third_party/parallel-inet .
cd parallel-inet
./compile.sh
cd ..


mkdir -p src
mkdir -p opt
mkdir -p tmp


echo "Installing anaconda..."
cd src/
rm -f Anaconda3-*
rm -rf ${BASE_DIR}/opt/anaconda3
wget https://repo.anaconda.com/archive/Anaconda3-5.3.1-Linux-x86_64.sh
chmod ugo+x Anaconda3-5.3.1-Linux-x86_64.sh
./Anaconda3-5.3.1-Linux-x86_64.sh -b -p ${BASE_DIR}/opt/anaconda3
conda update -y -n base -c defaults conda


echo "Installing pytorch prereqs..."
sudo apt-get install -y cmake libgflags-dev
conda install -y numpy # putting everything on one line causes a downgrade of python to 2.7 for some reason...
conda install -y pyyaml mkl mkl-include setuptools cmake cffi typing h5py
conda install -y -c mingfeima mkldnn
conda install -y -c pytorch magma-cuda92
conda install -y pyyaml==5.4.1 # switch yaml to 5.4.1


git clone https://github.com/google/glog.git || true
cd glog
git checkout v0.4.0
./autogen.sh
./configure
make
sudo make install
cd ..

echo "Installing pybind11..."
git clone --recursive https://github.com/pytorch/pytorch || true
cd pytorch
git checkout v0.4.1
git rm --cached third_party/nervanagpu || true
git rm --cached third_party/eigen || true
git submodule update --init --recursive
cd third_party/pybind11
python setup.py install
cp -r include ${BASE_DIR}/opt/
cd ../..


echo "Installing pytorch/ATEN..."
TMPDIR=${BASE_DIR}/tmp python setup.py install
cd aten/
mkdir -p build
cd build
if [ "$1" == "GPU" ]; then
    cmake .. -DCMAKE_INSTALL_PREFIX=${BASE_DIR}/opt -DUSE_TENSORRT=OFF -DUSE_NVRTC=ON -DCUDA_TOOLKIT_ROOT_DIR=${CUDA_HOME}
else
    cmake .. -DCMAKE_INSTALL_PREFIX=${BASE_DIR}/opt -DUSE_TENSORRT=OFF -DUSE_NVRTC=ON
fi
make -j
make install

pip install msgpack hyperopt
