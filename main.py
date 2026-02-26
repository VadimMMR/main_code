import sys
import os
from hardware_collector_lib.main import get_device_info
from os_system_lib.main import get_complete_os_info
import json

def get_info_device():
    system_info = get_complete_os_info
    all_info = get_device_info()
    print(system_info)
    print(all_info)

if __name__ == "__main__":
    get_info_device()