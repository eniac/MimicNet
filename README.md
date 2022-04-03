MimicNet provides fast performance estimation for data center networks at scale, based on packet-level simulations and machine learning.
[Our SIGCOMM 2021 paper](https://dl.acm.org/doi/10.1145/3452296.3472926) describes the details of the system.

# Getting Started
### 0. Setup

Download script separately or run from outer directory
```bash
# running from outer directory
./MimicNet/run_0_setup.sh CPU|GPU
source /etc/profile.d/mimicnet.sh
```

If running GPU, make sure to set the CUDA_HOME path 
```bash
export CUDA_HOME=<<cuda_path>>
```


The remaining scripts should be run inside the MimicNet directory
### 1. Compile 

Build simulation libraries 
```bash
# CPU or GPU correlates to the option used in setup
./run_1_compile.sh CPU|GPU
```

### 2. Generate

Run the simulation for the specified protocol and prepare the results
```bash
# variant is the protocol being simulated 
# Currently supported variants are tcp, dctcp, and homa 
./run_2_generate.sh <<VARIANT>>
```
### 3. Train 

Train a pair of internal models for approximating intra-cluster traffic and a feeder model for approximating inter-cluster traffic

```bash
# variant is the protocol being simulated
# train_script is the script used to train the Mimic models
# data_path is the location of the prepared results from 2_generate
./run_3_train.sh <<VARIANT>> <<TRAIN_SCRIPT>> <<DATA_PATH>>
``` 

Optionally run hyper-parameter tuning to find optimal hyper-parameters

```bash
# variant is the protocol being simulated
# train_script is the script used to train the Mimic models
# data_path is the location of the prepared results from 2_generate
# search_space_file is tune/hp_configs/lstm.json
./run_3_hypertrain.sh <<VARIANT>> <<TRAIN_SCRIPT>> <<DATA_PATH>> <<SEARCH_SPACE_FILE>>
```

### 4. Compose

Compose a large-scale MimicNet simulation using the trained models

```bash
# variant is the protocol being simulated
# ingress_model is the path to the ingress model trained in 3_train or 3_hypertrain
# egress_model is the path to the egress model
# feeder_model is the path to the feeder model
# num_clusters is the scale of the simulation 
./run_4_mimicnet.sh <<VARIANT>> <<INGRESS_MODEL>> <<EGRESS_MODEL>> <<FEEDER_MODEL>> <<NUM_CLUSTERS>>
```

### Run full process

Run the following command for 1. compile, 2. generate, 3. train, and 4. compose 

```bash
# variant is the protocol being simulated
# num_clusters is the scale of the MimicNet simulation
./run_all.sh <<VARIANT>> <<NUM_CLUSTERS>>
```

# Making Changes

### Models

run_3_train.sh and run_3_hypertrain.sh need a training script to be provided. In order to use a custom model, the custom training script should be provided here instead.

### Protocols

Following files/directories need to be changed/created
- prepare/Packet.py
- prepare/extract_features_[protocol].py
- train/lstm/train_lstm_[protocol].py
- simulate/simulate_[protocol]
- simulate/simulate_mimic_[protocol]

Where Packet.py should store the relevant flags used to determine whether packets match in the protocol (see Packet.py or HomaPkt.py for examples).
  
In extract_features_[protocol].py, the `extract_mimic_features` method needs to be modified depending on important features  

For the training script, all of the methods need to be changed to represent the feature vector for the specific protocol. 

The simulate_[protocol] directory contains the script to run the simulation of the protocol, and likewise the simulate_mimic_[protocol] directory contains the script used to run the simulation of the protocol with MimicNet.
