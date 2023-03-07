#!/usr/bin/env python3.8


#########################################################
###       Author        : Kuldeep Rajpurohit          ###
###       Cuser ID      : C5315737                    ###
###       Last updated  : 28th Nov 2022                ###
###       Title         : MAXDB Post Installation      ###
#########################################################

# Purpose of the script :
"""
The below script performs the MaxDB post installation checks as per GLDS standard wiki mentioned below :
https://wiki.one.int.sap/wiki/display/ITLABS/SAP+MaxDB+-+Post+installation+checks
"""


import os, sys, subprocess
import re
import getpass, getopt
import math


try:
    argv = sys.argv[1:]
    opts, args = getopt.getopt(argv, "c:s:a:p")
except:
    print('Error in providing in command line arguments')


class color:
    red = '\033[91m'
    green = '\033[92m'
    bold = '\033[1m'
    end = '\033[0m'


print(color.bold,"      MaxDB Post Installation Checks                       ", color.end)


def unix_cmd(cmd):
    temp = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    output, err = temp.communicate()
    returncode = temp.returncode
    return(returncode, output.decode())


class Maxdb:

    def __init__(self):
        self.control_pass = None
        self.superdba = None
        self.superdba_pass = None
        self.schema_pass = None
        self.schema_user = None


    def check_db_type(self):
        try:
            cmd = """cat /etc/fstab """
            rc, output = unix_cmd(cmd)
            matches = re.findall("sapdb/.../sapdata1", output)
            if matches:
                self.sid = matches[0].split('/')[1]
                self.db_user = "sqd" + self.sid.lower()
                self.app_user = self.sid.lower()+'adm'
                return(True)
            else:
                print(color.red, color.bold, "Unable to find SID", color.end)
                return(False)
        except:
            print("Error checking DB type")
            return(False)


    def check_user_connectivity(self, user, password):
        try:
            if user == "control":
                cmd = """su - {} -c \"dbmcli -d {} -u {},{} db_state\" """.format(self.db_user, self.sid, user, password)
            else:
                cmd = """su - {} -c \"dbmcli -U c -uSQL {},{} db_state \" """.format(self.db_user, user, password)
            rc, output = unix_cmd(cmd)
            if rc == 0:
                return(True, color.green + "OK" + color.end)
            else:
                if "User authorization failed" or "Unknown user name/password combination" in output:
                    return(False, color.red + "Incorrect password" + color.end)
                else:
                    return(False, color.red+ "Error"+ color.end)
        except:
            return(False, color.red+ "Error"+ color.end)


    def check_x_user(self, os_user, xuser, user, password):
        if xuser == 'c':
            temp = 0
            cmd = """su - {} -c \"dbmcli -U {} db_state\" """.format(os_user, xuser)    
        else:
            temp = 1
            cmd = """su - {} -c \" sqlcli -U {} -j 'select username from users' \" """.format(os_user, xuser)
        
        rc, output = unix_cmd(cmd)
        if not temp:
            if "OK" in output:
                return (True,color.green + "OK" + color.end)
        else:
            if user.lower() in output.lower():
                return(True, color.green + "OK" + color.end)

        cmd2 = """su - {} -c \"xuser set -U {} -d {} -u {},{} \" """.format(os_user, xuser, self.sid, user, password)
        rc2, output2 = unix_cmd(cmd2)
        if rc2 == 0:
            if self.check_x_user(os_user, xuser, user, password):
                return (True, color.green + "Created" + color.end)
            else:
                return (False, color.red + "Error" + color.end)
        else:
            return(False, color.red + "Error" + color.end)


    def get_db_status(self):
        cmd = """su - {} -c \"dbmcli -d {} -u control,{} db_state \" """.format(self.db_user, self.sid, self.control_pass)
        rc, output = unix_cmd(cmd)
        if "online" in output.lower():
            return True
        elif "offline" in output.lower():
            return False


    def get_version(self):
        cmd = """su - {} -c \"dbmcli -U c dbm_version \" | grep -i version """.format(self.db_user)
        rc, output = unix_cmd(cmd)
        self.db_version = output.split("=")[-1].strip()


    def get_passwd(self):
        try:
            for name, value in opts:
                if name in ['-c']:
                    self.control_pass = value
                elif name in ['-s']:
                    self.superdba_pass = value
                elif name in ['-a']:
                    self.schema_pass = value
        except:
            print(color.red, "Unable to assign arguments to command line.", color.end)
            exit(0)
        
        if not self.control_pass:
            self.control_pass = getpass.getpass(" Control user password  : ")
        if not self.superdba_pass:
            self.superdba_pass = getpass.getpass(" Superdba user password : ")
        if not self.schema_pass:
            self.schema_pass = getpass.getpass(" Schema user password   : ")


    def get_schema_user(self):
        cmd = """su - {} -c \"sqlcli -U w -j 'select username from users' \" | grep -i sap | grep -i {} """.format(self.db_user, self.sid)
        rc, output = unix_cmd(cmd)
        if output:
            output = output.replace('|', '').strip()
            self.schema_user = output
            return True
        else:
            print(color.red, "Unable to find schema user", color.end)
            return False


    def std_param_values(self):
        cmd = """cat /proc/cpuinfo | grep processor | wc -l """
        maxcpus = math.ceil((int(unix_cmd(cmd)[1].strip())/2)-1)
        if maxcpus > 7:
            maxExclusiveLockCollisionLoops = '10000'
            temp_max = 1
        else:
            maxExclusiveLockCollisionLoops = '-1'
            temp_max = 0
            
        cmd = """cat /proc/meminfo | grep -i MemTotal | awk '{print $2}' """
        cacheMemorySize = math.ceil(float(unix_cmd(cmd)[1])*0.32/8)
        officialNodeName = "LDDB"+self.sid.upper()

        self.std_values = [['DefaultCodePage', 'UNICODE', 0],
            ['MaxDataVolumes', '250', 0],
            ['LogQueueSize' ,'800', 0],
            ['MaxCPUs', str(maxcpus), 1],
            ['LogQueues', str(maxcpus), 0],
            ['MaxUserTasks', '100', 0],
            ['MaxSQLLocks', '500000', 0],
            ['CAT_CACHE_SUPPLY', '40000', 1],
            ['MaxExclusiveLockCollisionLoops', maxExclusiveLockCollisionLoops, temp_max],
            ['MaxTaskStackSize', '1024', 0],
            ['MaxServerTaskStackSize', '512', 0],
            ['MaxSpecialTaskStackSize', '512', 0],
            ['CacheMemorySize', str(cacheMemorySize), 0],
            ['IndexlistsMergeThreshold', '500', 0],
            ['UseStrategyCache', 'NO', 0],
            ['KernelMessageFileSize', '8000', 0],
            ['AutoLogBackupSize', '25600', 0],
            ['OfficialNodeName', officialNodeName, 0],
            ['UseFilesystemCacheForVolume', 'NO', 0],
            ['UseSharedSQL', 'YES', 0],
            ['HashJoinSingleTableMemorySize', '4000', 0],
            ['HashJoinTotalMemorySize', '24000', 0],
            ['UseHashedResultset', 'YES', 0],
            ['EnableOuterJoinOptimization', 'YES', 0],
            ['EnableFirstRowAccessOptimization', 'YES', 0],
            ['ParallelJoinServerTasks', '0', 0],
            ['EnableVariableInput', 'YES', 0],
            ['UpdateStatParallelServerTask', '0', 0],
            ['UseVectorIOSimulation', 'NEVER', 0]]


    def set_param_to_std(self, name, value, act_val):
        try:
            cmd = """su - {} -c \"dbmcli -U c param_directput {} {} \" """.format(self.db_user, name, value)
            rc, output = unix_cmd(cmd)
            if rc == 0:
                strin = """su - {} -c \"dbmcli -U c param_directget {}\" """.format(self.db_user, name)
                rc2, output2 = unix_cmd(strin)
                if rc2 == 0:
                    output2 = output2.split()[2]
                    if output2 == value:
                        print("{:<45} ".format(name), color.red,"{:<15}".format(act_val), color.green, "{}".format(output2), color.end)
                    else:
                        print(color.red, "Error changing {} parameter, check manaully.".format(name), color.end)
                        return
                else:
                    print(color.red, "Error changing {} parameter, check manaully.".format(name), color.end)
            else:
                print(color.red, "Error changing {} parameter, check manaully.".format(name), color.end)
        except:
            print(color.red, "Error changing {} parameter, check manaully.".format(name), color.end)


    def check_params(self):
        print("\n",color.bold, '\033[4m', "{:<45} {:<15} {:<15}".format("Parameter name", "Old value", "Standard/New Value"),'\033[0m', color.end)
        for each in self.std_values:
            strin = """su - {} -c \"dbmcli -U c param_directget {}\" """.format(self.db_user, each[0])
            rc , output = unix_cmd(strin)
            if rc == 0:
                try:
                    output = output.split()[2]
                    # parameter value is fixed 
                    if each[2] == 0:
                        if each[1] == output:
                            print("{:<45} ".format(each[0]), color.green,"{:<15} {:<15}".format(output, each[1]),color.end)
                        else:
                            self.set_param_to_std(each[0], each[1], output)
                    # parameter is not fixed
                    elif each[2] == 1:
                        if output >= each[1]:
                            print("{:<45} ".format(each[0]), color.green,"{:<15} {:<15}".format(output,">="+ each[1]),color.end)
                        else:
                            self.set_param_to_std(each[0], each[1], output)
                
                # this except is raised when earlier no value was present for a parameter
                except:
                    self.set_param_to_std(each[0] ,each[1], "None")
                    # print("Error getting parameter \t\t\t", color.red, "{}".format(each[0]), color.end)
            else:
                print("Error getting parameter \t\t\t", color.red, "{}".format(each[0]), color.end)


    def set_dbadtl_param(self):
        # set parameter if db version is >= 7.9
        if float(self.db_version[:3]) >= 7.9:
            try:
                cmd = """su - {} -c \"dbmcli -U c dbm_configget DBADTL \" """.format(self.db_user)
                rc, output = unix_cmd(cmd)
                output = int(output.split()[1])
                if output == 1:
                    print("{:<45} ".format("DBADTL"), color.green,"{:<15} {:<15}".format("1", output),color.end)
                else:
                    cmd2 = """su - {} -c \"dbmcli -U c dbm_configset DBADTL 1\" """.format(self.db_user)
                    rc, output2 = unix_cmd(cmd2)
                    rc, output3 = unix_cmd(cmd)
                    output3 = int(output3.split()[1])
                    if output3 == 1:
                        print("{:<45} ".format("DBADTL"), color.red,"{:<15}".format(output), color.green, "{}".format(output3), color.end)
                    else:
                        print(color.red, "Error changing {} parameter, check manaully.".format("DBADTL"), color.end)
            except:
                print(color.red, "Error changing {} parameter, check manaully.".format("DBADTL"), color.end)
        else:
            return


