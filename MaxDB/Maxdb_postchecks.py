#!/usr/bin/env python3.8

# Author : Kuldeep Rajpurohit (C5315737)
# Last Modified : 19th Oct 2022
# Reviewer : Kuldeep Rajpurohit (C5315737)


# Python script to automate maxdb post installation checks

import os, sys, subprocess
import math, getpass
import getopt
import re


def unix_cmd(cmd):
    output = subprocess.check_output(cmd, shell=True)
    return(output.decode())


try:
    argv = sys.argv[1:]
    opts, args = getopt.getopt(argv, "c:s:p")
except:
    print('Error in providing in command line arguments')


class color:
    red = '\033[91m'
    green = '\033[92m'
    bold = '\033[1m'
    end = '\033[0m'


print(color.bold,"      MaxDB Post Installation Checks                       ", color.end)


class Maxdb:

    def __init__(self):
        self.control_pass = None
        self.superdba_pass = None
        self.schema_pass = None

    def check_db_type(self):
        try:
            cmd = """cat /etc/fstab | grep -i sapdata1 | awk '{print $2}' """
            output = unix_cmd(cmd)
            # print(output)
            if "sapdb" in output.lower():
                self.sid = output.split("/")[2]
                self.db_user = 'sqd'+self.sid.lower()
                self.schema_user = self.sid.lower()+'adm'
                return(True)

            else:
                return(False)

        except:
            # error findingdb type or not a standard system
            return(False)


    # def check_xuser_connectivity(self):


    def check_user_connectivity(self, name, password):
        # try:
        cmd = """su - {} -c \"dbmcli -d {} -u {},{} db_state -v\" """.format(self.db_user, self.sid, name, password)
        output = s_open(cmd)
        if "User authorization failed" in output:
            print(color.red, "        Incorrect password for {} user".format(name), color.end)
        elif "OK" in output:
            print(color.green,"        Connection using {} user working fine".format(name),color.end)


    def get_passwd(self):
        try:
            for name, value in opts:
                if name in ['-c']:
                    self.control_pass = value
                elif name in ['-s']:
                    self.superdba_pass = value
        except:
            print(color.red, "Unable to assign arguments from command line.", color.end)
            exit(0)

        try:
            if not self.control_pass:
                self.control_pass = getpass.getpass(prompt="        Enter control user password : ")
            if not self.superdba_pass:
                self.superdba_pass = getpass.getpass(prompt="        Enter superdba user password : ")
            self.check_user_connectivity("control", self.control_pass)
            self.check_user_connectivity("superdba", self.superdba_pass)

        except:
            print(color.red,"Connection using entered password failed, try again with correct password.",color.end)


    def std_param_values(self):
        cmd = """cat /proc/cpuinfo | grep processor | wc -l """
        maxcps = math.ceil((int(unix_cmd(cmd).strip())/2)-1)
        if maxcps > 7:
            maxExclusiveLockCollisionLoops = '10000'
        else:
            maxExclusiveLockCollisionLoops = '-1'

        cmd = """cat /proc/meminfo | grep -i MemTotal | awk '{print $2}' """
        cacheMemorySize = math.ceil(float(unix_cmd(cmd))*0.32/8)
        officialNodeName = "LDDB"+self.sid.upper()

        self.std_values = [['DefaultCodePage', 'UNICODE'],
            ['MaxDataVolumes', '250'],
            ['LogQueueSize' ,'800'],
            ['MaxCPUs', str(maxcps)],
            ['LogQueues', str(maxcps)],
            ['MaxUserTasks', '100'],
            ['MaxSQLLocks', '500000'],
            ['CAT_CACHE_SUPPLY', '40000'],
            ['MaxExclusiveLockCollisionLoops', maxExclusiveLockCollisionLoops],
            ['MaxTaskStackSize', '1024'],
            ['MaxServerTaskStackSize', '512'],
            ['MaxSpecialTaskStackSize', '512'],
            ['CacheMemorySize', str(cacheMemorySize)],
            ['IndexlistsMergeThreshold', '500'],
            ['UseStrategyCache', 'NO'],
            ['KernelMessageFileSize', '8000'],
            ['AutoLogBackupSize', '25600'],
            ['OfficialNodeName', officialNodeName],
            ['UseFilesystemCacheForVolume', 'NO'],
            ['UseSharedSQL', 'YES'],
            ['HashJoinSingleTableMemorySize', '4000'],
            ['HashJoinTotalMemorySize', '24000'],
            ['UseHashedResultset', 'YES'],
            ['EnableOuterJoinOptimization', 'YES'],
            ['EnableFirstRowAccessOptimization', 'YES'],
            ['ParallelJoinServerTasks', '0'],
            ['EnableVariableInput', 'YES'],
            ['UpdateStatParallelServerTask', '0'],
            ['UseVectorIOSimulation', 'NEVER']]


    def set_param_to_std(self, name, value, act_val):
        try:
            cmd = """su - {} -c \"dbmcli -U c param_directput {} {} \" """.format(self.db_user, name, value)
            unix_cmd(cmd)
            strin = """su - {} -c \"dbmcli -U c -nohold param_directget {}\" | tail -1 """.format(self.db_user, name)
            output = unix_cmd(strin).strip().split()[1]
            if output == value:
                print(color.green,"{:<45} {:<15}".format(name,value), color.end, " changed from ", color.red, "{} to ".format(act_val), color.green, "{}".format(output), color.end)

        except:
            print(color.red, "Error changing {} parameter, check manaully.".format(name), color.end)


    def cmp_val(self, name, std_val, act_val):

        if std_val == act_val:
            print(color.green,"{:<45} {:<15} {:<15}".format(name, std_val, act_val),color.end)
        else:
            # print(color.red,"{:<45} {:<15} {:<15}".format(name, std_val, act_val),color.end)
            self.set_param_to_std(name, std_val, act_val)


    def check_params(self):
        print("{:<45} {:<15} {:<15}".format("Parameter name", "Standard", "Present"))
        for each in self.std_values:
            strin = """su - {} -c \"dbmcli -U c -nohold param_directget {}\" | tail -1 """.format(self.db_user, each[0])
            output = unix_cmd(strin).strip().split()[1]
            # compare values
            self.cmp_val(each[0], each[1], output)


    def xusers_availability(self):
        cmd = """su - {} -c \" xuser list\" | grep -i key | wc -l """.format(self.db_user)
        output = unix_cmd(cmd).strip()
        if not output == '0':
            print(output)
        else:
            print("Xusers not present")
            # create xusers here


def main():
    maxdb = Maxdb()
    is_maxdb = maxdb.check_db_type()
    if is_maxdb:
        print("SID : ", color.green, maxdb.sid, color.end)
        maxdb.get_passwd()
        maxdb.xusers_availability()
        maxdb.std_param_values()
        maxdb.check_params()

    else:
        print(color.red, "Not a maxdb system or not a standard system. Quitting", color.end)



if __name__ == '__main__':
    main()
