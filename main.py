import sys
import os
from hardware_collector_lib.main import get_device_info
import json

def get_info_device():
    all_info = get_device_info()
    print(all_info)

if __name__ == "__main__":
    get_info_device()