def main():
    maxdb = Maxdb()
    # if db type is maxdb : else part handled by called function
    if maxdb.check_db_type():
        maxdb.get_passwd()
        print("\nSID        : ", color.green, maxdb.sid, color.end)

        app_mssg_cx = app_mssg_sx = app_mssg_smx = mssg_cu = mssg_cx = mssg_su = mssg_sx = mssg_smu = mssg_smx = str(color.red + "NA" + color.end)
        
        # get control user connectivity status
        temp_cu, mssg_cu = maxdb.check_user_connectivity("control", maxdb.control_pass)
        if temp_cu:
            temp_cx, mssg_cx =  maxdb.check_x_user(maxdb.db_user, "c", "control", maxdb.control_pass)
            app_temp_cx, app_mssg_cx =  maxdb.check_x_user(maxdb.app_user, "c", "control", maxdb.control_pass)
            state = maxdb.get_db_status()
            if state:
                print("DB status  : ", color.green, "ONLINE", color.end)
                maxdb.get_version()
                print("DB version : ", color.green, maxdb.db_version, color.end)
            else:
                print(color.red, "DB is not ONLINE, exiting!", color.end)
                exit(0)
        else:
            print(mssg_cu + color.red + " provided for control user" + color.end)
            exit(0)
        print(color.bold, '\033[4m',"{:<15} {:<20} {:20} {}".format("User name", "User status", "sqdsid key", "sidadm key"), color.end, '\033[0m')
        print("{:<20} {:<30} {:<25} {}".format("control", mssg_cu, mssg_cx, app_mssg_cx))


        temp_schema_usr = False
        # get superdba user connectivity status
        temp_su, mssg_su = maxdb.check_user_connectivity("superdba", maxdb.superdba_pass)
        if temp_su:
            temp_sx, mssg_sx = maxdb.check_x_user(maxdb.db_user, "w", "superdba", maxdb.superdba_pass)
            app_temp_sx, app_mssg_sx = maxdb.check_x_user(maxdb.app_user, "w", "superdba", maxdb.superdba_pass)
            if temp_sx:
                temp_schema_usr = maxdb.get_schema_user()
        print("{:<20} {:<30} {:<25} {}".format("superdba", mssg_su, mssg_sx, app_mssg_sx))


        # get schema user connectivity status
        if temp_schema_usr:
            temp_smu, mssg_smu = maxdb.check_user_connectivity(maxdb.schema_user, maxdb.schema_pass)
            if temp_smu:
                temp_smx, mssg_smx =  maxdb.check_x_user(maxdb.db_user, "DEFAULT", maxdb.schema_user, maxdb.schema_pass)
                app_temp_smx, app_mssg_smx =  maxdb.check_x_user(maxdb.app_user, "DEFAULT", maxdb.schema_user, maxdb.schema_pass)
        print("{:<20} {:<30} {:<25} {}".format(maxdb.schema_user, mssg_smu, mssg_smx, app_mssg_smx))


        maxdb.std_param_values()
        maxdb.check_params()

        # set .cdb enabling file parameter
        maxdb.set_dbadtl_param()


if __name__ == "__main__":
    main()
