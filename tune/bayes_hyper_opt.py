#!/usr/bin/env python3

import argparse
from compare import *
from hyperopt import hp, fmin, pyll, tpe, STATUS_OK, Trials
import numpy as np
import glob
import json
import os
import random
import re
import shutil
import subprocess
import sys

def parse_target(variant, target, result_dir, seed, cl, degree):
    if target == "rtt":
        ret = subprocess.call("python evaluate/parse_rtt_" + variant + ".py " \
                              + result_dir + " " + str(cl) + " 1.0.",
                              shell = True)
    elif target == "thr":
        ret = subprocess.call("python evaluate/parse_thr_" + variant + ".py " \
                              + result_dir + " " + str(cl) + " 0.1",
                              shell = True)
    else:
        ret = subprocess.call("python evaluate/parse_fct_" + variant + ".py " \
                              + str(seed) + " " + result_dir + " " \
                              + "--numClusters " + str(cl) + " " \
                              + "--numToRs " + str(degree),
                              shell = True)

    return ret

def objective(params):
    variant = params["variant"]
    del params["variant"]

    train_script = params["train_script"]
    del params["train_script"]

    data_dir = params["data_dir"]
    del params["data_dir"]

    hp_results_dir = params["results_dir"]
    del params["results_dir"]

    degree = str(params["degree"])
    del params["degree"]

    seed = str(params["seed"])
    del params["seed"]

    original_args = params["original_args"]
    del params["original_args"]
    
    target = params["target"]
    del params["target"]

    metric = params["metric"]
    del params["metric"]
    
    cluster_array = params["test_cluster_counts"]
    del params["test_cluster_counts"]


    # assemble the training script arguments and the unique name of the trial,
    # for both ingress and egress
    arguments_in = ""
    arguments_out = ""
    for key, v in params.items():
        if isinstance(v, float):
            value = "{0:0.4f}".format(v)
        else:
            value = str(v)
        if key.startswith("in_"):
            arguments_in += " --" + key[3:] + " " + str(value) # remove in_
        else:
            arguments_out += " --" + key[4:] + " " + str(value) # remove out_
    trans_table = str.maketrans(dict.fromkeys('- '))
    unique_name_in = arguments_in.translate(trans_table)
    unique_name_out = arguments_out.translate(trans_table)
    hp_results_dir = os.path.abspath(hp_results_dir)
    unique_path_in = hp_results_dir + "/ingress_" + unique_name_in
    unique_path_out = hp_results_dir + "/egress_" + unique_name_out
    pkl_in = data_dir + "/in_data.pkl"
    pkl_out = data_dir + "/out_data.pkl"
    inter_mimic_model = os.path.abspath(data_dir + "/intermimic.dat")


    # Train ingress
    # TODO: Don't retrain if we've already trained something for this set of arguments...
    print("Starting ingress training of an ingress model with arguments:" \
          + arguments_in)
    ret = os.system(" ".join(["python", train_script, pkl_in, degree,
                              "--model_name", unique_path_in,
                              "--direction", "INGRESS", arguments_in]))
    if ret != 0:
        raise("Ingress training script failed!")
    os.system("rm " + unique_path_in + "_epoch*") # Remove intermediate models

    # Train egress
    print("Starting egress training of a(n) out" + \
          " network with arguments:" + arguments_out)
    ret = os.system(" ".join(["python", train_script, pkl_out, degree,
                              "--model_name", unique_path_out,
                              "--direction", "EGRESS", arguments_out]))
    if ret != 0:
        raise("Egress training script failed!")
    os.system("rm " + unique_path_out + "_epoch*") # Remove intermediate models


    # Simulate!
    values = []
    for cl in cluster_array:        
        print("Starting evaluation of " + str(cl) + " clusters...")
        subprocess.call("./clean.sh > /dev/null 2>&1",
                         cwd = "simulate/simulate_mimic_" + variant,
                         shell = True)
        ret = subprocess.call(" ".join(["./run.sh", "RecordEval", unique_path_in,
                                        unique_path_out, inter_mimic_model,
                                        original_args,
                                        # these overwrite originals:
                                        "-s", str(seed), "-c", str(cl),
                                        ">>", hp_results_dir + "/log.txt", "2>&1"]),
                              cwd = "simulate/simulate_mimic_" + variant,
                              shell = True)
        if ret != 0:
            raise("simulation failed!")

        # Move the data to the current directory under the name data + unique_name
        tmp_result_dirs = glob.glob("simulate/simulate_mimic_" + variant + "/results/*")
        assert(len(tmp_result_dirs) == 1)
        tmp_result_dir = tmp_result_dirs[0]
        result_dir = hp_results_dir + "/" \
                   + unique_name_in + "=" + unique_name_out
        os.system("rsync -a " + tmp_result_dir + "/ " + result_dir + \
                        "; rm -r " + tmp_result_dir);
        os.system("prepare/parse_pdmps.sh " + result_dir + " " + str(cl) + " > /dev/null 2>&1")

        # Compute the target and compare the metric
        parse_target(variant, target, result_dir, seed, cl, degree)
    
        baseline_file_name = data_dir + "/" + target + "_c"+ str(cl) + ".dat"
        eval_file_name = result_dir + "/" + target + "_c"+ str(cl) + ".dat"

        ret_value = 10000
        if metric == "ks" or metric == "w1":
            if metric == "ks":
                if target == "thr":
                    ret_value = compare_ks_no0s(eval_file_name, baseline_file_name)
                else:
                    ret_value = compare_ks(eval_file_name, baseline_file_name)
            elif metric == "w1":
                if target == "thr":
                    ret_value = compare_w1_no0s(eval_file_name, baseline_file_name)
                else:
                    ret_value = compare_w1(eval_file_name, baseline_file_name)
        elif metric.startswith("pct"):
            pct = int(metric[3:])
            ret_value = compare_pct(eval_file_name, baseline_file_name, pct)
        else:
            with open(baseline_file_name, "r") as fh:
                total_real_samples = 0
                for line in fh:
                    total_real_samples += 1

            mse, samples = compare_fct_mse(eval_file_name, baseline_file_name)
            if samples >= 0.5 * total_real_samples:
                ret_value = mse
        values.append(ret_value)

    # Clean up and archive
    # os.system("tar -czf " + unique_name + ".tar.gz " + result_dir)
    # shutil.rmtree(result_dir)

    with open(hp_results_dir + "/result.dat", 'a+') as outf:
        outf.write("ingress: " + arguments_in + "; egress: " + arguments_out + \
                   " | " + target + " " + metric + ": <" + \
                   ",".join([str(v) for v in values]) + \
                   "> = " + str(sum(values)) + " \n")

    return {'loss': sum(values), 'status': STATUS_OK,
            'model_string': " ".join([unique_path_in, unique_path_out,
                                      inter_mimic_model])}

