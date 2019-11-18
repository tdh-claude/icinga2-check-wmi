#!/usr/bin/env python

import argparse
import sys

import wmi_client_wrapper as wmi

import check_wmi


def parse_args():
    version = 'check_wmi.py, Version %s' % check_wmi.__VERSION__
    parser = argparse.ArgumentParser(description='Scripts arguments')
    parser.add_argument('-V', '--version', dest='version', action='store_true',
                        help='Print version of script')
    req_args = parser.add_argument_group('required arguments')
    req_args.add_argument('-H', '--host', dest='host', required=True,
                          help='Hostname or IP Address.')
    req_args.add_argument('-u', '--username', dest='username', required=True,
                          help='Domain/Workgroup username')
    req_args.add_argument('-p', '--password', dest='password', required=True,
                          help='Password')
    req_args.add_argument('-C', '--check', dest='check', required=True,
                          choices=['disks', 'disk', 'cpu', 'memory', 'services'],
                          help='Object to check_wmi')
    req_args.add_argument('-a', '--arguments', dest='arguments', nargs='*',
                          help='argument to check')
    req_args.add_argument('-c', '--critical', dest='critical', nargs='*',
                          help='critical value(s)')
    req_args.add_argument('-w', '--warning', dest='warning', nargs='*',
                          help='warning value(s)')
    opt = parser.parse_args()

    if (opt.check == 'disk' or opt.check == 'services') and opt.arguments is None:
        parser.error("UNKNOWN Missing arguments for check_wmi " + opt.check)
        sys.exit(3)

    if opt.version:
        print(version)

    return opt


def main():
    # Parsing script arguments
    options = parse_args()

    # Connecting remote host
    wmic = wmi.WmiClientWrapper(
        username=options.username,
        password=options.password,
        host=options.host,
    )

    if options.check == 'disks' or options.check == 'disk':
        sys.exit(check_wmi.check_disks(wmic, options))
    elif options.check == 'memory':
        sys.exit(check_wmi.check_memory(wmic, options))
    elif options.check == 'cpu':
        sys.exit(check_wmi.check_cpu(wmic, options))
    elif options.check == 'services':
        sys.exit(check_wmi.check_services(wmic, options))
    else:
        print("CRITICAL Check" + options.check + " not yet implemented")
        sys.exit(2)


if __name__ == "__main__":
    main()
