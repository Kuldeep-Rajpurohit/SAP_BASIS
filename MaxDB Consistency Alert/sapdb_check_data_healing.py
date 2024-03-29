#!/usr/bin/env python3.8


#########################################################
###       Author        : Kuldeep Rajpurohit          ###
###       Cuser ID      : C5315737                    ###
###       Last updated  : 16th Jan 2023               ###
###       Title         : Maxdb Consistency healing   ###
#########################################################

# Purpose of the script :
"""
Trigger maxdb consistency check for a maxdb system if an event is triggered by a maxdb check script from nagios check script.
Send an alert failure mail if script fails
"""


import subprocess
import os, smtplib
import datetime, time
from socket import gethostbyaddr, gethostname


def unix_cmd(cmd):
    temp = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    output, err = temp.communicate()
    return_code = temp.returncode
    return(output.decode())


def check_db_type():
    cmd = "cat /etc/fstab | grep -i sapdata1 | awk '{print $2}'"
    result = unix_cmd(cmd)
    return("sapdb" in result)


def sendMail(msg):
    smtpServer = 'localhost'
    hostname = gethostbyaddr(gethostname())[0]
    sender = 'root@{}'.format(hostname)
    text = """Hi Team,\n\n{}\n\nRegards,\nStackStorm Team""".format(msg)
    subject = 'ST2 Alert : StackStorm Self Healing Report of Hana Db Backup Catalog on {}'.format(hostname)
    message = 'Subject: {}\n\n{}'.format(subject, text)
    notification_receivers = ['DL_5F97A8BB7883FF027EE82632@global.corp.sap','kuldeep.rajpurohit@sap.com']
    try:
        smtpObj = smtplib.SMTP(smtpServer)
        smtpObj.sendmail(sender, notification_receivers, message)
        # print("Email Successfully sent")
    except smtplib.SMTPException:
        print("Error: unable to send email")
        exit(2)

    
def update_flagfile(val):
    file_name = "/var/log/nagios/heal_db_chkdata_flagfile"
    with open(file_name, 'w') as ffile:
        ffile.write(val)
    return


def get_flagvalue():
    file_name = "/var/log/nagios/heal_db_chkdata_flagfile"
    with open(file_name, 'r') as ffile:
        flagValue = ffile.read()
        return flagValue


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
            return(0)
        except:
            print("Warning : Error finding RunDirectory path.")
            return(1)


    def check_data_running(self):
        # print("x_cons check")
        try:
            cmd = """su - sqd{} -c \"x_cons {} show active\" | grep -i chkdata | wc -l """.format(self.sid.lower(), self.sid)
            output = int(unix_cmd(cmd).strip("\n"))
            return(0, output)
        except:
            msg = "Error finding running processes from database."
            # print(msg)
            sendMail(msg)
            return(2)


    def check_file_generation(self):
        # print("file generation check")
        self.get_rundirpath()
        os.chdir(self.rundirpath+"/dbahist")
        cmd = "ls -altr | grep -i .cdb | tail -3 | wc -l"
        exists = int(unix_cmd(cmd).strip("\n"))
        if exists:
            cmd = "ls -altr | grep -i .cdb | tail -1 | awk '{print $9}'"
            file_name = unix_cmd(cmd)[3:-5]
            # print(file_name)
            file_time = datetime.datetime(int(file_name[:4]), int(file_name[4:6]), int(file_name[6:8]), int(file_name[8:10]), int(file_name[10:12]), int(file_name[12:14]))
            # print(file_time)
            # print("answer of generation", (file_time > self.start_time))
            return(file_time > self.start_time)
        else:
            # print("return false for file generation")
            return False


    def trigger_checkdata(self):
        try:
            cmd = """su - sqd{} -c 'dbmcli -U c db_execute check data &' """.format(self.sid.lower())
            subprocess.Popen(cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
        except:
            # print("In except block of trigger.")
            pass        
        # check if .cdb file is generated
        temp = self.check_file_generation()
        if temp:
            # print("Self healing triggered (file generated)")
            return(True)
        
        # check process list
        temp = self.check_data_running()[1]
        if temp > 0:
            # print("Triggered check data (process list))")
            return(True)
        return(False)

        
exit_code = 0

def main():
    if check_db_type():
        start_time = datetime.datetime.now()
        time.sleep(1)
        flag = get_flagvalue()
        if flag == '1':
            print("Self healing already in process. Quitting")
            return(0)
        else:
            maxdb = MaxDB()
            maxdb.get_SID()
            maxdb.start_time = start_time
            exit_code, already_running = maxdb.check_data_running()
            if exit_code == 0:
                if not already_running:
                    if maxdb.trigger_checkdata():
                        print("Self healing triggered.")
                        update_flagfile('1')
                    else:
                        print("Failed to trigger check data. Kindly trigger manually")
                        sendMail("Failed to trigger check data. Kindly trigger manually")
                        update_flagfile('1')               
                else:
                    print("Check data already running.")
                    update_flagfile('1')
            else:
                return(exit_code)

    else:
        print("OK. Not a MaxDB system")
        return(0)

try: 
    if __name__ == '__main__':
        exit_code = main()

except:
    msg = "Critical. Error checking the status"
    print(msg)
    sendMail(msg)
    exit_code = 2

exit(exit_code)
