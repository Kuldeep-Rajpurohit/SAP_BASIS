#!/usr/bin/env python3.8

import subprocess
import os
import datetime

#############################################################
###       Author            : Kuldeep (C5315737)
###       Ver               : 2.0
###       Last Updated      : 17th Aug 2022
###       Purpose           : MaxDB data consistency check and healing script.
#############################################################


def unix_cmd(cmd):
        result = subprocess.check_output(cmd, shell=True)
        return(result.decode())


def check_db_type():
        cmd = "cat /etc/fstab | grep -i sapdata1 | awk '{print $2}'"
        result = unix_cmd(cmd)
        return("sapdb" in result)

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
        exit(0)

class MaxDB:

    def get_SID(self):
        cmd = "cat /etc/fstab | grep -i sapdata1 | awk '{print $2}'"
        result = unix_cmd(cmd)
        self.sid = result.split("/")[2]
        return


    def get_rundirpath(self):
        try:
            cmd = "su - sqd%s -c \"dbmcli -U c param_directget RunDirectoryPath\" | grep -i RunDirectoryPath | awk '{print $2}'"%self.sid.lower()
            self.rundirpath = unix_cmd(cmd).strip("\n")
            return
        except:
            print("Error finding RunDirectory path.")
            exit(0)


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
            exit(0)

    def check_data_running(self):
        try:
            cmd = "su - sqd%s -c \"x_cons %s show active\"| grep -i chkdata | wc -l"%(self.sid.lower(), self.sid)
            output = int(unix_cmd(cmd).strip("\n"))
            return(output)
        except:
            print("Error finding running processes from database.")
            exit(0)


    def trigger_checkdata(self):
        try:
            cmd = "su - sqd%s -c \"nohup dbmcli -U c db_execute check data &\""%self.sid.lower()
            subprocess.run(cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            if self.check_data_running:
                print("Triggered check data.")

            else:
                print("Failed to trigger check data. Kindly trigger manually")
        except:
            print("Error triggering check data. Check manually.")
            exit(0)


    def check_status(self, data):
        try:
            data = data.split("\n")
            for each in data:
                if "failure" in each.lower():
                    print("Latest check data failed.")
                    return False
            return True
        except:
            print("Error finding check data status. Check manually.")
            exit(0)


isMaxdb = check_db_type()

if isMaxdb:
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
                print("Check data seems to be hung, Kindly check manually.")
            else:
                # print("Time in hours : {}".format(hours))
                print("Check data is running.")

        else:
            print("Check .cdb files not being created in /dbahist path, check manually.")

    else:
        # check data is not running check the status of last check data file 
        if exists:
            # check if it is successfull
            successfull = maxdb.check_status(exists)
            if successfull:
                days = check_age(exists, 0)
                if days < 45:
                    print("Check data is {} days old. Hence no actions taken.\n".format(days))
                else:
                    print("Check data is {} days old".format(days))
                    maxdb.trigger_checkdata()
            else:
                print("Last check data failed.")
                maxdb.trigger_checkdata()

        else:
            print("Check data has not ran before on this system before.")
            maxdb.trigger_checkdata()

else:
    print("Not a Maxdb system")
    exit(0)


exit(0)
