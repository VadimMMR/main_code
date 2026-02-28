import sys
import os
from hardware_collector_lib.main import get_device_info
import json
from system_info_lib.main import get_system_info

def get_info_device():
    system_info = get_system_info(mode="standard", formatter=None)
    all_info = get_device_info()
    print(system_info)
    print(all_info)

if __name__ == "__main__":
    get_info_device()