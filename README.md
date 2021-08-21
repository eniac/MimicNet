Full Process:
# Getting Started
### 0. Setup

Download script separately or run from outer directory
```bash
# running from outer directory
./MimicNet/run_0_setup CPU|GPU
source /etc/profile.d/mimicnet.sh
```

If running GPU, make sure to set the CUDA_HOME path 
```bash
export CUDA_HOME=<<cuda_path>>
```


the remaining scripts should be run inside the MimicNet directory
### 1. Compile 

script used to build the libraries 
```bash
# CPU or GPU correlates to the option used in setup
./run_1_compile CPU|GPU
```

### 2. Generate

runs the simulation for the specified protocol and prepares the results
```bash
# variant is the protocol being simulated 
./run_2_generate <<VARIANT>>
```
### 3. Hypertrain 

trains Mimic models and finds optimal hyperparameters

```bash
#  variant is the protocol being simulated
#  train_script is the script used to train the Mimic models
#  data_path is the location of the prepared results from 2_generate
#  search_space_file is tune/hp_configs/lstm.json
./run_3_hypertrain <<VARIANT>> <<TRAIN_SCRIPT>> <<DATA_PATH>> <<SEARCH_SPACE_FILE>>
``` 

### Run full process

To start, run the following command in order to train a Mimic model for a specific variant.
```bash
# Currently supported variants are tcp, dctcp and homa
./run_all <<VARIANT>>
```

# Making Changes

Models: 
	./run_3_hypertrain needs a training script to be provided. In order to use a custom model, the custom training script should be provided here instead.

Protocols:
Following files/directories need to be changed/created
- simulate/simulate_[protocol]
- simulate/simulate_mimic_[protocol]
- prepare/extract_features_[protocol].py
- prepare/Packet.py
- train/lstm/train_lstm_[protocol].py

Where simulate_[protocol] is a directory that contains the script to run the simulation of the protocol, and likewise simulate_mimic_[protocol] is the directory that contains the script used to run the simulation of the protocol with MimicNet.
  
In extract_features_[protocol].py, the `extract_mimic_features` method needs to be modified depending on important features
  
Packet.py should store the relevant flags used to determine whether packets match in the protocol (see Packet.py or HomaPkt.py for examples).

For the training script, all of the methods need to be changed to represent the feature vector for the specific protocol. 

