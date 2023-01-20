#!/usr/bin/env python3.8

import subprocess
import os, smtplib
import datetime
from socket import gethostbyaddr, gethostname


def unix_cmd(cmd):
        result = subprocess.check_output(cmd, shell=True)
        return(result.decode())


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
    notification_receivers = ['kuldeep.rajpurohit@sap.com']
    try:
        smtpObj = smtplib.SMTP(smtpServer)
        smtpObj.sendmail(sender, notification_receivers, message)
        print("Email Successfully sent")
    except smtplib.SMTPException:
        print("Error: unable to send email")
        return(2)

    
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

    def check_data_running(self):
        try:
            cmd = "su - sqd%s -c \"x_cons %s show active\"| grep -i chkdata | wc -l"%(self.sid.lower(), self.sid)
            output = int(unix_cmd(cmd).strip("\n"))
            return(output)
        except:
            msg = "Error finding running processes from database."
            print(msg)
            sendMail(msg)
            exit(2)


    def trigger_checkdata(self):
        try:
            cmd = "su - sqd%s -c \"nohup dbmcli -U c db_execute check data &\""%self.sid.lower()
            subprocess.run(cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            if self.check_data_running():
                print("Triggered check data.")
            else:
                msg = "Failed to trigger check data. Kindly trigger manually"
                print(msg)
                sendMail(msg)
        except:
            msg = "Error triggering check data. Check manually."
            print(msg)
            sendMail(msg)
            exit(2)


def main():
    flag = get_flagvalue()
    if flag == '1':
        print("Self healing already in process. Quitting")
        exit(0)
    else:
        maxdb = MaxDB()
        maxdb.get_SID()
        already_running = maxdb.check_data_running()
        
        if not already_running:
            maxdb.trigger_checkdata()
            print("Self healing triggered.")
            update_flagfile('1')
            
        else:
            print("Check data already running.")
            update_flagfile('1')

try: 
    if __name__ == '__main__':
        main()

except:
    msg = "Critical. Error checking the status"
    print(msg)
    sendMail(msg)
    
