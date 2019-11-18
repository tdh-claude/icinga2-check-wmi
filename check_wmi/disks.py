import math
import sys
from collections import namedtuple

import sh

import check_wmi as check


def check_disks(wmic, options):
    # Return condition
    cond = check.OK
    ret_code = check.OK_CODE

    ld_lst = []

    # Checking only Local HardDrive
    where = "DriveType = 3"

    # Building where clause for choosed drives
    if options.check == 'disk':
        where += " and ( DeviceID like "
        count = 0
        for device_id in options.arguments:
            if count > 0:
                where += " or DeviceId like "
            where += "'" + device_id + "%'"
            count += 1
        where += ")"

    # Executing WQL
    try:
        wmi_dataset = wmic.query(
            "SELECT SystemName, DeviceID, VolumeName, Size, FreeSpace FROM Win32_LogicalDisk WHERE " + where)
    except sh.ErrorReturnCode:
        ret_code = check.CRI_CODE
        cond = check.CRI
        print(cond + ' WMI Query return an exception')
        return ret_code

    # Checking WMI returning values and building status return value
    for ld in wmi_dataset:
        # Calculate used percent
        percent = int(round(100 - int(ld['FreeSpace']) / int(ld['Size']) * 100, 0))
        ld['used_percent'] = percent

        # Evaluating usage disk and set condition
        if percent > int(options.critical[0]):
            ld['condition'] = check.CRI
            ld['ret_code'] = check.CRI_CODE
            cond = check.CRI
            ret_code = check.CRI_CODE
        elif percent > int(options.warning[0]):
            ld['condition'] = check.WAR
            ld['ret_code'] = check.WAR_CODE
            if check.WAR_CODE > ret_code:
                ret_code = check.WAR_CODE
                cond = check.WAR
        else:
            ld['condition'] = check.OK
            ld['ret_code'] = check.OK_CODE

        # Defining disk size unit (KB, MB, GB or TB)
        if len(ld['Size']) < 7:
            ld['unit'] = 'KB'
            ld['Size'] = round(int(ld['Size']) / math.pow(1024, 1), 2)
            ld['FreeSpace'] = round(int(ld['FreeSpace']) / math.pow(1024, 1), 2)
        elif len(ld['Size']) < 10:
            ld['unit'] = 'MB'
            ld['Size'] = round(int(ld['Size']) / math.pow(1024, 2), 2)
            ld['FreeSpace'] = round(int(ld['FreeSpace']) / math.pow(1024, 2), 2)
        elif len(ld['Size']) < 13:
            ld['unit'] = 'GB'
            ld['Size'] = round(int(ld['Size']) / math.pow(1024, 3), 2)
            ld['FreeSpace'] = round(int(ld['FreeSpace']) / math.pow(1024, 3), 2)
        elif len(ld['Size']) < 16:
            ld['unit'] = 'TB'
            ld['Size'] = round(int(ld['Size']) / math.pow(1024, 4), 2)
            ld['FreeSpace'] = round(int(ld['FreeSpace']) / math.pow(1024, 4), 2)

        # Convert tuple to Object and adding in list of Disks
        x = namedtuple("LogicalDisk", ld.keys())(*ld.values())
        ld_lst.append(x)
        # print(x)

    # Generating output string
    # Condition result (Message)
    result = cond
    if cond == check.OK:
        result += ' All ' + str(len(ld_lst)) + ' drive(s) are ok.'
    else:
        for i in ld_lst:
            if i.condition == check.WAR:
                result += ' ' + i.DeviceID + ' ' + str(i.used_percent) + '% > ' + options.warning[0] + '%'
            if i.condition == check.CRI:
                result += ' ' + i.DeviceID + ' ' + str(i.used_percent) + '% > ' + options.critical[0] + '%'
            if i.condition == check.UNK:
                result += ' Unknown condition for ' + i.DeviceID
    # Metric
    result += '|'
    for i in ld_lst:
        vn = ''
        if i.VolumeName:
            vn = "[" + i.VolumeName + "]"
        # result += "'" + i.DeviceID + vn + " used'="
        result += "'" + i.DeviceID + vn + "'="
        result += str(round(i.Size - i.FreeSpace, 2)) + i.unit + ";"  # Monitored value
        result += str(round(i.Size * float(options.warning[0]) / 100, 2)) + ";"  # Warning value
        result += str(round(i.Size * float(options.critical[0]) / 100, 2)) + ";"  # Critical value
        result += "0;"  # N/A
        result += str(round(i.Size, 2))  # Max value
        result += ' '

    print(result)
    sys.exit(ret_code)
