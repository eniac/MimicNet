#pragma once

#include <ATen/ATen.h>
#include <ATen/MatrixRef.h>
#include <ATen/cudnn/Descriptors.h>
#include <ATen/cudnn/Handles.h>

#include <H5Cpp.h>

#include "lstm_fwd.h"


using namespace std; // assumed in the following

class MimicNetLstmDctcp {
public:
    MimicNetLstmDctcp(const int input_size = 20, const int batch_size = 1,
                      const int num_layers = 2, const int window_size = 10,
                      const double& DIS_META_LAST_MIN = 0.0,
                      const double& DIS_META_LAST_STEP = 0.0,
                      const double& DIS_META_EWMA_MIN = 0.0,
                      const double& DIS_META_EWMA_STEP = 0.0,
                      const double& DIS_META_LATENCY_MIN = 0.0,
                      const double& DIS_META_LATENCY_STEP = 0.0)
            : input_size_(input_size), batch_size_(batch_size),
            num_layers_(num_layers), window_size_(window_size),
            DIS_META_LAST_MIN_(DIS_META_LAST_MIN),
            DIS_META_LAST_STEP_(DIS_META_LAST_STEP),
            DIS_META_EWMA_MIN_(DIS_META_EWMA_MIN),
            DIS_META_EWMA_STEP_(DIS_META_EWMA_STEP),
            DIS_META_LATENCY_MIN_(DIS_META_LATENCY_MIN),
            DIS_META_LATENCY_STEP_(DIS_META_LATENCY_STEP),
            hidden_size_(input_size * window_size),
            linear_(hidden_size_, 3) {
        for (int i = 0; i < num_layers_; ++i) {
            h_ts_.emplace_back(at::zeros({1, hidden_size_}, TENSOR_OPTS));
            c_ts_.emplace_back(at::zeros({1, hidden_size_}, TENSOR_OPTS));
        }

        cudaMalloc((MimicDType**)&gpu_input, input_size * sizeof(MimicDType));
        data_ = from_blob(gpu_input, {1, input_size}, TENSOR_OPTS);
        output_ = at::zeros({1, hidden_size_}, TENSOR_OPTS);
    }

    ~MimicNetLstmDctcp() {
        cudaFree(gpu_input);
    }

    void forward(MimicDType* drop_prediction, MimicDType* latency_prediction,
                 MimicDType* ECN_prediction, const at::Tensor& data) {
        auto* input = &data;
        for (int i = 0; i < num_layers_; ++i) {
            lstms_[i].forward(*input, &(h_ts_[i]), &(c_ts_[i]));
            input = &(h_ts_[i]);
        }
        auto& output_ = *input;

        // doing this on CPU is faster!
        auto h_t = output_.to(at::Device::Type::CPU);
        auto pred_ = linear_.forward(h_t);
        MimicDType* pred = pred_.toDoubleData();
        *drop_prediction = 1.0 / (1.0 + exp(-pred[0]));
        *latency_prediction = pred[1];
        *ECN_prediction = 1.0 / (1.0 + exp(-pred[2]));
    }

    void getValue(bool* drop, MimicDType* latency, bool* ECN, MimicDType* input) {
        cudaMemcpy(gpu_input, input, input_size_ * sizeof(MimicDType),
                   cudaMemcpyHostToDevice);
        // apparently this is implicit:
        // data_ = from_blob(gpu_input, {1, len}, TENSOR_OPTS);
        forward(&prev_drop_, &prev_latency_, &prev_ECN_, data_);

#ifdef DEBUG
        cout.precision(18);
        cout << fixed << prev_drop_ << " " << prev_latency_ << " "
                      << prev_ECN_ << endl;
#endif

        if (prev_drop_ >= 0.5) {
            *drop = true;
        } else {
            *drop = false;
        }
        *latency = prev_latency_;
        if (prev_ECN_ >= 0.5) {
            *ECN = true;
        } else {
            *ECN = false;
        }
    }

