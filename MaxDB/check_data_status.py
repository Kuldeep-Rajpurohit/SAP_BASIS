#!/usr/bin/env python3.8

import subprocess
import os


def linux_cmd(cmd):
        output = subprocess.check_output(cmd, shell=True)
        return(output.decode())


def get_sid(cmd):
        data_path = linux_cmd(cmd)
        sid = data_path.split("/")[2]
        return(sid)


def get_run_dir_path(cmd):
        output = linux_cmd(cmd)
        run_dir_path = output.split()
        # print(run_dir_path)
        return(run_dir_path[0])


def get_latest_cdb(run_dir_path):
        dbahist_path = str(run_dir_path + "/dbahist")
        # print("dbahist path is {0}".format(dbahist_path))
        go_to_dbahist_cmd = "cd %s"%dbahist_path
        os.chdir(dbahist_path)
        # print(os.getcwd())
        file_name_cmd = "ls -altr | grep -i .cdb | tail -1 | awk '{print $9}'"      
        file_status_cmd = "cat `ls -altr | grep -i .cdb | tail -1 | awk '{print $9}'`"
        file_name = linux_cmd(file_name_cmd)
        status = linux_cmd(file_status_cmd)
        print(file_name)
        print(status)



sid_cmd = "cat /etc/fstab | grep -i /sapdb/***/sapdata1 | awk '{print $2}'"
sid = get_sid(sid_cmd)
print("\nSID : {0}".format(sid))


run_dir_path_cmd = "su - sqd%s -c \"dbmcli -U c -nohold param_directget RunDirectoryPath\"| awk '{print $2}'"% sid.lower()
run_dir_path = get_run_dir_path(run_dir_path_cmd)
print("Run directory path : {0}\n".format(run_dir_path))
get_latest_cdb(run_dir_path)

exit(0)
