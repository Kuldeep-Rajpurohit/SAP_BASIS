#!/usr/bin/env python3.8



#########################################################
###       Author        : Kuldeep Rajpurohit          ###
###       Cuser ID      : C5315737                    ###
###       Last updated  : 02 March 2023               ###
###       Title         : Run Directory Check         ###
#########################################################

# Purpose of the script :
"""
The below script performs the Hana post installation checks as per GLDS standard wiki mentioned below :
The below script is to check dun directory path's utilization.
Checks done for : MaxDB, Oracle, DB2/DB6, Sybase
States : 
OK          : <50
Warning     : >=50 <70
Critical    : >70
"""


import subprocess, os, sys
import re
import shutil


class system:
    db_type = None
    sid = None
    path = None
    param_name = None
    percent = 0


# run unix queries and return the output
def unix_cmd(cmd):
    temp = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    output, err = temp.communicate()
    rc = temp.returncode
    return(rc, output.decode())


def flag_file():
    try:
        file_name = "/var/log/nagios/heal_db_rundir_flagfile"
        file_path = "/var/log/nagios"
        exists = os.path.exists(file_path)

        # check if /var/log/nagios path exists
        if not exists:
            # print("doesn't exist")
            os.mkdir(file_path)
            with open(file_name, 'w') as ffile:
                ffile.write('0')
                return()

        else:
            # check if file exists in /var/log/nagios path
            if os.path.exists(file_name):
                with open(file_name, 'r') as ffile:
                    flagValue = ffile.read()
                    return (flagValue)
            else:
                with open(file_name, 'w') as ffile:
                    ffile.write('0')
                    return()

    except:
        print("Critical. Error checking flagfile status.")
        return(2)


def update_flagfile(val):
    file_name = "/var/log/nagios/heal_db_rundir_flagfile"
    with open(file_name, 'w') as ffile:
        ffile.write(val)


def get_usage():
    # get mount utilization percent(%) using df -lh command
    cmd = """df -lh --output=pcent {} | tail -1 """.format(system.path)
    rc, output = unix_cmd(cmd)
    pattern = re.compile(r'(\d{1,2})')
    matches = pattern.finditer(output)

    for each in matches:
        system.percent = int(each.group(1))


# get db flavour and SID
def get_db_type():
    cmd = """ cat /etc/fstab | grep -i sapdata | grep -iv '#' | uniq """
    rc, output = unix_cmd(cmd)
    temp = output.strip().split("\n")

    # system has more than 1 data mounts, not a standard setup hence exit
    if len(temp) > 1:
        print("Warning. Not a standard system.")
        exit(1)

    # no data instance found, exit with OK
    elif len(temp) == 0:
        print("OK. No DB instance found.")
        exit(0)

    # create a pattern to find sid and database type
    pattern = re.compile(r'/+(\w{3,6})+/+(\w{3})/sapdata')    
    matches = pattern.finditer(output)

    for each in matches:
        # print(each)
        system.db_type = each.group(1)
        system.sid = each.group(2)

    # print(system.db_type, system.sid)
    return()


def status():
    # usage is < 50 hence exit with 0 and ok status
    if system.percent < 50 :
        print("{}, Run directory utilization is {}%".format(system.db_type.upper(), system.percent))
        update_flagfile('0')
        exit(0)
    elif system.percent < 70 :
        print("{}: Run directory utilization is {}%".format(system.db_type.upper(), system.percent))
        update_flagfile('0')
        exit(1)
    else:
        print("{}: Run directory utilization is {}%".format(system.db_type.upper(), system.percent))
        update_flagfile('0')
        exit(2)


def sapdb():
    cmd = """su - sqd%s -c \"dbmcli -U c -nohold param_directget RunDirectory\" | grep -i rundirectory | awk '{print $2}' """%system.sid.lower()
    rc, output = unix_cmd(cmd)
    temp = output.strip()
    if temp == "":
        print("Maxdb: Unable to find run directory path.")
        exit(1)

    system.param_name = 'run directory path'
    system.path = output.strip()
    return()


def sybase():
    cmd = """su - syb%s -c 'printenv PATH' | cut -d: -f1- | tr ":" "\n" | grep -i install """%system.sid.lower()
    rc, output = unix_cmd(cmd)
    system.param_name = "SYBASE $PATH"
    system.path = output.strip()
    if system.path == "":
        print("Sybase: Unable to find ASE-**/install path.")
        exit(1)
    return()


def db2():
    cmd = """su - db2%s -c 'db2 get dbm cfg' | grep '(DIAGPATH)' """%system.sid.lower()
    rc, output = unix_cmd(cmd)
    temp = output.strip()
    if output.strip() == "":
        print("DB2: Run directory path doesn't exist.")
        exit(1)
    param_name, value = temp.split('=')
    system.param_name = 'DIAGPATH'
    system.path = value.strip()
    return()


def oracle():
    cmd = """su - ora%s -c 'sqlplus / as sysdba <<EOF
    show parameter diagnostic_dest
    exit
    EOF' | grep -i diagnostic_dest """%system.sid.lower()
    rc, output = unix_cmd(cmd)
    temp = output.strip()
    if temp == "" :
        print("Oracle: DIAGNOSTIC_DEST path doesn't exist.".format(system.sid))
        exit(1)

    system.param_name = 'diagnostic_path'
    system.path = temp.split()[2]
    return()


def main():
    flag_file()
    get_db_type()
    # if db type is hana, exit with okay
    if system.db_type == 'hdb':
        print("OK. Hana system")
        exit(0)
    elif system.db_type == 'sapdb':
        path = sapdb()
    elif system.db_type == 'oracle':
        path = oracle()
    elif system.db_type in ['db2', 'db6']:
        path = db2()
    elif system.db_type == 'sybase':
        path = sybase()
    else:
        print("OK. No standard DB instance present")
        exit(0)

    used = get_usage()
    status()


if __name__ == "__main__":
    main()
