import torch
print("CUDA Available: ", torch.cuda.is_available())
print("Number of CUDA Devices:", torch.cuda.device_count())
print(torch.version.cuda)

# output 
# CUDA Available:  False
#Number of CUDA Devices: 