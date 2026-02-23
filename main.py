import sys
import os
from device_lib.main import get_device_info
import json

def get_info_device():
    all_info = get_device_info()
    print(all_info)

    for key, value in all_info["cpu"].items():
        print(f"{key:20}: {value}")
    for gpu in all_info["gpu"]:
        for key, value in gpu.items():
            print(f"{key:20}: {value}")
    for key, value in all_info["ram"].items():
        print(f"{key:20}: {value}")

if __name__ == "__main__":
    get_info_device()