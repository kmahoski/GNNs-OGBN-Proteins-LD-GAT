# new code start
import os
os.environ["CUDA_DEVICE_ORDER"] = "PCI_BUS_ID"
os.environ["CUDA_VISIBLE_DEVICES"] = "1"
import torch
import numpy as np
from types import SimpleNamespace as SN
import subprocess as sp
from pathlib import Path

print(os.environ['CUDA_VISIBLE_DEVICES'])
#torch.zeros(1).cuda()
print(torch.__version__)
#print(torch.cuda.is_available())
print(torch.__file__)


class ServerInfo:
    def __init__(self):
        self.gpu_mem, self.gpus, self.n_gpus = 0, [], 0
        try:
            command = "nvidia-smi --query-gpu=memory.total --format=csv"
            gpus = sp.check_output(command.split()).decode('ascii').split('\n')[:-1][1:]
            self.gpus = np.array(range(len(gpus)))
            self.n_gpus = len(gpus)
            self.gpu_mem = round(int(gpus[0].split()[0]) / 1024)
            self.sv_type = f'{self.gpu_mem}Gx{self.n_gpus}'
        except:
            print('NVIDIA-GPU not found, set to CPU.')
            self.sv_type = f'CPU'

    def __str__(self):
        return f'SERVER INFO: {self.sv_type}'


print(ServerInfo().gpu_mem)


#device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
#print(f"Using device: {device}")
