import sys
import os
from hardware_collector_lib.main import get_device_info
import json
from system_info_library.main import get_system_info

def get_info_device():
    all_info = get_device_info()
    print(all_info)

def get_info_os_standart():
    system_info = get_system_info(mode="standard")
    print(system_info)

def get_info_os_advanced():
    system_info = get_system_info(mode="advanced")
    print(system_info)

if __name__ == "__main__":
    get_info_device()