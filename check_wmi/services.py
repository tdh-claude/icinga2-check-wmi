import sys
from collections import namedtuple

import sh

import check_wmi as check


def check_services(wmic, options):
    ret_code = check.OK_CODE
    ret_cond = check.OK
    msg = ""
    where = ""
    services = {}

    # Building where clause for services
    where += "(Name like "
    count = 0
    for s in options.arguments:
        if count > 0:
            where += " or Name like "
        where += "'" + s + "'"
        count += 1
    where += ")"

    # Executing WQL
    try:
        wmi_dataset = wmic.query(
            "SELECT Name, Caption, Started, State, StartMode, Status FROM Win32_BaseService WHERE " + where)
    except sh.ErrorReturnCode:
        ret_code = check.CRI_CODE
        cond = check.CRI
        print(cond + ' WMI Query return an exception')
        return ret_code

    for s in wmi_dataset:
        services[s['Name'].lower()] = namedtuple('Service', s.keys())(*s.values())

    # Check if service is defined on host
    for s in options.arguments:
        if not s.lower() in services:
            ret_cond = check.CRI
            ret_code = check.CRI_CODE
            msg += "Missing service " + s
            break

        if services[s.lower()].State.lower() != "running":
            ret_cond = check.CRI
            ret_code = check.CRI_CODE
            msg += " " + services[s.lower()].Caption + " is " + services[s.lower()].State

    if ret_cond == check.OK:
        if services.__len__() > 1:
            msg += "All " + str(services.__len__()) + " services are Running"
        else:
            msg += "Service '" + services[options.arguments[0].lower()].Caption + "' is Running"

    result = ret_cond + " " + msg
    print(result)
    sys.exit(ret_code)

