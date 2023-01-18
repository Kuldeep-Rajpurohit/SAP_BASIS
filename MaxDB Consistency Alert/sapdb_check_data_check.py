#!/usr/bin/env python3.8

import subprocess
import os
import datetime


def unix_cmd(cmd):
    result = subprocess.check_output(cmd, shell=True)
    return(result.decode())


def check_db_type():
    cmd = "cat /etc/fstab | grep -i sapdata1 | awk '{print $2}'"
    result = unix_cmd(cmd)
    return("sapdb" in result)

def flag_file():
    try:
        file_name = "/var/log/nagios/heal_db_chkdata_flagfile"
        file_path = "/var/log/nagios"
        exists = os.path.exists(file_path)
        
        if not exists:
            # print("doesn't exist")
            os.mkdir(file_path)
            with open(file_name, 'w') as ffile:
                ffile.write('0')
                return('0')
        
        
        else:
            # print("exists")
            if os.path.exists(file_name):
                with open(file_name, 'r') as ffile:
                    flagValue = ffile.read()
                    return flagValue
            else:
                with open(file_name, 'w') as ffile:
                    ffile.write('0')
                    return('0')
                

    except:
        print("Critical. Error checking flagfile status.")
        exit(2)
        
    return
    
    

def update_flagfile(val):
    file_name = "/var/log/nagios/heal_db_chkdata_flagfile"
    with open(file_name, 'w') as ffile:
        ffile.write(val)
    return


def check_age(data, flag):
    try:
        data = data.split("\n")

        for each in data:
            if "Timestamp" in each:
                stamp = each
                break
        
        last_date = str(stamp.split()[1])
        last_day = datetime.date(int(last_date[:4]), int(last_date[4:6]), int(last_date[6:8]))
        present_day = datetime.date.today()
        diff = present_day - last_day
        
        if flag == 0:
            return(diff.days)
            
        elif flag == 1:
            time_in_secs = diff.total_seconds()
            time_in_hours = int(divmod(time_in_secs, 3600)[0])
            return(time_in_hours)
    except:
        print("Error finding check data process details.")
        exit(1)


class MaxDB:

    def get_SID(self):
        cmd = "cat /etc/fstab | grep -i sapdata1 | awk '{print $2}'"
        result = unix_cmd(cmd)
        self.sid = result.split("/")[2]
        return
    
    
    def get_rundirpath(self):
        try:
            cmd = "su - sqd%s -c \"dbmcli -U c -nohold param_directget RunDirectoryPath\" | grep -i RunDirectoryPath | awk '{print $2}'"%self.sid.lower()
            self.rundirpath = unix_cmd(cmd).strip("\n")
            return
        except:
            print("Error finding RunDirectory path.")
            exit(1)
    
    
    def cdb_exists(self):
        try:
            os.chdir(self.rundirpath+"/dbahist")
            cmd = "ls -altr | grep -i .cdb | tail -3 | wc -l"
            exists = int(unix_cmd(cmd).strip("\n"))
            if exists:
                cmd = "cat `ls -altr | grep -i .cdb | tail -1 | awk '{print $9}'`"
                file_content = unix_cmd(cmd).strip("\n")
                return(file_content)
            else:
                return(0)
        except:
            print("Error finding check data (.cdb) files.")
            exit(1)
            
    def check_data_running(self):
        try:
            cmd = "su - sqd%s -c \"x_cons %s show active\"| grep -i chkdata | wc -l"%(self.sid.lower(), self.sid)
            output = int(unix_cmd(cmd).strip("\n"))
            return(output)
        except:
            print("Error finding running processes from database.")
            exit(1)


    def check_status(self, data):
        try:
            data = data.split("\n")
            for each in data:
                if "failure" in each.lower():
                    # print("Latest check data failed.")
                    return False
            return True
        except:
            print("Error finding check data status. Check manually.")
            exit(1)


def main():

    isMaxdb = check_db_type()
    
    if isMaxdb:
        
        flag = flag_file()

        maxdb = MaxDB()
        maxdb.get_SID()
        maxdb.get_rundirpath()
        exists = maxdb.cdb_exists()
        running = maxdb.check_data_running()
        
        if running:
            # check data is already running check its age
            if exists:
                hours = check_age(exists, 1)
                if hours > 48:
                    # print("Time in hours : {}".format(hours))
                    print("Warning. Check data seems to be hung, Kindly check manually.")
                    exit(1)
    
                else:
                    # print("Time in hours : {}".format(hours))
                    print("OK. Check data is running.")
                    # update_flagfile('0')
                    exit(0)
            
            else:
                print("Warning. Check .cdb files not being created in /dbahist path, check manually.")
                exit(1)
        
        else:
            # check data is not running check the status of last check data file 
            if exists:
                # check if it is successfull
                successfull = maxdb.check_status(exists)
                if successfull:
                    days = check_age(exists, 0)
                    if days < 45:
                        print("OK. Check data is {} days old. Hence no actions taken.\n".format(days))
                        update_flagfile('0')
                        exit(0)
                    else:
                        print("Critical. Check data is {} days old".format(days))
                        # update_flagfile('1')
                        # maxdb.trigger_checkdata()
                        exit(2)
    
                else:
                    print("Critical. Last check data failed.")
                    # maxdb.trigger_checkdata()
                    # update_flagfile('1')
                    exit(2)
    
            else:
                print("Critical. Check data has not ran before on this system before.")
                # maxdb.trigger_checkdata()
                # update_flagfile('1')
                exit(2)

    
    else:
        print("Not a Maxdb system")
        exit(0)
    


if __name__ == '__main__':
    main()