if __name__ == "__main__":
    parser = argparse.ArgumentParser();
    parser.add_argument("variant", type = str, \
                        help="(tcp|dctcp|homa)")
    parser.add_argument("train_script", type = str, \
                        help="path to training script")
    parser.add_argument("data_dir", type = str, \
                        help="data dictionary pickle file directory")
    parser.add_argument("results_dir", type = str, \
                        help="File to which we will print results")
    parser.add_argument("config_file", type = str, \
                        help="JSON file that contains the config of the current job")
    parser.add_argument("--max_evals", type = int, \
                        help="Number of iterations to run")
    args = parser.parse_args()


    max_evals = 20
    if args.max_evals:
        max_evals = args.max_evals


    with open(args.data_dir + "/params.txt", "r") as arg_file:
        original_args = arg_file.readline().rstrip('\n')
        original_seed = int(arg_file.readline())
        degree = int(arg_file.readline())
    new_seed = original_seed
    while new_seed == original_seed:
        new_seed = random.randint(1, 10000)

    space = {}
    with open(args.config_file, "r") as cf:
        config = json.load(cf)
        # build space parameters
        for k, v in config["in_parameters"].items():
            key = "in_" + k

            if k == "latency_loss":
                space[key] = hp.choice(key, v)
            elif not isinstance(v, list):
                space[key] = int(v)
            else:
                start, end, quantum = v
                if quantum == -1:
                    space[key] = hp.uniform(key, start, end)
                elif isinstance(quantum, int):
                    space[key] = pyll.scope.int(hp.quniform(key, start, end, quantum))
                else:
                    space[key] = hp.quniform(key, start, end, quantum)
        for k, v in config["out_parameters"].items():
            key = "out_" + k

            if k == "latency_loss":
                space[key] = hp.choice(key, v)
            elif not isinstance(v, list):
                space[key] = int(v)
            else:
                start, end, quantum = v
                if quantum == -1:
                    space[key] = hp.uniform(key, start, end)
                elif isinstance(quantum, int):
                    space[key] = pyll.scope.int(hp.quniform(key, start, end, quantum))
                else:
                    space[key] = hp.quniform(key, start, end, quantum)

        # add metrics
        assert("target" not in space)
        space["target"] = config["target"]
        assert("metric" not in space)
        space["metric"] = config["metric"]
        assert("test_cluster_counts" not in space)
        space["test_cluster_counts"] = config["test_cluster_counts"]

    supported_metrics = ["fct_mse", "fct_ks", "fct_w1", "fct_pct[0-9]+",
                         "rtt_ks", "rtt_w1", "rtt_pct[0-9]+",
                         "thr_ks", "thr_w1", "thr_pct[0-9]+"]
    target_metric = space["target"] + "_" + space["metric"]
    temp = '(?:% s)' % '|'.join(supported_metrics)
    if not re.match(temp, target_metric):
        raise Exception("Metric not supported!")


    print("Generating ground-truth " + space["target"] + " if necessary...")
    data_unique_name = os.path.basename(os.path.normpath(args.data_dir))
    for cl in space["test_cluster_counts"]:
        datfile = args.data_dir + "/" + space["target"] + "_c"+ str(cl) + ".dat"
        if os.path.isfile(datfile):
            print("Using EXISTING eval data for " + str(cl) + " clusters")
            continue

        evalfolder = args.data_dir + "/eval" + str(cl)
        if not os.path.isdir(evalfolder):
            print("Generating NEW eval data for " + str(cl) + " clusters")
            subprocess.call(" ".join(["evaluate/run_get_eval.sh", args.variant,
                                      str(cl), args.data_dir,
                                      original_args]),
                            shell = True)
        else:
            print("Computing MISSING eval data for " + str(cl) + " clusters")

        # Compute the target and compare the metric
        ret = parse_target(args.variant, space["target"], args.data_dir,
                           original_seed, cl, degree)
        if ret != 0:
            raise RuntimeError("ERROR: non-zero return for eval parsing: " \
                               + str(ret))


    # add file in/out params too
    assert("variant" not in space)
    space["variant"] = args.variant
    assert("train_script" not in space)
    space["train_script"] = args.train_script
    assert("data_dir" not in space)
    space["data_dir"] = args.data_dir
    assert("results_dir" not in space)
    space["results_dir"] = args.results_dir
    assert("degree" not in space)
    space["degree"] = degree
    assert("seed" not in space)
    space["seed"] = new_seed
    assert("original_args" not in space)
    space["original_args"] = original_args

    print("Starting hyperparam tuning with OMNeT seed:", new_seed)
    trials = Trials()
    best = fmin(objective, space, algo=tpe.suggest, max_evals=max_evals,
                trials=trials)
    print("The best result is " + str(best) + " with models:")
    print(trials.results[np.argmin([r['loss'] for r in trials.results])]['model_string'])
