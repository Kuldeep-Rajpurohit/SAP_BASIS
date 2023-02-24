#! /usr/bin/env python3.8


#########################################################
###       Author        : Kuldeep Rajpurohit          ###
###       Cuser ID      : C5315737                    ###
###       Last updated  : 7th Nov 2022                ###
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



class color:
    red = '\033[91m'
    green = '\033[92m'
    bold = '\033[1m'
    end = '\033[0m'

print(color.bold,"                     Hana Post Installation Checks                       ", color.end)
print("System Information : ")


def unix_cmd(cmd):
    output = subprocess.check_output(cmd, shell=True)
    return(output.decode())

def check_key_connectivity(user, key):
    try:
        cmd = """su - {} -c \"hdbsql -U {} -j '\\s' \" """.format(user, key)
        output = unix_cmd(cmd)
        # print(output)
        if "host" in output.lower() and "sid" in output.lower() and "dbname" in output.lower() and "user" in output.lower() and "kernel version" in output.lower():
            return True
        else:
            return False
    except:
        print("** ERROR finding keys status.")
        exit(0)


class Hana:
    
    def check_db_type(self):
        try:
            cmd = """cat /etc/fstab | grep -i sapdata1 | awk '{print $2}' """
            output = unix_cmd(cmd).strip()
            self.temp_data = output
            
            # db type is hana
            if 'hdb' in output:
                self.is_hana = True
            # db type is not hana
            else:
                self.is_hana = False
                
        except:
            # not a hana system or not standard fs
            self.is_hana = False
        return(self.is_hana)

    def get_sys_details(self):
        try:
            temp = self.temp_data.split('/')[2].lower()
            self.db_user = temp + 'adm'
            self.inst_no = self.db_user[1:3]
            self.hostname = os.uname()[1].strip()
            self.ghur_pass = None
            cmd = """cat /etc/fstab | grep -i sapmnt | grep -iv sapmnt_db | awk '{print $2}' """
            output = unix_cmd(cmd)
            self.sid = output.split("/")[2].strip()
            self.app_user = self.sid.lower()+"adm"
            self.sys_pass = None
            self.schema_user = None
            print("     1. Instance number          :   {}".format(self.inst_no))
            # print("      DB user                  : {}".format(self.db_user))
            print("     2. SID                      :   {}".format(self.sid))
            # print("      App user                 : {}".format(self.app_user))
            return

        except:
            print(color.red, "Unable to get system details.", color.end)
            exit(0)  

    def get_db_status(self):
        try:
            cmd = """su - {} -c \"sapcontrol -nr {} -function GetProcessList\" 2>/dev/null | grep -i hdb """.format(self.db_user, self.inst_no)
            output = unix_cmd(cmd)
            if "yellow" in output.lower() or "gray" in output.lower():
                self.db_status = False
            else:
                self.db_status = True
            return self.db_status
        except:
            print(color.red, " **ERROR**   :    DB services are not running.", color.end)
            exit(0)

    def get_version(self):
        try:
            cmd = """ su - {} -c \"HDB version\" 2>/dev/null | grep -i version | tail -1 """.format(self.db_user, self.inst_no)
            output = unix_cmd(cmd).split(":")[1].strip()
            self.db_version = output
            print("     1. DB version                                      :   {}".format(self.db_version))
        except:
            print(color.red, "     1. Unable to get DB version.", color.end)

    def create_ghur(self, key_name):
        if self.sys_pass:
            pass
        else:
            self.sys_pass = getpass.getpass(prompt="            System user password               : ")
            
        if key_name == "GHADMIN" and self.sys_pass:
            try:
                self.ghur_pass = getpass.getpass(prompt="            Enter GHUR user password           : ")
                temp = getpass.getpass(prompt="            Enter GHUR user password again     : ")
                
                if self.ghur_pass == temp:
                    cmd = """su - {} -m -s /bin/sh -c \" hdbsql -i {} -u SYSTEM -d SYSTEMDB -p {} -j <<EOF
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
                    GRANT EXECUTE ON 'SYS'.'REPOSITORY_REST' TO GHSYS_ROLE;
                    GRANT EXECUTE ON 'PUBLIC'.'GRANT_ACTIVATED_ROLE' TO GHSYS_ROLE;
                    GRANT EXECUTE ON 'PUBLIC'.'REVOKE_ACTIVATED_ROLE' TO GHSYS_ROLE;
                    GRANT GHBKP_ROLE TO GHADMIN_ROLE;
                    GRANT GHMON_ROLE TO GHADMIN_ROLE;
                    GRANT GHCKP_ROLE TO GHADMIN_ROLE;
                    GRANT GHREP_ROLE TO GHADMIN_ROLE;
                    GRANT GHSYS_ROLE TO GHADMIN_ROLE;
                    GRANT GHUSRADM_ROLE TO GHADMIN_ROLE;
                    GRANT GHADMIN_ROLE TO GHUR;
                    exit
                    EOF\" 2>/dev/null """.format(self.db_user,self.inst_no, self.sys_pass, self.ghur_pass)
                    
                    unix_cmd(cmd)
                    cmd2 = """su - {} -c \"hdbuserstore set GHADMIN {}:3{}13 GHUR {}\" 2>/dev/null""".format(self.db_user, self.hostname, self.inst_no, self.ghur_pass)
                    unix_cmd(cmd2)
                    self.ghadmin = check_key_connectivity(self.db_user, "GHADMIN")
                    if not self.ghadmin:
                        exit(0)
                else:
                    flag = 1
                    exit(0)
                    
            except:
                if flag:
                    print(color.red, "**ERROR** Password did not match. Kindly enter correct password and try again.", color.end)
                else:    
                    print(color.red, "**ERROR** creating ghur user and key in systemdb.", color.end)
                exit(0)
        
        elif key_name == "GHTADMIN" and self.sys_pass:
            if not self.ghur_pass:
                self.ghur_pass = getpass.getpass(prompt="            Enter GHUR user password           : ")
                temp = getpass.getpass(prompt="            Enter GHUR user password again     : ")
                if self.ghur_pass == temp:
                    pass
                else:
                    print(color.red, "**ERROR** Password did not match. Kindly enter correct password and try again.", color.end)
                    exit(0)
                    
            if self.ghur_pass:
                try:
                    cmd = """su - {} -m -s /bin/sh -c \" hdbsql -i {} -u SYSTEM -d {} -p {} -j <<EOF
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
                            GRANT EXECUTE ON 'SYS'.'REPOSITORY_REST' TO GHSYS_ROLE;
                            GRANT EXECUTE ON 'PUBLIC'.'GRANT_ACTIVATED_ROLE' TO GHSYS_ROLE;
                            GRANT EXECUTE ON 'PUBLIC'.'REVOKE_ACTIVATED_ROLE' TO GHSYS_ROLE;
                            
                            GRANT GHBKP_ROLE TO GHADMIN_ROLE;
                            GRANT GHMON_ROLE TO GHADMIN_ROLE;
                            GRANT GHCKP_ROLE TO GHADMIN_ROLE;
                            GRANT GHREP_ROLE TO GHADMIN_ROLE;
                            GRANT GHSYS_ROLE TO GHADMIN_ROLE;
                            GRANT GHUSRADM_ROLE TO GHADMIN_ROLE;
                            
                            GRANT GHADMIN_ROLE TO GHUR;
                            exit
                            EOF\" 2>/dev/null """.format(self.db_user, self.inst_no, self.sid, self.sys_pass, self.ghur_pass)
                    
                    unix_cmd(cmd)
                    cmd2 = """su - {} -c \"hdbuserstore set GHTADMIN {}:3{}15 GHUR {}\" 2>/dev/null""".format(self.db_user, self.hostname, self.inst_no, self.ghur_pass)
                    unix_cmd(cmd2)
                    self.ghtadmin = check_key_connectivity(self.db_user, "GHTADMIN")
                    if not self.ghtadmin:
                        exit(0)
                    
                except:
                    print(color.red, "**ERROR** Creation of GHUR user in TENANT failed. Check manually.", color.end)
                    exit(0)

    def create_bkpmon(self):
        try:
            self.bkpmon_pass = getpass.getpass(prompt="            Enter BKPMON user password         : ")
            temp = getpass.getpass(prompt="            Enter BKPMON user password again   : ")
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
                EOF\" 2>/dev/null """.format(self.db_user, self.connect, self.bkpmon_pass)
                    
                subprocess.run(cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                cmd2 = """su - {} -c \"hdbuserstore set BKPMON {}:3{}13 BKPMON {}\" 2>/dev/null """.format(self.db_user, self.hostname, self.inst_no, self.bkpmon_pass)
                subprocess.run(cmd2, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                self.bkpmon = check_key_connectivity(self.db_user, "BKPMON")
                if not self.bkpmon:
                    exit(0)
            else:
                flag = 1
                exit(0)
        except:
            if flag:
                print(color.red, "Password did not match. Kindly enter correct password and try again.", color.end)
            else:
                print(color.red, "**ERROR** Unable to create BKPMON user and key, kindly check manually.", color.end)
            exit(0)

    def check_keys(self):
        try:
            cmd = """su - {} -c \"hdbuserstore list\" 2>/dev/null | grep -i key | grep -iv file """.format(self.db_user)
            output = unix_cmd(cmd)
    
            if "ghadmin" in output.lower():
                self.ghadmin = check_key_connectivity(self.db_user, "GHADMIN")
                print("     2. GHUR & GHADMIN availability                     : ", color.green, self.ghadmin, color.end)
            else:
                self.ghadmin = False
                self.create_ghur("GHADMIN")
                print("     2. GHUR & GHADMIN created for systemdb             : ", color.green, self.ghadmin, color.end)                
                
            self.connect = 'hdbsql -U GHADMIN'

            if "ghtadmin" in output.lower():
                self.ghtadmin = check_key_connectivity(self.db_user, "GHTADMIN")
                print("        GHUR & GHTADMIN availability                    : ", color.green, self.ghtadmin, color.end)
            else:
                self.ghtadmin = False
                self.create_ghur("GHTADMIN")
                print("        GHUR & GHTADMIN created for tenantdb            : ", color.green, self.ghtadmin, color.end)


            if "bkpmon" in output.lower():
                self.bkpmon = check_key_connectivity(self.db_user, "BKPMON")
                print("     3. BKPMON availability                             : ", color.green, self.bkpmon, color.end)

            else:
                self.bkpmon = False
                self.create_bkpmon()
                print("     3. BKPMON user & key created                       : ", color.green, self.bkpmon, color.end)

        except:
            self.bkpmon = False
            self.ghadmin = False
            self.ghtadmin = False
            print(color.red, "ERROR finding BKPMON, GHADMIN, GHTADMIN keys status.", color.end)
            exit(0)

    def default_key(self):
        users = ["SAPHANADB", "SAP"+self.sid]
        flag = 0
        try:
            cmd = """su - {} -c \"hdbsql -U GHTADMIN -j '\\du' \" 2>/dev/null """.format(self.db_user, users[1])
            output = unix_cmd(cmd)
            for each in users:
                if each in output:
                    self.schema_user = each
                    flag = 1
                    break
                    print(user)
            if flag == 0:
                print("     4. DB-App connectivity (DEFAULT key)               : {} Not found".format(color.red+users+color.end))
        except:
            print(color.red, "    4. **ERROR** finding schema user. Check manually.", color.end)

        if flag:
            try:
                cmd = """su - {} -c \"hdbuserstore list\" 2>/dev/null """.format(self.app_user)
                output = unix_cmd(cmd)
                if "DEFAULT" in output:
                    if self.schema_user.lower() in output.lower():
                        con = check_key_connectivity(self.app_user, "DEFAULT")
                        if con:
                            print("     4. DEFAULT key connection                          : ",color.green, "True", color.end)
                        else:
                            print(color.red,"     4. DEFAULT key connection is not working.",color.end)
                    else:
                        print("      DEFAULT key not created properly.")
                else:
                    print("     4. DEFAULT key not present")
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

    def check_permanent_license(self):
        try:
            cmd = '''su - {} -c " hdbsql -aU GHADMIN -j \\"select permanent from m_license\\""'''.format(self.db_user)
            output = unix_cmd(cmd)
            if "true" in output.lower(): 
                print("     5. Permanent license                               : ", color.green, "Present", color.end)
            elif "false" in output.lower():
                print("     5. Permanent license                               : ", color.red, "Not present. Kindly install", color.end)
        except:
            print("         5. Permanent license                               : ", color.red, "Unable to get permanent license status", color.end)

    def check_fulldb_backup(self):
        try:
            cmd = """su - {} -c \" {} -j 'select TOP 1 ENTRY_TYPE_NAME,SYS_END_TIME from M_BACKUP_CATALOG'\" | grep -i 'complete data backup' """.format(self.db_user, self.connect)
            output = unix_cmd(cmd).strip()
            print("     6. Full DB backup                                  : ", color.green, output, color.end)
        except:
            print("     6. Full DB backup                                  : ", color.bold, "No intial database backup found: Please check", color.end)

    def get_param_values(self):
        if "ccwdf" in self.hostname or "gcl" in self.hostname:
            temp = [
                ['global.ini', 'SYSTEM', 'persistence', 'basepath_logbackup', '/dbarchive'],
                ['global.ini', 'SYSTEM', 'persistence', 'basepath_catalogbackup', '/dbarchive']]
        else:
            temp = [
                ['global.ini', 'SYSTEM', 'persistence', 'basepath_logbackup', '/dbarchive/H{}'.format(self.inst_no)],
                ['global.ini', 'SYSTEM', 'persistence', 'basepath_catalogbackup', '/dbarchive/H{}'.format(self.inst_no)]]

        std_data = "/hdb/" + "H" +str(self.inst_no) + "/sapdata1"
        std_log = "/hdb/" + "H" +str(self.inst_no) + "/saplog1"
        
        temp2 = [
            ['global.ini', 'SYSTEM', 'persistence', 'basepath_datavolumes', std_data],
            ['global.ini', 'SYSTEM', 'persistence', 'basepath_logvolumes', std_log],
            ['nameserver.ini', 'SYSTEM', 'password policy', 'password_lock_time', '0']]
        
        self.std_param = temp + temp2

    def change_param_val(self, p, val):
        try:
            cmd = '''su - {} -c "{} -j \\"ALTER SYSTEM ALTER CONFIGURATION ('{}', '{}') SET ('{}', '{}') = '{}'\\"" 2>/dev/null '''.format(self.db_user, self.connect, p[0], p[1], p[2], p[3], p[4])
            subprocess.run(cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            if val:
                print("            ", p[3] ,color.red, val, color.end, "set to standard  : ", color.green + p[4] + color.end)
            else:
                print("            ", p[3], "set to standard  : ", color.green + p[4] + color.end)
        except:
            print(color.red,"            ERROR failed to set {} parameter, check manually.".format(p[3]) + color.end)
    
    def check_dblevel_params(self):
        print(color.bold,"    9. DB level parameters ", color.end)
        for p in self.std_param:
            cmd = '''su - {} -c "{} -j \\"select key,value from m_inifile_contents where file_name='{}' and layer_name='{}' and section='{}' and key='{}'\\"" 2>/dev/null | grep -i {} | wc -l'''.format(self.db_user, self.connect, p[0], p[1], p[2], p[3], p[3])
            output = unix_cmd(cmd).strip()
            if not (output == '0'):
                cmd = '''su - {} -c "{} -j \\"select key,value from m_inifile_contents where file_name='{}' and layer_name='{}' and section='{}' and key='{}'\\"" 2>/dev/null | grep -i {} '''.format(self.db_user, self.connect, p[0], p[1], p[2], p[3], p[3])
                output = unix_cmd(cmd).strip()
                val = output.split(',')[1].strip('"')
                if val == p[4]:
                    print("            ", p[3], "is standard               : ", color.green + val + color.end)
                else:
                    self.change_param_val(p, val)
            else:
                self.change_param_val(p, None)
                
    def disable_password(self):
        try:
            if self.ghadmin:
                cmd = """su - {} -c \" hdbsql -U GHADMIN -j <<EOF
                alter user bkpmon disable password lifetime;
                exit
                EOF\" 2>/dev/null """.format(self.db_user)
                unix_cmd(cmd)
                
            if self.schema_user:
                cmd = """su - {} -c \" hdbsql -U GHTADMIN -j <<EOF
                alter user {} disable password lifetime;
                exit
                EOF\" 2>/dev/null """.format(self.db_user, self.schema_user)
                unix_cmd(cmd)
            print("     7. Disable password lifetime of technical users    : ", color.green, "Successful", color.end)
        except:
            print(color.red,"     7. **ERROE** Failed to disable password lifetime. Check manually.", color.end)
    
    def lock_system_users(self):
        if self.ghadmin:
            try:
                cmd = """su - {} -c \" hdbsql -U GHADMIN -j <<EOF
                alter user system deactivate user now
                exit
                EOF\" 2>/dev/null """.format(self.db_user)
                
                unix_cmd(cmd)
                print("     8. System user in systemdb                         : ", color.green, "Locked", color.end)
            
            except:
                print(color.red, "     8. **ERROR** Unable to lock system user for systemdb. Check manually", color.end)
        
        if self.ghtadmin:
            try:
                cmd = """su - {} -c \" hdbsql -U GHTADMIN -j <<EOF
                alter user system deactivate user now
                exit
                EOF\" 2>/dev/null """.format(self.db_user)
            
                unix_cmd(cmd)
                print("        System user in tenantdb                         : ", color.green, "Locked", color.end)
            except:
                print(color.red,"        Unable to lock system user for tenantdb. Check manually", color.end)

    
def main():
        
    hana = Hana()
    temp = hana.check_db_type()
    if temp:
        hana.get_sys_details()
        temp = hana.get_db_status()
        if temp:
            print("     3. DB status                : ", color.green, "Up", color.end)
        else:
            print(color.red, " **ERROR**   :    DB services are not running.\n Quiting", color.end)
        print(color.bold, "\nPost installation checks : ", color.end)
        hana.get_version()
        hana.check_keys()
        hana.default_key()
        hana.check_permanent_license()
        hana.check_fulldb_backup()
        hana.disable_password()
        hana.lock_system_users()
        hana.get_param_values()
        hana.check_dblevel_params()
        
    else:
        exit(0)

if __name__ == '__main__':
    main()
