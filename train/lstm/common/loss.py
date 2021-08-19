import torch
import torch.nn.functional as F


def weighted_binary_cross_entropy(output, target, weight0=0.5):
    epsilon = 1e-7
    output_ = torch.clamp(output, epsilon, 1 - epsilon)
    target_ = torch.clamp(target, epsilon, 1 - epsilon)
    loss = (1 - weight0) * (target * torch.log(output_)) + \
               weight0 * ((1 - target) * torch.log(1 - output_))
    return torch.neg(torch.mean(loss))

def rescaled_mean_absolute_log_error(output, target, discretized_max = 1000.0):
    epsilon = 1e-7
    output_ = torch.clamp(output, epsilon, discretized_max)
    target_ = torch.clamp(target, epsilon, discretized_max)
    not_rescaled = torch.mean(torch.abs(torch.log(output_) - torch.log(target_)))
    return (not_rescaled / discretized_max)

def rescaled_mean_absolute_error(output, target, discretized_max = 1000.0):
    not_rescaled = torch.mean(torch.abs(output - target))
    return (not_rescaled / discretized_max)

def mean_absolute_error(output, target):
    return torch.mean(torch.abs(output - target))

def rescaled_mean_squared_error(output, target, discretized_max = 1000.0):
    return torch.mean(((output - target)/discretized_max)**2)

def rescaled_huber_loss(output, target, discretized_max = 1000.0):
    not_rescaled = F.smooth_l1_loss(output, target, size_average=False)
    return (not_rescaled / discretized_max)