import time
import torch
import numpy as np

from utils import logger
from dataset import synthetic_env
from options import train_options

from models import relighting_env_init, \
        relighting_env_cas1, relighting_env_cas2

"""Relighting with point light + evironment map"""

# Options
opts = train_options.TrainOptions().parse()
opts.name = 'relighting_env'
opts.outf = './data'
opts.reuse = False
opts.workers = 32
opts.batch_size = 16
opts.start_epoch = 0
opts.data_root = './data/dataset/Synthetic'
opts.gpu_id = list(range(torch.cuda.device_count()))

# TODO: define the training stage
# 0: initial stage
# 1: cascade 1
# 2: cascade 2
opts.cascade = 0  

print('--> pytorch can use %d GPUs'  %(torch.cuda.device_count()))
print('--> pytorch is using %d GPUs' %(len(opts.gpu_id)))
print('--> GPU IDs:', opts.gpu_id)

logger.print_options(opts)

# Dataloader
dataset = synthetic_env.SyntheticData(dataRoot=opts.data_root)
dataloader = torch.utils.data.DataLoader(dataset, batch_size=opts.batch_size, \
                    shuffle=opts.shuffle, pin_memory=True, num_workers=opts.workers)
opts.niter = len(dataloader)

# Model
if opts.cascade == 0:
    model = relighting_env_init.Model(opts)
if opts.cascade == 1:
    model = relighting_env_cas1.Model(opts)
if opts.cascade == 2:
    model = relighting_env_cas2.Model(opts)

# Train models
print('--> start to train')
for epoch in range(opts.start_epoch, opts.nepoch[0]):
    prefetcher = synthetic_env.DataPrefetcher(dataloader)
    data = prefetcher.next()
    i = 0
    while data is not None:
        i += 1
        model.set_input_var(data)
        model.update()
        model.print_loss(epoch, i)

        if i % 100 == 0:
            print('--> current time: ', time.strftime("%Y/%m/%d %H:%M:%S", time.localtime()))
            model.flush_error_npy()
            model.save_cur_sample(epoch)
        if i % 3000 == 0 and i != 0:
            model.save_error_to_file(epoch)
            model.save_cur_checkpoint(epoch)
        data = prefetcher.next()

    # save model
    model.save_error_to_file(epoch)
    model.save_cur_checkpoint(epoch)

    if (epoch + 1) % 2 == 0:
        model.update_lr()