    static unique_ptr<MimicNetLstmDctcp> loadFromHdf5(const char* path) {
        H5::H5File file(path, H5F_ACC_RDONLY);
        H5::DataSet dataset;

        int input_size, window_size, num_layers;
        double DIS_META_LAST_MIN;
        double DIS_META_LAST_STEP;
        double DIS_META_EWMA_MIN;
        double DIS_META_EWMA_STEP;
        double DIS_META_LATENCY_MIN;
        double DIS_META_LATENCY_STEP;
        dataset = file.openDataSet("input_size");
        dataset.read(&input_size, H5::PredType::NATIVE_INT);
        dataset = file.openDataSet("window_size");
        dataset.read(&window_size, H5::PredType::NATIVE_INT);
        dataset = file.openDataSet("num_layers");
        dataset.read(&num_layers, H5::PredType::NATIVE_INT);
        dataset = file.openDataSet("dis_meta_last_min");
        dataset.read(&DIS_META_LAST_MIN, H5::PredType::NATIVE_DOUBLE);
        dataset = file.openDataSet("dis_meta_last_step");
        dataset.read(&DIS_META_LAST_STEP, H5::PredType::NATIVE_DOUBLE);
        dataset = file.openDataSet("dis_meta_ewma_min");
        dataset.read(&DIS_META_EWMA_MIN, H5::PredType::NATIVE_DOUBLE);
        dataset = file.openDataSet("dis_meta_ewma_step");
        dataset.read(&DIS_META_EWMA_STEP, H5::PredType::NATIVE_DOUBLE);
        dataset = file.openDataSet("dis_meta_latency_min");
        dataset.read(&DIS_META_LATENCY_MIN, H5::PredType::NATIVE_DOUBLE);
        dataset = file.openDataSet("dis_meta_latency_step");
        dataset.read(&DIS_META_LATENCY_STEP, H5::PredType::NATIVE_DOUBLE);
        int hidden_size = input_size * window_size;

        auto model = make_unique<MimicNetLstmDctcp>(
                    input_size, 1, num_layers, window_size,
                    DIS_META_LAST_MIN, DIS_META_EWMA_STEP,
                    DIS_META_EWMA_MIN, DIS_META_EWMA_STEP,
                    DIS_META_LATENCY_MIN, DIS_META_LATENCY_STEP);

        dataset = file.openDataSet("lstm.weight_ih_l0");
        auto weight_ih = (MimicDType*)malloc(dataset.getInMemDataSize());
        dataset.read(weight_ih, H5::PredType::NATIVE_DOUBLE);
        dataset = file.openDataSet("lstm.weight_hh_l0");
        auto weight_hh = (MimicDType*)malloc(dataset.getInMemDataSize());
        dataset.read(weight_hh, H5::PredType::NATIVE_DOUBLE);
        dataset = file.openDataSet("lstm.bias_ih_l0");
        auto bias_ih = (MimicDType*)malloc(dataset.getInMemDataSize());
        dataset.read(bias_ih, H5::PredType::NATIVE_DOUBLE);
        dataset = file.openDataSet("lstm.bias_hh_l0");
        auto bias_hh = (MimicDType*)malloc(dataset.getInMemDataSize());
        dataset.read(bias_hh, H5::PredType::NATIVE_DOUBLE);

        model->lstms_.emplace_back(input_size, hidden_size);
        model->lstms_[0].setParameters(weight_ih, weight_hh, bias_ih, bias_hh);

        free(weight_ih);
        free(weight_hh);
        free(bias_ih);
        free(bias_hh);

        for (int i = 1; i < num_layers; ++i) {
            dataset = file.openDataSet("lstm.weight_ih_l" + to_string(i));
            weight_ih = (MimicDType*)malloc(dataset.getInMemDataSize());
            dataset.read(weight_ih, H5::PredType::NATIVE_DOUBLE);
            dataset = file.openDataSet("lstm.weight_hh_l" + to_string(i));
            weight_hh = (MimicDType*)malloc(dataset.getInMemDataSize());
            dataset.read(weight_hh, H5::PredType::NATIVE_DOUBLE);
            dataset = file.openDataSet("lstm.bias_ih_l" + to_string(i));
            bias_ih = (MimicDType*)malloc(dataset.getInMemDataSize());
            dataset.read(bias_ih, H5::PredType::NATIVE_DOUBLE);
            dataset = file.openDataSet("lstm.bias_hh_l" + to_string(i));
            bias_hh = (MimicDType*)malloc(dataset.getInMemDataSize());
            dataset.read(bias_hh, H5::PredType::NATIVE_DOUBLE);

            model->lstms_.emplace_back(hidden_size, hidden_size);
            model->lstms_[i].setParameters(weight_ih, weight_hh, bias_ih, bias_hh);

            free(weight_ih);
            free(weight_hh);
            free(bias_ih);
            free(bias_hh);
        }

        dataset = file.openDataSet("linearD.weight");
        weight_ih = (MimicDType*)malloc(dataset.getInMemDataSize() * 3);
        dataset.read(weight_ih, H5::PredType::NATIVE_DOUBLE);
        dataset = file.openDataSet("linearD.bias");
        bias_ih = (MimicDType*)malloc(dataset.getInMemDataSize() * 3);
        dataset.read(bias_ih, H5::PredType::NATIVE_DOUBLE);

        dataset = file.openDataSet("linearL.weight");
        dataset.read((char*)weight_ih + dataset.getInMemDataSize(),
                     H5::PredType::NATIVE_DOUBLE);
        dataset = file.openDataSet("linearL.bias");
        dataset.read((char*)bias_ih + dataset.getInMemDataSize(),
                     H5::PredType::NATIVE_DOUBLE);
        
        dataset = file.openDataSet("linearE.weight");
        dataset.read((char*)weight_ih + dataset.getInMemDataSize()*2,
                     H5::PredType::NATIVE_DOUBLE);
        dataset = file.openDataSet("linearE.bias");
        dataset.read((char*)bias_ih + dataset.getInMemDataSize()*2,
                     H5::PredType::NATIVE_DOUBLE);

        model->linear_.setParameters(weight_ih, bias_ih);
        free(weight_ih);
        free(bias_ih);

        return move(model);
    }
public:
    const double DIS_META_LAST_MIN_;
    const double DIS_META_LAST_STEP_;
    const double DIS_META_EWMA_MIN_;
    const double DIS_META_EWMA_STEP_;
    const double DIS_META_LATENCY_MIN_;
    const double DIS_META_LATENCY_STEP_;

private:
    const int input_size_;
    const int batch_size_;
    const int num_layers_;
    const int window_size_;
    const int hidden_size_;

    vector<LSTMCell> lstms_;
    vector<at::Tensor> h_ts_;
    vector<at::Tensor> c_ts_;
    Linear linear_;

    MimicDType prev_drop_;
    MimicDType prev_latency_;
    MimicDType prev_ECN_;

    // To prevent allocation
    at::Tensor data_;
    at::Tensor output_;

    MimicDType* gpu_input;
};
