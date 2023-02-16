#! /usr/bin/env python3.8


#########################################################
###       Author        : Kuldeep Rajpurohit          ###
###       Cuser ID      : C5315737                    ###
###       Last updated  : 3rd Aug 2022                ###
###       Title         : Hana Post Installation      ###
#########################################################

# Purpose of the script :
"""
The below script performs the Hana post installation checks as per GLDS standard wiki mentioned below :
https://wiki.one.int.sap/wiki/display/ITLABS/SAP+HANA+-+Post+installation+Checks
"""



import os
import sys
import subprocess
import getpass



print("=========================================================================")
print("                     Hana Post Installation Checks                       ")
print("=========================================================================")


print("System Information : ")

# function to run unix command and return output in standard text format
def unix_cmd(cmd):
    output = subprocess.check_output(cmd, shell=True)
    return(output.decode())


# check key connectivity
def check_key_connectivity(user, key):
    
    cmd = """su - {} -c \"hdbsql -U {} -j '\\s' \" """.format(user, key)
    output = unix_cmd(cmd)
    # print(output)
    
    if "host" in output.lower() and "sid" in output.lower() and "dbname" in output.lower() and "user" in output.lower() and "kernel version" in output.lower():
        return True
    else:
        return False
    

class Hana:
    
    def get_instance_no(self):

        try:
            cmd = """cat /etc/fstab | grep -i /sapdata | grep -i hdb | awk '{print $2}' """
            output = unix_cmd(cmd)
            # print(output)
            self.db_user = output.split("/")[2].lower() + "adm"
            self.inst_no = self.db_user[1:3]
            self.hostname = os.uname()[1].strip()
            self.restart_needed = False
            self.ghur_pass = ''
            if "ccwdf" in self.hostname or "gcl" in self.hostname:
                self.cc_or_gcp = True
            else:
                self.cc_or_gcp = False
            print("     1. Instance number          : {}".format(self.inst_no))
            print("     2. DB user                  : {}".format(self.db_user))
            print("     3. hostname                 : {}".format(self.hostname))
            print("     4. CC or GCP                : {}".format(self.cc_or_gcp))
            return
        except:
            print("Unable to get instance number.")
            exit(0)

    
    def get_db_status(self):

        try:
            cmd = """su - {} -c \"sapcontrol -nr {} -function GetProcessList\" 2>/dev/null | grep -i hdb """.format(self.db_user, self.inst_no)
            output = unix_cmd(cmd)
            # print(output)
            if "yellow" in output.lower() or "gray" in output.lower():
                self.db_status = False
                # print("DB services are not running....")
            else:
                self.db_status = True
                # print("     5. DB status                : {}".format(self.db_status))

        except:
            print(" **ERROR**   :    DB services are not running.")
            exit(0)
        
        if self.db_status:
            return self.db_status
        else:
            print(" **ERROR**   :    DB services are not running.")
            exit(0)
        return


    def get_sid(self):

        # try to get SID from fstab
        try:
            cmd = """cat /etc/fstab | grep -i sapmnt | grep -iv sapmnt_db | awk '{print $2}' """
            output = unix_cmd(cmd)
            self.sid = output.split("/")[2].strip()
            # self.sid = 'H10'
            self.app_user = self.sid.lower()+"adm"
            print("     6. SID                      : {}".format(self.sid))
            # print("     7. App user                 : {}".format(self.app_user))

            return

        except:

            # try to get from hdb services
            try:
                cmd = """su - {} -c \"sapcontrol -nr {} -function GetProcessList \" | grep -i index""".format(self.db_user,self.inst_no)
                output = unix_cmd(cmd).split(",")[1].split("-")[1]
                self.sid = output
                print("     6. SID                      : {}".format(self.sid))
                return

            except:
                print("     6. Unable to find SID.")
                exit(0)


    def get_version(self):
        try:

            cmd = """ su - {} -c \"HDB version\" 2>/dev/null | grep -i version | tail -1 """.format(self.db_user, self.inst_no)
            output = unix_cmd(cmd).split(":")[1].strip()

            self.db_version = output
            print("     1. DB version                                     : {}".format(self.db_version))
            return
        except:
            print("     1. Unable to get DB version.")
            exit(0)


    def check_keys(self):
        try:
            cmd = """su - {} -c \"hdbuserstore list\" 2>/dev/null | grep -i key | grep -iv file """.format(self.db_user)
            output = unix_cmd(cmd)
            
            if "bkpmon" in output.lower():
                self.bkpmon = check_key_connectivity(self.db_user, "BKPMON")
                # print("bkpmon :", self.bkpmon)
            else:
                self.bkpmon = False
                
            if "ghadmin" in output.lower():
                self.ghadmin = check_key_connectivity(self.db_user, "GHADMIN")
                # print("ghadmin :", self.ghadmin)
            else:
                self.ghadmin = False
                
            if "ghtadmin" in output.lower():
                self.ghtadmin = check_key_connectivity(self.db_user, "GHTADMIN")
                # print("ghtadmin :", self.ghtadmin)
            else:
                self.ghtadmin = False
                
        except:
            self.bkpmon = False
            self.ghadmin = False
            self.ghtadmin = False
            print("Couldn't find BKPMON, GHADMIN, GHTADMIN keys.")
        
        return


    def get_system_pass(self):
        self.sys_pass = getpass.getpass(prompt="     Syetem user password : ")
        return


    def user_or_key(self):
        try:
            if hana.ghadmin:
                # True for key
                self.connect = """hdbsql -U GHADMIN """
            else:
                # self.sys_pass = getpass.getpass(prompt="Syetem user password : ")

                self.connect = """hdbsql -i {} -u SYSTEM -d SYSTEMDB -p {}""".format(self.inst_no, self.sys_pass)
        except:
            print("Error in finding way to connect.")
        
        return
        

    def check_permanent_license(self):
        
        try:
        
            cmd = """su - {} -c \" {} -j <<EOF
                select permanent from m_license
                exit
                EOF\" 2>/dev/null """.format(self.db_user, self.connect)
                
            output = unix_cmd(cmd)
            
            if "true" in output.lower(): 
                print("     3. Permanent license                              : Present")
            
            elif "false" in output.lower():
                print("     3. Permanent license                              : Not present. Kindly install")
            else:
                print(output)
            
        except:
            print("         3. Permanent license                              : Unabel to get permanent license status.")
            exit(0) 
            
        return


    def check_fulldb_backup(self):

        try:
            cmd = """su - {} -c \" {} -j 'select TOP 1 ENTRY_TYPE_NAME,SYS_END_TIME from M_BACKUP_CATALOG'\" | grep -i 'complete data backup' """.format(self.db_user, self.connect)
            output = unix_cmd(cmd).strip()
            print("     4. Full DB backup                                 : {}".format(output))
            return

        except:
            print("     4. Full DB backup                                 : No intial database backup found: Please check ")
            return


    def set_param_to_std(self, param_name,param_value):
        
        if param_name == "basepath_catalogbackup":
            try:
                cmd = """su - {} -c \"{} -j <<EOF
                ALTER SYSTEM ALTER CONFIGURATION ('global.ini', 'SYSTEM') SET ('persistence', 'basepath_catalogbackup') = '{}'
                exit
                EOF\" 2>/dev/null """.format(self.db_user, self.connect, param_value)
                subprocess.run(cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                self.restart_needed = True

            except:
                print("Unabel to set basepath_catalogbackup parameter, kindly check manually.")
                
        elif param_name == "basepath_logbackup":
        
            try:
                cmd = """su - {} -c \"{} -j <<EOF
                ALTER SYSTEM ALTER CONFIGURATION ('global.ini', 'SYSTEM') SET ('persistence', 'basepath_logbackup') = '{}'
                exit
                EOF\" 2>/dev/null """.format(self.db_user, self.connect, param_value)
                subprocess.run(cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                self.restart_needed = True
            except:
                print("Unabel to set basepath_logbackup parameter, kindly check manually.")
            
        elif param_name == "basepath_datavolumes":
        
            try:
                cmd = """su - {} -c \"{} -j <<EOF
                ALTER SYSTEM ALTER CONFIGURATION ('global.ini', 'SYSTEM') SET ('persistence', 'basepath_datavolumes') = '{}'
                exit
                EOF\" 2>/dev/null """.format(self.db_user, self.connect, param_value)
                subprocess.run(cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                self.restart_needed = True
            except:
                print("Unabel to set basepath_datavolume parameter, kindly check manually.")
        
        elif param_name == "basepath_logvolumes":
        
            try:
                cmd = """su - {} -c \"{} -j <<EOF
                ALTER SYSTEM ALTER CONFIGURATION ('global.ini', 'SYSTEM') SET ('persistence', 'basepath_logvolumes') = '{}'
                exit
                EOF\" 2>/dev/null """.format(self.db_user, self.connect, param_value)
                subprocess.run(cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                self.restart_needed = True
            except:
                print("Unabel to set basepath_logvolumes parameter, kindly check manually.")
        
        elif param_name == "password_lock_time":
            try:
                cmd = """su - {} -c \"{} -j <<EOF
                ALTER SYSTEM ALTER CONFIGURATION ('nameserver.ini', 'SYSTEM') SET ('password policy', 'password_lock_time') = '0' WITH RECONFIGURE
                exit
                EOF \" 2>/dev/null """.format(self.db_user, self.connect)
                subprocess.run(cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                self.restart_needed = True
            except:
                print("Unabel to set password_lock_time parameter, kindly check manually.")
        
        else:
            print("error changing parameter")
            

    def check_dblevel_params(self):
        
        print("     5. DB Parameters : ")
        # Basepath_logbackup     = /dbarchive/<SID> ====> On-Prem Systems only
        # Basepath_logbackup     = /dbarchive       ====> GCP & cc

        try:
            cmd = """su - {} -c \"{} -j <<EOF
            select * from m_inifile_contents where file_name='global.ini' and layer_name='SYSTEM' and section='persistence'
            exit
            EOF\" 2>/dev/null | grep -i 'basepath_logbackup' | wc -l""".format(self.db_user, self.connect)
            
            output = unix_cmd(cmd).strip()
            if '1' == output:
                cmd = """su - {} -c \"{} -j <<EOF
                select * from m_inifile_contents where file_name='global.ini' and layer_name='SYSTEM' and section='persistence'
                exit
                EOF\" 2>/dev/null | grep -i 'basepath_logbackup'""".format(self.db_user, self.connect)

                output = unix_cmd(cmd)
                self.basepath_logbackup = output.split(",")[6].replace('"', '').replace('\n','')

                if self.cc_or_gcp:
                    
                    if '/dbarchive' == self.basepath_logbackup: # == self.basepath_logbackup:
                        print("         a. Basepath_logbackup is standard           : {}".format(self.basepath_logbackup))
                    else:
                        print("         a. Basepath_logbackup is not standard       : {}".format(self.basepath_logbackup))
                        self.set_param_to_std("basepath_logbackup", "/dbarchive")
                        print("            Basepath_logbackup set to standard       : /dbarchive")
                        
                else:
                    temp = '/dbarchive'+"H"+str(self.inst_no)
                    
                    if temp == self.basepath_logbackup:
                        print("         a. Basepath_logbackup is standard           : {}".format(self.basepath_logbackup))
                    else:
                        print("         a. Basepath_logbackup is not standard       : {}".format(self.basepath_logbackup))
                        self.set_param_to_std("basepath_logbackup", "/dbarchive/"+"/H"+self.inst_no)
                        print("            Basepath_logbackup set to standard       : {}".format(temp))
                        
            elif '0' == output:
                if self.cc_or_gcp:
                    print("         a. basepath_logbackup                       : Not set")
                    self.set_param_to_std("basepath_logbackup", "/dbarchive")
                    print("            Basepath_logbackup set to standard       : /dbarchive")
                else:
                    temp = '/dbarchive'+"H"+str(self.inst_no)
                    print("         a. basepath_logbackup                       : Not set")
                    self.set_param_to_std("basepath_logbackup", "/dbarchive/"+"/H"+self.inst_no)
                    print("            Basepath_logbackup set to standard       : {}".format(temp))
                    
            else:
                print("         a. **ERROR** finding Basepath_logbackup: ")

        except:
            print("         a. **ERROR** Unable to get basepath_logbackup. Check manually.")
            
        # Basepath_catalogbackup = /dbarchive       ====> GCP & cc
        # Basepath_catalogbackup = /dbarchive/<SID> ====> On-Prem Systems only
   
        try:
            
            cmd = """su - {} -c \" {} -j <<EOF
            select * from m_inifile_contents where file_name='global.ini' and layer_name='SYSTEM' and section='persistence'
            exit
            EOF\" 2>/dev/null | grep -i 'basepath_catalogbackup' | wc -l""".format(self.db_user, self.connect)
            
            output = unix_cmd(cmd).strip()
            
            if '1' == output:
                cmd = """su - {} -c \" {} -j <<EOF
                select * from m_inifile_contents where file_name='global.ini' and layer_name='SYSTEM' and section='persistence'
                exit
                EOF\" 2>/dev/null | grep -i 'basepath_catalogbackup'""".format(self.db_user, self.connect)
                                                                                        
            
                self.basepath_catalogbackup = unix_cmd(cmd).split(",")[6].replace('"', '').replace('\n','')
            
                if self.cc_or_gcp:
                    if '/dbarchive' == self.basepath_catalogbackup:
                        print("         b. Basepath_catalogbackup is standard       : {}".format(self.basepath_catalogbackup))
                    else:
                        print("         b. Basepath_catalogbackup is not standard   : {}".format(self.basepath_catalogbackup))
                        self.set_param_to_std("basepath_catalogbackup", "/dbarchive")
                        print("            Basepath_catalogbackup set to standard   : /dbarchive")
                
                else:
                    temp = '/dbarchive'+"H"+str(self.inst_no)
                    if temp == self.basepath_logbackup:
                        print("         b. Basepath_catalogbackup is standard       : {}".format(self.basepath_catalogbackup))
                    else:
                        print("         b. Basepath_catalogbackup is not standard   : {}".format(self.basepath_catalogbackup))
                        self.set_param_to_std("basepath_catalogbackup", temp)
                        print("            Basepath_catalogbackup set to standard   : {}".format(temp))
                        # print('Kindly change it to                  : "/dbarchive/H<inst_no>"')
            
            elif '0' == output:
                if self.cc_or_gcp:
                    print("         b. Basepath_catalogbackup                   : Not set")
                    self.set_param_to_std("basepath_catalogbackup", "/dbarchive")
                    print("            Basepath_catalogbackup set to standard   : /dbarchive")
                else:
                    temp = '/dbarchive'+"H"+str(self.inst_no)
                    print("         a. Basepath_catalogbackup                   : Not set")
                    self.set_param_to_std("Basepath_catalogbackup", temp)
                    print("            Basepath_catalogbackup set to standard   : {}".format(temp))
                    
                
        except:
            print("         b. **ERROR** Unable to get basepath_catalogbackup. Check manually.")
 
        try:
            cmd = """su - {} -c \"{} -j <<EOF
            select * from m_inifile_contents where file_name='global.ini' and layer_name='SYSTEM' and section='persistence'
            exit
            EOF\" 2>/dev/null | grep -i 'basepath_datavolumes' | wc -l""".format(self.db_user, self.connect)
            output = unix_cmd(cmd).strip()
            
            if '1' == output:
                cmd = """su - {} -c \"{} -j <<EOF
                select * from m_inifile_contents where file_name='global.ini' and layer_name='SYSTEM' and section='persistence'
                exit
                EOF\" 2>/dev/null | grep -i 'basepath_datavolumes'""".format(self.db_user, self.connect)  
            
                self.basepath_datavolumes = unix_cmd(cmd).split(",")[6].replace('"', '').replace('\n','')
                
                std = "/hdb/" + "H" +str(self.inst_no) + "/sapdata1"
                if self.basepath_datavolumes == std:
                    print("         c. Basepath_datavolumes is standard         : {}".format(self.basepath_datavolumes))
                
                else:
                    print("         c. Basepath_datavolumes is not standard       : {}".format(self.basepath_datavolumes))
                    self.set_param_to_std("basepath_datavolumes", std)
                    print("            basepath_datavolumes set to standard     : {}".format(std))

                    # print("Set basepath_datavolumes to       : {}".format(std))
            elif '0' == output:
                print("         c. Basepath_datavolumes                     : Not set")
                std = "/hdb/" + "H" +str(self.inst_no) + "/sapdata1"
                self.set_param_to_std("basepath_datavolumes", std)
                print("            basepath_datavolumes set to standard     : {}".format(std))

            else:
                print("         c. **ERROR** Unable to get basepath_datavolumes. Check manually.")

                
        except:
            print("         c. **ERROR** Unable to get basepath_datavolumes. Check manually.")


        try:
            cmd = """su - {} -c \"{} -j <<EOF
            select * from m_inifile_contents where file_name='global.ini' and layer_name='SYSTEM' and section='persistence'
            exit
            EOF\" 2>/dev/null | grep -i 'Basepath_logvolumes' | wc -l """.format(self.db_user, self.connect)
            
            output = unix_cmd(cmd).strip()
            if '1' == output:
                cmd = """su - {} -c \"{} -j <<EOF
                select * from m_inifile_contents where file_name='global.ini' and layer_name='SYSTEM' and section='persistence'
                exit
                EOF\" 2>/dev/null | grep -i 'Basepath_logvolumes' """.format(self.db_user, self.connect)
                  
                self.basepath_logvolumes = unix_cmd(cmd).split(",")[6].replace('"', '').replace('\n','')
                
                std = "/hdb/" + "H" +str(self.inst_no) + "/saplog1"
                if self.basepath_logvolumes == std:
                    print("         d. Basepath_logvolumes is standard          : {}".format(self.basepath_logvolumes))
                
                else:
                    print("         d. Basepath_logvolumes is not standard      : {}".format(self.basepath_logvolumes))
                    self.set_param_to_std("basepath_logvolumes", std)
                    print("            basepath_logvolumes set to standard      : {}".format(std))

    
                # print("Set basepath_logvolumes to       : {}".format(std))
            elif '0' == output:
                std = "/hdb/" + "H" +str(self.inst_no) + "/saplog1"
                print("         d. Basepath_logvolumes                      : Not set")
                self.set_param_to_std("basepath_logvolumes", std)
                print("            basepath_logvolumes set to standard      : {}".format(std))
                
            else:
                print("         d. **ERROR** Unable to get basepath_logvolumes. Check manually.")

        except:
            print("         d. **ERROR** Unable to get basepath_logvolumes. Check manually.")
        
        
        # password_lock_time should be 0 for system
        
        try:
            cmd = """su - {} -c \"{} -j <<EOF
            select * from m_inifile_contents where file_name='nameserver.ini' and layer_name='SYSTEM' and section='password policy'
            exit
            EOF\" 2>/dev/null | grep -i 'nameserver.ini' | wc -l""".format(self.db_user, self.connect)
            
            output = unix_cmd(cmd).strip()
            # print(output, type(output), len(output))
        

            if '1' == output:
                
                cmd = """su - {} -c \"{} -j <<EOF
                select * from m_inifile_contents where file_name='nameserver.ini' and layer_name='SYSTEM' and section='password policy'
                exit
                EOF\" 2>/dev/null | grep -i 'nameserver.ini'""".format(self.db_user, self.connect)
            
                output = unix_cmd(cmd).strip()
                
                self.password_lock_time = output.split(",")[6].replace('"', '').replace('\n','')
                if self.password_lock_time == '0':
                    print("         e. Password locktime is standard            : {}".format(self.password_lock_time))
                else:
                    print("         e. Password_lock_time is {}                 : Not standard".format(self.password_lock_time))
                    self.set_param_to_std("password_lock_time", "0")
                    print("            Changed password_lock_time to            : 0")
            
            else:
                self.set_param_to_std("password_lock_time", "0")
                print("         e. Changed password_lock_time to                : 0")
            
        except:
            print("         e. **ERROR** Unabel to get password_lock_time. Check manually")
            
        return(self.restart_needed)


    def create_bkpmon(self):

        if self.bkpmon:
            cmd = """su - {} -c \"{} -j '\du' \" 2>/dev/null | grep -i bkpmon """.format(self.db_user, self.connect)
            output = unix_cmd(cmd)
            
            if "bkpmon" in output.lower():
                print("     6. BKPMON user and key                            : Already Present")
                
        else:
            # create user and key function
            try:

                self.bkpmon_pass = getpass.getpass(prompt="            Enter BKPMON user password               : ")
                temp = getpass.getpass(prompt="            Enter BKPMON user password again             : ")
                if self.bkpmon_pass == temp:
                    
                    cmd = """su - {} -c \"{} -j <<EOF
                    CREATE USER BKPMON PASSWORD {} NO FORCE_FIRST_PASSWORD_CHANGE;
                    GRANT MONITORING TO BKPMON;
                    GRANT CATALOG READ TO BKPMON;
                    GRANT BACKUP ADMIN TO BKPMON;
                    GRANT DATABASE BACKUP ADMIN TO BKPMON;
                    GRANT DATABASE RECOVERY OPERATOR to BKPMON;
                    Alter USER BKPMON DISABLE PASSWORD LIFETIME;
                    exit
                    EOF \" 2>/dev/null """.format(self.db_user, self.connect, self.bkpmon_pass)
                        
                    unix_cmd(cmd)
                    cmd2 = """su - {} -c \"hdbuserstore set BKPMON {}:3{}13 BKPMON {}\" 2>/dev/null """.format(self.db_user, self.hostname, self.inst_no, self.bkpmon_pass)
                    unix_cmd(cmd2)
                    print("         6. BKPMON user and key                      : Created and verified")
                
                else:
                    print("Password did not match. Kindly enter correct password and try again.")
                    exit(0)
            
            except:
                print("**ERROR** Unable to create BKPMON user and key, kindly check manually.")
        
        return
             

    def create_ghur(self):
        
        if self.ghadmin:
            try:
                
                cmd = """su - {} -c \"{} -j '\du' \" 2>/dev/null | grep -i ghur """.format(self.db_user, self.connect)
                output = unix_cmd(cmd)
                
                if "ghur" in output.lower():
                    print("     7.a GHUR user and key in systemdb                 : Already Present")
                
                else:
                    print("     7.a **Error** checking ghur user status in systemdb. Kindly check manually")
                    
            except:
                    print("     7.a **Error** checking ghur user status in systemdb. Kindly check manually")
        
        else:
            try:
                self.ghur_pass = getpass.getpass(prompt="            Enter GHUR user password       : ")
                temp = getpass.getpass(prompt="            Enter GHUR user password again     : ")
                
                if self.ghur_pass == temp:
                
                    cmd = """su - {} -c \"{} -j <<EOF
                    CREATE USER GHUR PASSWORD {} NO FORCE_FIRST_PASSWORD_CHANGE;
                    ALTER USER GHUR DISABLE PASSWORD LIFETIME;
                    CREATE ROLE GHBKP_ROLE;
                    CREATE ROLE GHMON_ROLE;
                    CREATE ROLE GHCKP_ROLE;
                    CREATE ROLE GHREP_ROLE;
                    CREATE ROLE GHSYS_ROLE;
                    CREATE ROLE GHUSRADM_ROLE;
                    CREATE ROLE GHADMIN_ROLE;
                    GRANT BACKUP ADMIN TO GHBKP_ROLE;
                    GRANT CATALOG READ TO GHBKP_ROLE;
                    GRANT MONITORING TO GHBKP_ROLE;
                    GRANT MONITORING TO GHMON_ROLE;
                    GRANT USER ADMIN TO GHUSRADM_ROLE;
                    GRANT INFILE ADMIN TO GHUSRADM_ROLE;
                    GRANT TENANT ADMIN TO GHCKP_ROLE;
                    GRANT MONITORING TO GHCKP_ROLE;
                    GRANT BACKUP ADMIN TO GHCKP_ROLE;
                    GRANT CATALOG READ TO GHCKP_ROLE;
                    GRANT INIFILE ADMIN TO GHCKP_ROLE;
                    GRANT SERVICE ADMIN TO GHCKP_ROLE;
                    GRANT SERVICE ADMIN TO GHCKP_ROLE;
                    GRANT TRACE ADMIN TO GHCKP_ROLE;
                    GRANT RESOURCE ADMIN TO GHCKP_ROLE;
                    GRANT LICENSE ADMIN TO GHCKP_ROLE;
                    GRANT EXECUTE ON SCHEMA _SYS_STATISTICS TO GHCKP_ROLE WITH GRANT OPTION;
                    GRANT SELECT ON SCHEMA _SYS_STATISTICS TO GHCKP_ROLE WITH GRANT OPTION;
                    GRANT DELETE ON SCHEMA _SYS_STATISTICS TO GHCKP_ROLE WITH GRANT OPTION;
                    GRANT UPDATE ON SCHEMA _SYS_STATISTICS TO GHCKP_ROLE WITH GRANT OPTION;
                    GRANT INSERT ON SCHEMA _SYS_STATISTICS TO GHCKP_ROLE WITH GRANT OPTION;
                    GRANT UPDATE ON _SYS_STATISTICS.STATISTICS_SCHEDULE TO GHCKP_ROLE WITH GRANT OPTION;
                    GRANT SELECT ON SYS.FULL_SYSTEM_INFO_DUMPS TO GHCKP_ROLE WITH GRANT OPTION;
                    GRANT EXECUTE ON SYS.MANAGEMENT_CONSOLE_PROC TO GHCKP_ROLE WITH GRANT OPTION;
                    GRANT UPDATE ON _SYS_STATISTICS.STATISTICS_SCHEDULE TO GHCKP_ROLE WITH GRANT OPTION;
                    GRANT EXECUTE ON SYS.MANAGEMENT_CONSOLE_PROC TO GHCKP_ROLE WITH GRANT OPTION;
                    GRANT EXECUTE ON SYS.FULL_SYSTEM_INFO_DUMP_DELETE TO GHCKP_ROLE WITH GRANT OPTION;
                    GRANT EXECUTE ON SYS.FULL_SYSTEM_INFO_DUMP_RETRIEVE TO GHCKP_ROLE WITH GRANT OPTION;
                    GRANT EXECUTE ON SYS.FULL_SYSTEM_INFO_DUMP_CREATE TO GHCKP_ROLE WITH GRANT OPTION;
                    GRANT REPO.EXPORT TO GHREP_ROLE;
                    GRANT REPO.IMPORT TO GHREP_ROLE;
                    GRANT REPO.MAINTAIN_DELIVERY_UNITS TO GHREP_ROLE;
                    GRANT REPO.CONFIGURE TO GHREP_ROLE;
                    GRANT REPO.MODIFY_CHANGE TO GHREP_ROLE;
                    GRANT REPO.MODIFY_OWN_CONTRIBUTION TO GHREP_ROLE;
                    GRANT REPO.MODIFY_FOREIGN_CONTRIBUTION TO GHREP_ROLE;
                    GRANT ADAPTER ADMIN TO GHSYS_ROLE;
                    GRANT AGENT ADMIN TO GHSYS_ROLE;
                    GRANT ALTER CLIENTSIDE ENCRYPTION KEYPAIR TO GHSYS_ROLE;
                    GRANT AUDIT ADMIN TO GHSYS_ROLE;
                    GRANT AUDIT OPERATOR TO GHSYS_ROLE;
                    GRANT AUDIT READ TO GHSYS_ROLE;
                    GRANT SSL ADMIN TO GHSYS_ROLE;
                    GRANT CREATE SCHEMA TO GHSYS_ROLE;
                    GRANT BACKUP ADMIN TO GHSYS_ROLE;
                    GRANT BACKUP OPERATOR TO GHSYS_ROLE WITH ADMIN OPTION;
                    GRANT CATALOG READ TO GHSYS_ROLE;
                    GRANT CERTIFICATE ADMIN TO GHSYS_ROLE;
                    GRANT CREATE REMOTE SOURCE TO GHSYS_ROLE;
                    GRANT CREATE STRUCTURED PRIVILEGE TO GHSYS_ROLE;
                    GRANT CREDENTIAL ADMIN TO GHSYS_ROLE;
                    GRANT DATA ADMIN TO GHSYS_ROLE;
                    GRANT DATABASE ADMIN TO GHSYS_ROLE WITH ADMIN OPTION;
                    GRANT DATABASE AUDIT ADMIN TO GHSYS_ROLE;
                    GRANT DATABASE BACKUP ADMIN TO GHSYS_ROLE;
                    GRANT DATABASE BACKUP OPERATOR TO GHSYS_ROLE;
                    GRANT DATABASE RECOVERY OPERATOR TO GHSYS_ROLE;
                    GRANT DATABASE START TO GHSYS_ROLE;
                    GRANT DATABASE STOP TO GHSYS_ROLE;
                    GRANT EXPORT, IMPORT TO GHSYS_ROLE;
                    GRANT EXTENDED STORAGE ADMIN TO GHSYS_ROLE;
                    GRANT INIFILE ADMIN TO GHSYS_ROLE;
                    GRANT LICENSE ADMIN TO GHSYS_ROLE;
                    GRANT LOG ADMIN TO GHSYS_ROLE;
                    GRANT MONITOR ADMIN TO GHSYS_ROLE;
                    GRANT OPTIMIZER ADMIN TO GHSYS_ROLE;
                    GRANT RESOURCE ADMIN TO GHSYS_ROLE;
                    GRANT ROLE ADMIN TO GHSYS_ROLE;
                    GRANT SAVEPOINT ADMIN TO GHSYS_ROLE;
                    GRANT SCENARIO ADMIN TO GHSYS_ROLE;
                    GRANT SERVICE ADMIN TO GHSYS_ROLE;
                    GRANT SESSION ADMIN TO GHSYS_ROLE;
                    GRANT SSL ADMIN TO GHSYS_ROLE;
                    GRANT STRUCTUREDPRIVILEGE ADMIN TO GHSYS_ROLE;
                    GRANT SYSTEM REPLICATION ADMIN TO GHSYS_ROLE;   
                    GRANT TENANT ADMIN TO GHSYS_ROLE;
                    GRANT TABLE ADMIN TO GHSYS_ROLE;
                    GRANT TRACE ADMIN TO GHSYS_ROLE;
                    GRANT TRUST ADMIN TO GHSYS_ROLE;
                    GRANT USER ADMIN TO GHSYS_ROLE;
                    GRANT VERSION ADMIN TO GHSYS_ROLE;
                    GRANT WORKLOAD ADMIN TO GHSYS_ROLE;
                    GRANT WORKLOAD ANALYZE ADMIN TO GHSYS_ROLE;
                    GRANT WORKLOAD CAPTURE ADMIN TO GHSYS_ROLE;
                    GRANT WORKLOAD REPLAY ADMIN TO GHSYS_ROLE;
                    GRANT EXECUTE ON "SYS"."REPOSITORY_REST" TO GHSYS_ROLE;
                    GRANT EXECUTE ON "PUBLIC"."GRANT_ACTIVATED_ROLE" TO GHSYS_ROLE;
                    GRANT EXECUTE ON "PUBLIC"."REVOKE_ACTIVATED_ROLE" TO GHSYS_ROLE;
                    GRANT GHBKP_ROLE TO GHADMIN_ROLE;
                    GRANT GHMON_ROLE TO GHADMIN_ROLE;
                    GRANT GHCKP_ROLE TO GHADMIN_ROLE;
                    GRANT GHREP_ROLE TO GHADMIN_ROLE;
                    GRANT GHSYS_ROLE TO GHADMIN_ROLE;
                    GRANT GHUSRADM_ROLE TO GHADMIN_ROLE;
                    GRANT GHADMIN_ROLE TO GHUR;
                    exit
                    EOF \" 2>/dev/null """.format(self.db_user, self.connect, self.ghur_pass)
                    
                    unix_cmd(cmd)
                
                    cmd2 = """su - {} -c \"hdbuserstore set GHADMIN {}:3{}13 GHUR {}\" 2>/dev/null""".format(self.db_user, self.hostname, self.inst_no, self.ghur_pass)
                
                    unix_cmd(cmd2)
                
                    self.ghadmin = check_key_connectivity(self.db_user, "GHADMIN")
                    if self.ghadmin:
                        print("     7.a GHUR user and key in SYSTEM db              : Created & verified")
                    else:
                        print("     7.a **ERROR** Creation of GHUR user in systemdb failed. Check manually.")
                                
                else:
                    print("**ERROR** Password did not match. Kindly enter correct password and try again.")
                    exit(0)
            except:
                print("     7.a **ERROR** Creation of GHUR user in systemdb failed. Check manually.")
        
        
        
        if self.ghtadmin:
            try:
                cmd = """su - {} -c \"{} -j '\du' \" 2>/dev/null | grep -i ghur """.format(self.db_user, "hdbsql -U GHTADMIN")
                output = unix_cmd(cmd)
                if "ghur" in output.lower():
                    print("     7.b GHUR user and key in tenant db                : Already Present")
                else:
                    print("     7.b **ERROR** checking ghur user status in tenant db. Kindly check manually")
                    
            except:
                    print("     7.b **ERROR** checking ghur user status in tenant db. Kindly check manually")
        
        else:
            try:
                if not self.ghur_pass:
                    self.ghur_pass = getpass.getpass(prompt="Enter GHUR user password       : ")
                    temp = getpass.getpass(prompt="Enter GHUR user password again     : ")
                else:
                    if self.ghur_pass == temp:
                        self.get_system_pass()
                        cmd = """su - {} -c \"hdbsql -i {} -u SYSTEM -d {} -p {} -j <<EOF
                            CREATE USER GHUR PASSWORD {} NO FORCE_FIRST_PASSWORD_CHANGE;
                            ALTER USER GHUR DISABLE PASSWORD LIFETIME;
                            
                            CREATE ROLE GHBKP_ROLE;
                            CREATE ROLE GHMON_ROLE;
                            CREATE ROLE GHCKP_ROLE;
                            CREATE ROLE GHREP_ROLE;
                            CREATE ROLE GHSYS_ROLE;
                            CREATE ROLE GHUSRADM_ROLE;
                            CREATE ROLE GHADMIN_ROLE;
                            
                            GRANT BACKUP ADMIN TO GHBKP_ROLE;
                            GRANT CATALOG READ TO GHBKP_ROLE;
                            GRANT MONITORING TO GHBKP_ROLE;
                            GRANT MONITORING TO GHMON_ROLE;
                            GRANT USER ADMIN TO GHUSRADM_ROLE;
                            GRANT INIFILE ADMIN TO GHUSRADM_ROLE;
                            
                            GRANT TENANT ADMIN TO GHCKP_ROLE;
                            GRANT MONITORING TO GHCKP_ROLE;
                            GRANT BACKUP ADMIN TO GHCKP_ROLE;
                            GRANT CATALOG READ TO GHCKP_ROLE;
                            GRANT INIFILE ADMIN TO GHCKP_ROLE;
                            GRANT SERVICE ADMIN TO GHCKP_ROLE;
                            GRANT TRACE ADMIN TO GHCKP_ROLE;
                            GRANT RESOURCE ADMIN TO GHCKP_ROLE;
                            GRANT LICENSE ADMIN TO GHCKP_ROLE;
                            
                            GRANT EXECUTE ON SCHEMA _SYS_STATISTICS TO GHCKP_ROLE WITH GRANT OPTION;
                            GRANT SELECT ON SCHEMA _SYS_STATISTICS TO GHCKP_ROLE WITH GRANT OPTION;
                            GRANT DELETE ON SCHEMA _SYS_STATISTICS TO GHCKP_ROLE WITH GRANT OPTION;
                            GRANT UPDATE ON SCHEMA _SYS_STATISTICS TO GHCKP_ROLE WITH GRANT OPTION;
                            GRANT INSERT ON SCHEMA _SYS_STATISTICS TO GHCKP_ROLE WITH GRANT OPTION;
                            GRANT UPDATE ON _SYS_STATISTICS.STATISTICS_SCHEDULE TO GHCKP_ROLE WITH GRANT OPTION;
                            GRANT SELECT ON SYS.FULL_SYSTEM_INFO_DUMPS TO GHCKP_ROLE WITH GRANT OPTION;
                            GRANT EXECUTE ON SYS.MANAGEMENT_CONSOLE_PROC TO GHCKP_ROLE WITH GRANT OPTION;
                            GRANT UPDATE ON _SYS_STATISTICS.STATISTICS_SCHEDULE TO GHCKP_ROLE WITH GRANT OPTION;
                            GRANT EXECUTE ON SYS.MANAGEMENT_CONSOLE_PROC TO GHCKP_ROLE WITH GRANT OPTION;
                            GRANT EXECUTE ON SYS.FULL_SYSTEM_INFO_DUMP_DELETE TO GHCKP_ROLE WITH GRANT OPTION;
                            GRANT EXECUTE ON SYS.FULL_SYSTEM_INFO_DUMP_RETRIEVE TO GHCKP_ROLE WITH GRANT OPTION;
                            GRANT EXECUTE ON SYS.FULL_SYSTEM_INFO_DUMP_CREATE TO GHCKP_ROLE WITH GRANT OPTION;
                            
                            GRANT REPO.EXPORT TO GHREP_ROLE;
                            GRANT REPO.IMPORT TO GHREP_ROLE;
                            GRANT REPO.MAINTAIN_DELIVERY_UNITS TO GHREP_ROLE;
                            GRANT REPO.CONFIGURE TO GHREP_ROLE;
                            GRANT REPO.MODIFY_CHANGE TO GHREP_ROLE;
                            GRANT REPO.MODIFY_OWN_CONTRIBUTION TO GHREP_ROLE;
                            GRANT REPO.MODIFY_FOREIGN_CONTRIBUTION TO GHREP_ROLE;
                            
                            GRANT ADAPTER ADMIN TO GHSYS_ROLE;
                            GRANT AGENT ADMIN TO GHSYS_ROLE;
                            GRANT ALTER CLIENTSIDE ENCRYPTION KEYPAIR TO GHSYS_ROLE;
                            GRANT AUDIT ADMIN TO GHSYS_ROLE;
                            GRANT AUDIT OPERATOR TO GHSYS_ROLE;
                            GRANT AUDIT READ TO GHSYS_ROLE;
                            GRANT SSL ADMIN TO GHSYS_ROLE;
                            GRANT CREATE SCHEMA TO GHSYS_ROLE;
                            GRANT BACKUP ADMIN TO GHSYS_ROLE;
                            GRANT BACKUP OPERATOR TO GHSYS_ROLE WITH ADMIN OPTION;
                            GRANT CATALOG READ TO GHSYS_ROLE;
                            GRANT CERTIFICATE ADMIN TO GHSYS_ROLE;
                            GRANT CREATE REMOTE SOURCE TO GHSYS_ROLE;
                            GRANT CREATE STRUCTURED PRIVILEGE TO GHSYS_ROLE;
                            GRANT CREDENTIAL ADMIN TO GHSYS_ROLE;
                            GRANT EXPORT, IMPORT TO GHSYS_ROLE;
                            GRANT EXTENDED STORAGE ADMIN TO GHSYS_ROLE;
                            GRANT INIFILE ADMIN TO GHSYS_ROLE;
                            GRANT LICENSE ADMIN TO GHSYS_ROLE;
                            GRANT LOG ADMIN TO GHSYS_ROLE;
                            GRANT MONITOR ADMIN TO GHSYS_ROLE;
                            GRANT OPTIMIZER ADMIN TO GHSYS_ROLE;
                            GRANT RESOURCE ADMIN TO GHSYS_ROLE;
                            GRANT ROLE ADMIN TO GHSYS_ROLE;
                            GRANT SAVEPOINT ADMIN TO GHSYS_ROLE;
                            GRANT SCENARIO ADMIN TO GHSYS_ROLE;
                            GRANT SERVICE ADMIN TO GHSYS_ROLE;
                            GRANT SESSION ADMIN TO GHSYS_ROLE;
                            GRANT SSL ADMIN TO GHSYS_ROLE;
                            GRANT STRUCTUREDPRIVILEGE ADMIN TO GHSYS_ROLE;
                            GRANT SYSTEM REPLICATION ADMIN TO GHSYS_ROLE;   
                            GRANT TENANT ADMIN TO GHSYS_ROLE;
                            GRANT TABLE ADMIN TO GHSYS_ROLE;
                            GRANT TRACE ADMIN TO GHSYS_ROLE;
                            GRANT TRUST ADMIN TO GHSYS_ROLE;
                            GRANT USER ADMIN TO GHSYS_ROLE;
                            GRANT VERSION ADMIN TO GHSYS_ROLE;
                            GRANT WORKLOAD ADMIN TO GHSYS_ROLE;
                            GRANT WORKLOAD ANALYZE ADMIN TO GHSYS_ROLE;
                            GRANT WORKLOAD CAPTURE ADMIN TO GHSYS_ROLE;
                            GRANT WORKLOAD REPLAY ADMIN TO GHSYS_ROLE;
                            GRANT EXECUTE ON "SYS"."REPOSITORY_REST" TO GHSYS_ROLE;
                            GRANT EXECUTE ON "PUBLIC"."GRANT_ACTIVATED_ROLE" TO GHSYS_ROLE;
                            GRANT EXECUTE ON "PUBLIC"."REVOKE_ACTIVATED_ROLE" TO GHSYS_ROLE;
                            
                            GRANT GHBKP_ROLE TO GHADMIN_ROLE;
                            GRANT GHMON_ROLE TO GHADMIN_ROLE;
                            GRANT GHCKP_ROLE TO GHADMIN_ROLE;
                            GRANT GHREP_ROLE TO GHADMIN_ROLE;
                            GRANT GHSYS_ROLE TO GHADMIN_ROLE;
                            GRANT GHUSRADM_ROLE TO GHADMIN_ROLE;
                            
                            GRANT GHADMIN_ROLE TO GHUR;
                            exit
                            EOF \" 2>/dev/null """.format(self.db_user, self.inst_no, self.sid, self.sys_pass, self.ghur_pass)
                        
                        unix_cmd(cmd)
                        cmd2 = """su - {} -c \"hdbuserstore set GHTADMIN {}:3{}15 GHUR {}\" 2>/dev/null """.format(self.db_user, self.hostname, self.inst_no, self.ghur_pass)
                        unix_cmd(cmd2)
                        self.ghtadmin = check_key_connectivity(self.db_user, "GHTADMIN")
                    
                        if self.ghtadmin:
                            print("     7.b GHUR user and key for Tenant db               : Created & Verified")
                        else:
                            print("     7.b **ERROR** Creation of GHUR user in tenant db failed. Check manually.")
                            
                    else:
                        print("**ERROR** Password did not match. Kindly enter correct password and try again.")
                        exit(0)
                    
                    
            except:
                print("     7.b **ERROR** checking ghur user status in tenant db. Kindly check manually")

            return


    def disable_password(self):
        try:
            if self.ghadmin:
                cmd = """su - {} -c \" hdbsql -U GHADMIN -j <<EOF
                alter user bkpmon disable password lifetime;
                exit
                EOF\" 2>/dev/null """.format(self.db_user)
            
                unix_cmd(cmd)
                print("     8. Disable password lifetime of technical users   : Successful")
        except:
            print("     8. **ERROE** Failed to disable password lifetime. Check manually.")
        return
        
            
    def lock_system_users(self):
        if self.ghadmin:
            try:
                cmd = """su - {} -c \" hdbsql -U GHADMIN -j <<EOF
                alter user system deactivate user now
                exit
                EOF\" 2>/dev/null """.format(self.db_user)
                
                unix_cmd(cmd)
                print("     9.a System user in systemdb                       : Locked")
            
            except:
                print("     9.a **ERROR** Unable to lock system user for systemdb. Check manually")
        
        if self.ghtadmin:
            try:
                cmd = """su - {} -c \" hdbsql -U GHTADMIN -j <<EOF
                alter user system deactivate user now
                exit
                EOF\" 2>/dev/null """.format(self.db_user)
            
                unix_cmd(cmd)
                print("     9.b System user in tenantdb                       : Locked")
            except:
                print("     9.b Unable to lock system user for systemdb. Check manually")
        
        return
        
    
    def default_key(self):
        
        user = "SAP" + self.sid
        users = ["SAPHANADB", user]
        
        flag = 0
        
        try:
            cmd = """su - {} -c \"hdbsql -U GHTADMIN -j '\\du' \" 2>/dev/null """.format(self.db_user, user)
            output = unix_cmd(cmd)
            for each in users:
                if each in output:
                    self.schema_user = each
                    flag = 1
                    break
                    # print(user)
            if flag == 0:
                print("     10. DB-App connectivity (DEFAULT key)             : {} Not found".format(users))

        except:
            print("     10. **ERROR** finding schema user. Check manually.")
        
        if flag:
            try:
                cmd = """su - {} -c \"hdbuserstore list\" 2>/dev/null """.format(self.app_user)
                output = unix_cmd(cmd)
                if "DEFAULT" in output:
                    # print("DEFAULT")
                    if self.schema_user.lower() in output.lower():
                        
                        print("     10. Schema user & DEFAULT key                     : {}".format(self.schema_user))
                        
                        con = check_key_connectivity(self.app_user, "DEFAULT")
                        if con:
                            print("      Connection using default key is working fine")
                        else:
                            print("      DEFAULT key connection is not working.")
                    else:
                        print("      DEFAULT key not created properly.")

                else:
                    print("     10. DEFAULT key not present")
                    
                    try:
                        self.schema_pass = getpass.getpass(prompt="Enter SCHEMA user password       : ")
                        temp = getpass.getpass(prompt="Enter SCHEMA user password again     : ")
                        
                        if self.schema_pass == temp:
                            
                            cmd = """su - {} -c \"hdbuserstore set DEFAULT {}:3{}15 {} {}\" 2>/dev/null """.format(self.app_user, self.hostname, self.inst_no, self.schema_user, self.schema_pass)
                            unix_cmd(cmd)
                            temp2 = check_key_connectivity("DEFAULT")
                            if temp2:
                                print("       Default key created successfully.")
                            else:
                                print("       Default key created, connection not working, check manually.")
                        else:
                            print("       Password mismatch, enter correct password and try again.")
                            exit(0)
                    except:
                        print("       Error creating DEFAULT key.")
                    
            except:
                print("       DEFAULT key not present.")
        else:
            pass
        
        
        return

hana = Hana()
hana.get_instance_no()


# step 2  get status of DB
status =  hana.get_db_status()

hana.get_sid()

print("\nPost installation checks : ")

# step 1  Display DB version
hana.get_version()

#step 2 db status output
if status:
    print("     2. DB Status                                      : Up")


# check keys
hana.check_keys()

hana.user_or_key()

hana.get_system_pass()
hana.check_permanent_license()

hana.check_fulldb_backup()

restart = hana.check_dblevel_params()

hana.create_bkpmon()

hana.create_ghur()

hana.disable_password()

hana.lock_system_users()

hana.default_key()

print("     11. Verify the SISM entry for database configuration.\n")

if restart:
    print("*****NOTE : DB parameters are modified hence take a DB restart to reflect the changes.*****")
