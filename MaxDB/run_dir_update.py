#!/usr/bin/env python3.8
import subprocess
import os


def unix_cmd(cmd):
        output = subprocess.check_output(cmd, shell=True)
        return(output.decode())


class system:

        def get_SID(self):
                cmd = "cat /etc/fstab | grep -i sapdata1 | awk '{print $2}'"
                result = unix_cmd(cmd)
                if "sapdb" in result:
                        self.db_type = "MaxDB"
                        self.sid = result.split("/")[2]
                        print("DB type \t\t\t\t: {0}\nSID \t\t\t\t\t: {1}".format(self.db_type, self.sid))
                        return(self.sid)

                else:
                        print(result)
                        print("DB type is not MaxDB")
                        exit(0)

        def stop_db(self):
                cmd = "su - sqd%s -c \"dbmcli -U c db_offline\""%self.sid.lower()
                
                try:
                        output = unix_cmd(cmd)
                        cmd1 = "su - sqd%s -c \"dbmcli -U c db_state -v\""%self.sid.lower()
                        output = unix_cmd(cmd1)
                        if "OFFLINE" in output:
                                print("\nDB stopped.")
                except:
                        print("Unable to stop DB.")
                        exit(0)



        def start_db(self):
                cmd = "su - sqd%s -c \"dbmcli -U c db_online\""%self.sid.lower()
                
                try:
                        output = unix_cmd(cmd)
                        cmd1 = "su - sqd%s -c \"dbmcli -U c db_state -v\""%self.sid.lower()
                        output = unix_cmd(cmd1)                        
                        if "ONLINE" in output:
                                print("DB started.")
                except:
                        print("Unable to start DB.\nERROR:\n")
                        print(output)

                        exit(0)



        def get_run_dir_path(self):
                cmd = "su - sqd%s -c \"dbmcli -U c param_directget RunDirectory\"| grep -i rundirectory | awk '{print $2}'"%self.sid.lower()
                self.run_dir_path = unix_cmd(cmd).strip("\n")
                print("Run Directory Path  \t\t\t: {0}".format(self.run_dir_path))
                return(self.run_dir_path)




        def check_path_standard(self, std_path):
                # standard_path = "/sapdb/"+self.sid+"/data/wrk/"+self.sid
                self.standard_path = std_path
                if std_path == self.run_dir_path:
                        print("Present path is standard \t\t: {0}".format("YES"))
                        print("No actions needed\n")
                        exit(0)
                else:
                        print("Present RunDirectory path is standard \t\t\t\t: {0}".format("NO"))


        def compare_size(self):
                os.chdir(self.run_dir_path)
                os.chdir("..")

                size1 = unix_cmd("du -sh %s | awk '{print $1}'"%self.sid).strip("\n")
                size1 = size1[:-1]
                size1 = float(size1)
                print("Space consumed by current path in MB \t\t: {0}".format(size1))
                
                size2 = unix_cmd("df -lm %s | tail -1 | awk '{print $4}'"%self.standard_path).strip("\n")
                size2 = float(size2)
                print("Space available in standard path in MB \t\t: {0}".format(size2))

                if size2>size1:
                        print("Enough space available for changing path \t\t: {0}".format("YES"))
                else:
                        print("Not enough space available to change the path\nClear old files and try again")
                        exit(0)


                       

        def copy_files(self):
                os.chdir(self.run_dir_path)
                try:
                        unix_cmd("cp -p -R * %s/"%self.standard_path)
                        print("Files copied Successfully \t\t\t: {0}".format("YES"))
                except:
                        print("Could not copy files to standard path.")
                        exit(0)



        def change_param(self):
                cmd = "su - sqd%s -c \"dbmcli -U c param_directput RunDirectory %s\""%(self.sid.lower(), self.standard_path)
                try:

                        output = unix_cmd(cmd)
                        if "OK" in output:
                                print("Parameter change Successful \t\t\t: {0}".format("YES"))
                except:
                        print("Changing parameter failed.")
                        exit(0)

                self.stop_db()
                self.start_db()



def check_mount(standard_path):
        cmd = 'cat /etc/fstab | grep -i sapdb'
        mounts = unix_cmd(cmd)
        if standard_path in mounts:
                print("Standard fs mount present \t\t\t : {0}".format("YES"))
        else:
                print("Standard fs mount {0} not present".format(standard_path))
                exit(0)




SYS = system()
sid = SYS.get_SID()
present_RD_PATH = SYS.get_run_dir_path()
standard_path = "/sapdb/"+sid+"/data/wrk/"+sid
SYS.check_path_standard(standard_path)

std_mnt_availability = check_mount(standard_path)


SYS.compare_size()
SYS.copy_files()
SYS.change_param()



exit(0)

