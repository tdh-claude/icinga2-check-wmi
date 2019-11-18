from .cpu import check_cpu
from .disks import check_disks
from .memory import check_memory
from .services import check_services

__author__ = 'Claude Débieux'
__VERSION__ = '0.0.0.0'

# Return Text and code
OK = 'OK'
OK_CODE = 0
WAR = 'WARNING'
WAR_CODE = 1
CRI = 'CRITICAL'
CRI_CODE = 2
UNK = 'UNKNOWN'
UNK_CODE = 3

# Critical and Warning Constant
COND = 'cond'       # Condition
PHYS = 'phys'       # Physical memory [%]
COMM = 'comm'       # Commited [%]
HF   = 'hf'         # Memory hardfault [Number of page]
PFU  = 'pfu'        # Pagefile usage [%]
