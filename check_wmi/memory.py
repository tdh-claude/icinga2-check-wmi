import re
import sys
from collections import namedtuple

import sh

import check_wmi as check


def check_memory(wmic, options):
    # Parsing parameter
    warning_dict = {}
    critical_dict = {}
    keyword = re.compile('(cond|phys|comm|hf|pfu):(.*)', re.IGNORECASE)

    for w in options.warning:
        if keyword.match(w):
            key = (re.split(':', w)[0]).lower()
            value = re.split(':', w)[1]
            warning_dict[key] = value
        else:
            print("UNKNOWN Error WMI memory check_wmi wrong check_wmi argument (Warning) <" + re.split(':', w)[
                0] + ">, must be {cond|phys|comm|hf|pfu}")
            sys.exit(check.UNK_CODE)
    if check.COND not in warning_dict:
        warning_dict[check.COND] = 1
    warning = namedtuple("Warning", warning_dict.keys())(*warning_dict.values())

    for c in options.critical:
        if keyword.match(c):
            key = (re.split(':', c)[0]).lower()
            value = re.split(':', c)[1]
            critical_dict[key] = value
        else:
            print("UNKNOWN Error WMI memory check_wmi wrong check_wmi argument (Critical) <" + re.split(':', c)[
                0] + ">, must be {cond|phys|comm|hf|pfu}")
            sys.exit(check.UNK_CODE)
    if check.COND not in critical_dict:
        critical_dict[check.COND] = '1'
    critical = namedtuple("Critical", critical_dict.keys())(*critical_dict.values())

    # Executing WQL
    try:
        wmi_dataset = wmic.query(
            "SELECT PageFaultsPersec, PagesPersec, PageWritesPersec, PageReadsPersec,  PagesInputPersec, CommittedBytes, CommitLimit, PercentCommittedBytesInUse, PoolNonpagedBytes "
            "FROM Win32_PerfFormattedData_PerfOS_Memory")
        memory = namedtuple("Memory", wmi_dataset[0].keys())(*wmi_dataset[0].values())

        wmi_dataset = wmic.query(
            "SELECT PercentUsage, PercentUsagePeak FROM Win32_PerfFormattedData_PerfOS_PagingFile WHERE name = '_Total'")
        page_file = namedtuple("Page_File", wmi_dataset[0].keys())(*wmi_dataset[0].values())

        wmi_dataset = wmic.query(
            "SELECT FreePhysicalMemory, TotalVisibleMemorySize, TotalVirtualMemorySize FROM Win32_OperatingSystem")
        physical_memory = namedtuple("physical_memory", wmi_dataset[0].keys())(*wmi_dataset[0].values())
    except sh.ErrorReturnCode:
        ret_code = check.CRI_CODE
        cond = check.CRI
        print(cond + ' WMI Query return an exception')
        return ret_code

    # Checking WMI returning values and building status return value
    warning_count = 0
    critical_count = 0
    msg = ''
    pfu_metric = ''
    phys_metric = ''
    comm_metric = ''
    hf_metric = ''

    # Evaluating pagefile usage and set condition
    try:
        if int(page_file.PercentUsage) > int(critical.pfu):
            critical_count += 1
            msg += ' Pagefile usage ' + page_file.PercentUsage + '% > ' + critical.pfu + '%'
        elif int(page_file.PercentUsage) > int(warning.pfu):
            warning_count += 1
            msg += ' Pagefile usage ' + page_file.PercentUsage + '% > ' + warning.pfu + '%'
        pfu_metric = "'pagefile use'=" + page_file.PercentUsage + "%;" + warning.pfu + ";" + critical.pfu + " "
    except AttributeError:
        pass

    # Evaluating Physical memory usage
    try:
        phys_usage = int(
            round(100 - (int(physical_memory.FreePhysicalMemory) / int(physical_memory.TotalVisibleMemorySize) * 100),
                  0))
        if phys_usage > int(critical.phys):
            critical_count += 1
            msg += ' Memory usage ' + str(phys_usage) + '% > ' + critical.phys + '%'
        elif phys_usage > int(warning.phys):
            warning_count += 1
            msg += ' Memory usage ' + str(phys_usage) + '% > ' + warning.phys + '%'
        phys_metric = "'Memory use'=" + str(phys_usage) + "%;" + warning.phys + ";" + critical.phys + " "
    except AttributeError:
        pass

    # Evaluating committed memory
    try:
        if int(memory.PercentCommittedBytesInUse) > int(critical.comm):
            critical_count += 1
            msg += ' Committed ' + memory.PercentCommittedBytesInUse + '% > ' + critical.comm + '%'
        elif int(memory.PercentCommittedBytesInUse) > int(warning.comm):
            warning_count += 1
            msg += ' Committed ' + memory.PercentCommittedBytesInUse + '% > ' + warning.comm + '%'
        comm_metric = "'Committed'=" + memory.PercentCommittedBytesInUse + "%;" + warning.comm + ";" + critical.comm + " "
    except AttributeError:
        pass

    # Evaluating memory hard fault pages rate
    try:
        if int(memory.PageFaultsPersec) > int(critical.hf):
            critical_count += 1
            hf_cond = 'CRITICAL'
            msg += ' Hard page fault rate ' + memory.PageFaultsPersec + ' > ' + critical.hf
        elif int(memory.PageFaultsPersec) > int(warning.hf):
            warning_count += 1
            hf_cond = 'WARNING'
            msg += ' Hard page fault rate ' + memory.PageFaultsPersec + ' > ' + warning.hf
        hf_metric = "'Hard page fault rate'=" + memory.PageFaultsPersec + ";" + warning.hf + ";" + critical.hf + " "
    except AttributeError:
        pass

    # Generating output string
    # Condition result (Message)
    if critical_count >= int(critical.cond):
        cond = check.CRI
        ret_code = check.CRI_CODE
    elif warning_count >= int(warning.cond):
        cond = check.WAR
        ret_code = check.WAR_CODE
    else:
        cond = check.OK
        ret_code = check.OK_CODE
    result = cond

    # Metric
    result += msg + '|' + pfu_metric + phys_metric + comm_metric + hf_metric

    print(result)
    sys.exit(ret_code)
