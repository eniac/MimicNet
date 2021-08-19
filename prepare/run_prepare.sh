#! /bin/bash
set -e

if [ "$#" -ne 3 ]; then
	echo "Usage: run_prepare.sh [directory] [seed] [number of ToRs/Aggs per subtree]"
	exit 1
fi

dir=${1%/}

echo "Starting pdmp parsing..."
prepare/parse_pdmps.sh $dir 2
find . -path ${1}\*.dump -delete

echo "Starting feature extraction..."
if [[ ${dir: -5} == "_homa" ]]; then    
    python3 prepare/extract_features_homa.py $dir 1.1. $2 $3
elif [[ ${dir: -6} == "_dctcp" ]]; then
    python3 prepare/extract_features_dctcp.py $dir 1.1. $2 $3
elif [[ ${dir: -4} == "_tcp" ]]; then
    python3 prepare/extract_features_tcp.py $dir 1.1. $2 $3
else
    echo "ERROR: Unable to infer variant from directory name: $dir"
    exit 1
fi

# remove the last 1000 elements because the tail always looks like drops
# TODO: make this configurable
head -n -1000 $dir/in_features.dat > tmp.dat && mv tmp.dat $dir/in_features.dat
head -n -1000 $dir/in_target_time.dat > tmp.dat && mv tmp.dat $dir/in_target_time.dat
head -n -1000 $dir/in_target_drop.dat > tmp.dat && mv tmp.dat $dir/in_target_drop.dat
head -n -1000 $dir/out_features.dat > tmp.dat && mv tmp.dat $dir/out_features.dat
head -n -1000 $dir/out_target_time.dat > tmp.dat && mv tmp.dat $dir/out_target_time.dat
head -n -1000 $dir/out_target_drop.dat > tmp.dat && mv tmp.dat $dir/out_target_drop.dat

echo "Starting pkl-ization..."
python3 prepare/bin_data_by_time.py $dir/in_target_time.dat
python3 prepare/bin_data_by_time.py $dir/out_target_time.dat
python3 prepare/load_data.py $dir/in_features.dat \
        $dir/in_target_time.dat_binned $dir/in_target_drop.dat $dir/in_data.pkl
python3 prepare/load_data.py $dir/out_features.dat \
        $dir/out_target_time.dat_binned $dir/out_target_drop.dat $dir/out_data.pkl

