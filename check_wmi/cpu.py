import sys
from collections import namedtuple

import sh

import check_wmi as check


def check_cpu(wmic, options):
    ret_code = check.UNK_CODE
    ret_cond = check.UNK
    msg = "Unknown condition"

    # Executing WQL
    try:
        wmi_dataset = wmic.query(
            "SELECT PercentProcessorTime, DPCsQueuedPersec, PercentPrivilegedTime, PercentDPCTime, PercentInterruptTime "
            "FROM  Win32_PerfFormattedData_PerfOS_Processor ")
        processor = namedtuple("processor", wmi_dataset[0].keys())(*wmi_dataset[0].values())
        # print(processor)

        wmi_dataset = wmic.query("SELECT ProcessorQueueLength "
                                 "FROM  Win32_PerfFormattedData_PerfOS_System ")
        queue_length = namedtuple("queue_length", wmi_dataset[0].keys())(*wmi_dataset[0].values())
        # print(queue_length)

    except sh.ErrorReturnCode:
        ret_code = check.CRI_CODE
        cond = check.CRI
        print(cond + ' WMI Query return an exception')
        return ret_code

    # Check CPU usage
    if int(processor.PercentProcessorTime) > int(options.critical[0]):
        ret_code = check.CRI_CODE
        ret_cond = check.CRI
        msg = processor.PercentProcessorTime + "% > " + options.critical[0] + "%"
    elif int(processor.PercentProcessorTime) > int(options.warning[0]):
        ret_code = check.WAR_CODE
        ret_cond = check.WAR
        msg = processor.PercentProcessorTime + "% > " + options.warning[0] + "%"
    else:
        ret_code = check.OK_CODE
        ret_cond = check.OK
        msg = "CPU is Ok"

    # Building metric
    metric = "'CPU usage'=" + processor.PercentProcessorTime + "%;" + options.warning[0] + ";" + options.critical[0]
    metric += " 'DPCs queued/s'=" + processor.DPCsQueuedPersec
    metric += " 'Queue Length'=" + queue_length.ProcessorQueueLength

    result = ret_cond + " " + msg + "|" + metric
    print(result)
    sys.exit(ret_code)
