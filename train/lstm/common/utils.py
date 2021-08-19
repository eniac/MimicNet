import h5py
import numpy as np
import torch


# from https://stackoverflow.com/questions/29831489/numpy-1-hot-array
def convertToOneHot(vector, num_classes=None):
    """
    Converts an input 1-D vector of integers into an output
    2-D array of one-hot vectors, where an i'th input value
    of j will set a '1' in the i'th row, j'th column of the
    output array.

    Example:
        v = np.array((1, 0, 4))
        one_hot_v = convertToOneHot(v)
        print one_hot_v

        [[0 1 0 0 0]
         [1 0 0 0 0]
         [0 0 0 0 1]]
    """
    assert isinstance(vector, np.ndarray)
    assert len(vector) > 0

    if num_classes is None:
        num_classes = np.max(vector)+1
    else:
        assert num_classes > 0
        assert num_classes >= np.max(vector)

    result = np.zeros(shape=(len(vector), num_classes))
    result[np.arange(len(vector)), vector] = 1
    return result.astype(int)

def save_ckpt(filename, model, start_epoch,
              dis_meta_last, dis_meta_ewma, dis_meta_latency):
    torch.save({'model_type': "LSTM",
                'variant': model.variant,
                'start_epoch': start_epoch,
                'input_size': model.input_size,
                'num_layers': model.num_layers,
                'window_size': model.window_size,
                'dis_meta_last_min': dis_meta_last[0],
                'dis_meta_last_step': dis_meta_last[1],
                'dis_meta_ewma_min': dis_meta_ewma[0],
                'dis_meta_ewma_step': dis_meta_ewma[1],
                'dis_meta_latency_min': dis_meta_latency[0],
                'dis_meta_latency_step': dis_meta_latency[1],
                'model_state_dict': model.state_dict()},
                filename)

def save_hdf5(filename, model, device, start_epoch,
              dis_meta_last, dis_meta_ewma, dis_meta_latency):
    with h5py.File(filename, 'w') as outf:
        dataset = outf.create_dataset('variant', data=model.variant)
        dataset = outf.create_dataset('start_epoch', data=start_epoch)
        dataset = outf.create_dataset('input_size', data=model.input_size)
        dataset = outf.create_dataset('num_layers', data=model.num_layers)
        dataset = outf.create_dataset('window_size', data=model.window_size)
        dataset = outf.create_dataset('dis_meta_last_min',
                                      data=dis_meta_last[0])
        dataset = outf.create_dataset('dis_meta_last_step',
                                      data=dis_meta_last[1])
        dataset = outf.create_dataset('dis_meta_ewma_min',
                                      data=dis_meta_ewma[0])
        dataset = outf.create_dataset('dis_meta_ewma_step',
                                      data=dis_meta_ewma[1])
        dataset = outf.create_dataset('dis_meta_latency_min',
                                      data=dis_meta_latency[0])
        dataset = outf.create_dataset('dis_meta_latency_step',
                                      data=dis_meta_latency[1])

        model.cpu()
        for key, val in model.state_dict().items():
            dataset = outf.create_dataset(key, data=val)
        model.to(device)