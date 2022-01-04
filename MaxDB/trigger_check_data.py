#!/usr/bin/env python3.8

import subprocess
import os


def linux_cmd(cmd):
        output = subprocess.check_output(cmd, shell=True)
        return(output.decode())


def get_sid(cmd):
        data_path = linux_cmd(cmd)
        sid = data_path.split("/")[2]
        # print("2. command to get sid in loop ")
        return(sid)




sid_cmd = "cat /etc/fstab | grep -i sapdata1 | awk '{print $2}'"
sid = get_sid(sid_cmd)

#print("\nSID is {0}".format(sid))


trigger_cmd = "su - sqd%s -c \"nohup dbmcli -U c db_execute check data &\""% sid.lower()
trigger = linux_cmd(trigger_cmd)

exit(0)

