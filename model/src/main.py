import os
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
import torch
import torchvision

print("PyTorch version:", torch.__version__)
print("Torchvision version:", torchvision.__version__)
print("CUDA available:", torch.cuda.is_available())
print("CUDA toolkit version PyTorch was built with:", torch.version.cuda)

if torch.cuda.is_available():
    print("Current device:", torch.cuda.get_device_name(0))
    # Thông tin chi tiết
    props = torch.cuda.get_device_properties(0)
    print(f"  • Total memory: {props.total_memory/1024**3:.1f} GB")
    print(f"  • Compute capability: {props.major}.{props.minor}")
