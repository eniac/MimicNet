#pragma once

#include <ATen/ATen.h>
#include <ATen/MatrixRef.h>
#include <ATen/cudnn/Descriptors.h>
#include <ATen/cudnn/Handles.h>

#include <THCUNN/THCUNN.h>

#define GetTH(x) (THTensor*)(x).unsafeGetTH(false)

at::TensorOptions TENSOR_OPTS = CUDA(at::kDouble);
at::TensorOptions CPU_OPTS = CPU(at::kDouble);
typedef double MimicDType;

using namespace std; // assumed in the following


// CPU only
class Linear {
public:
    // bias = True
    Linear(const int in_features, const int out_features)
            : in_features_(in_features), out_features_(out_features) {
        weight_ = at::zeros({in_features, out_features}, CPU_OPTS);
        bias_ = at::zeros({out_features}, CPU_OPTS);
    }

    inline at::Tensor forward(const at::Tensor& input) {
        return at::addmm(bias_, input, weight_, 1.0, 1.0);
    }

    void setParameters(MimicDType* weight, MimicDType* bias) {
        weight_ = at::from_blob(weight, {out_features_, in_features_}, CPU_OPTS).t().clone();
        bias_ = at::from_blob(bias, {out_features_}, CPU_OPTS).clone();
    }

private:
    const int in_features_;
    const int out_features_;

    at::Tensor weight_;
    at::Tensor bias_;
};


class LSTMCell {
public:
    LSTMCell(const int input_size, const int hidden_size)
            : input_size_(input_size), hidden_size_(hidden_size),
              gate_size_(4 * hidden_size) {
        weight_ih_ = at::zeros({input_size_, gate_size_}, TENSOR_OPTS);
        weight_hh_ = at::zeros({hidden_size_, gate_size_}, TENSOR_OPTS);
        bias_ih_ = at::zeros({gate_size_}, TENSOR_OPTS);
        bias_hh_ = at::zeros({gate_size_}, TENSOR_OPTS);

        if (bias_ih_.dim() == 1) {
            bias_ih_ = bias_ih_.unsqueeze(0);
        }
        if (bias_hh_.dim() == 1) {
            bias_hh_ = bias_hh_.unsqueeze(0);
        }

        igates_ = at::zeros({1, gate_size_}, TENSOR_OPTS);
        hgates_ = at::zeros({1, gate_size_}, TENSOR_OPTS);
    }

    void setParameters(MimicDType* weight_ih, MimicDType* weight_hh,
                       MimicDType* bias_ih, MimicDType* bias_hh) {
        const size_t max_size = max(gate_size_ * hidden_size_,
                                    gate_size_ * input_size_);

        MimicDType* gpu_mem;
        cudaMalloc(&gpu_mem, max_size * sizeof(MimicDType));

        cudaMemcpy(gpu_mem, weight_ih, gate_size_ * input_size_ * sizeof(MimicDType), cudaMemcpyHostToDevice);
        weight_ih_ = at::from_blob(gpu_mem, {gate_size_, input_size_}, TENSOR_OPTS).t().clone();

        cudaMemcpy(gpu_mem, weight_hh, gate_size_ * hidden_size_ * sizeof(MimicDType), cudaMemcpyHostToDevice);
        weight_hh_ = at::from_blob(gpu_mem, {gate_size_, hidden_size_}, TENSOR_OPTS).t().clone();

        cudaMemcpy(gpu_mem, bias_ih, gate_size_ * sizeof(MimicDType), cudaMemcpyHostToDevice);
        bias_ih_ = at::from_blob(gpu_mem, {gate_size_}, TENSOR_OPTS).clone();

        cudaMemcpy(gpu_mem, bias_hh, gate_size_ * sizeof(MimicDType), cudaMemcpyHostToDevice);
        bias_hh_ = at::from_blob(gpu_mem, {gate_size_}, TENSOR_OPTS).clone();

        cudaFree(gpu_mem);

        if (bias_ih_.dim() == 1) {
            bias_ih_ = bias_ih_.unsqueeze(0);
        }
        if (bias_hh_.dim() == 1) {
            bias_hh_ = bias_hh_.unsqueeze(0);
        }
    }

    void forward(const at::Tensor& input, at::Tensor* h_t, at::Tensor* c_t) {
#ifdef DEBUG
        assert(input.dim() == 2);
        assert(weight_ih_.dim() == 2);
        assert(h_t->dim() == 2);
        assert(weight_hh_.dim() == 2);
#endif
        at::native::mm_out(igates_, input, weight_ih_);
        at::native::mm_out(hgates_, *h_t, weight_hh_);
        
        THNN_CudaDoubleLSTMFused_updateOutput(
            at::globalContext().getTHCState(),
            GetTH(igates_), GetTH(hgates_),
            GetTH(bias_ih_), GetTH(bias_hh_),
            GetTH(*c_t), GetTH(*h_t), GetTH(*c_t));
    }

private:
    const int input_size_;
    const int hidden_size_;
    const int gate_size_;

    at::Tensor weight_ih_;
    at::Tensor weight_hh_;
    at::Tensor bias_ih_;
    at::Tensor bias_hh_;

    // Temporaries
    at::Tensor igates_;
    at::Tensor hgates_;
};
