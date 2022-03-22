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

def check_G_key(inst_no):
	try:

		check_G_keys_cmd = "su - {}adm -c \"hdbuserstore list\" | grep -wo '[A-Z]*ADMIN[A-Z0-9]*'".format(inst_no.lower())
		exists = linux_cmd(check_G_keys_cmd)
		exists = exists.split("\n")
		exists = [x for x in exists if not x == '']
		return(exists)

	except:
		return(False)



def display_db_name(inst_no, key):
	find_db_name_cmd = """su - {}adm -c "hdbsql -U {} <<EOF
select DATABASE_NAME from SYS.M_DATABASE
exit
EOF" 2>&1 | tail -3 | head -2 | head -1
""".format(inst_no.lower(), key)

	return(linux_cmd(find_db_name_cmd))



def del_bkp_ctlg_entries(inst_no, key):

	find_id_cmd = """su - {}adm -c "hdbsql -U {} <<EOF
select top 1 (BACKUP_ID),SYS_START_TIME,STATE_NAME FROM SYS.M_BACKUP_CATALOG where SYS_START_TIME <= ADD_DAYS(CURRENT_TIMESTAMP, -45) and ENTRY_TYPE_NAME= 'complete data backup' and STATE_NAME = 'successful' order by backup_id desc
exit
EOF" 2>&1 | grep -i successful
""".format(inst_no.lower(), key)

	db_name = display_db_name(inst_no, key)
	print("DB name : {}\tKey : {}".format(db_name.strip("\n"), key))


	id_output = linux_cmd(find_id_cmd)
	id = id_output.split(",")[0]
	print("ID : {}".format(id.strip("\n")))


	get_count_cmd = """su - {}adm -c "hdbsql -U {} <<EOF
SELECT count (*) from SYS.M_BACKUP_CATALOG where BACKUP_ID < {}
exit
EOF" 2>&1 | tail -3 | head -1
""".format(inst_no.lower(), key, id)

	cnt = linux_cmd(get_count_cmd)
	print("Count before deleting : {}".format(cnt.strip("\n")))

	delete_entries_cmd = """su - {}adm -c "hdbsql -U {} <<EOF
backup catalog delete all before BACKUP_ID {}
exit
EOF" 2>&1
""".format(inst_no.lower(), key, id)

	linux_cmd(delete_entries_cmd)
        
	cnt = linux_cmd(get_count_cmd)
	print("Count after deleting : {}\n".format(cnt.strip("\n")))


sid_cmd = "cat /etc/fstab | grep -i sapdata1 | awk '{print $2}'"
inst_no = get_sid(sid_cmd)

#print("\nSID is {0}".format(inst_no))


keys = check_G_key(inst_no)

if key:
	for each in keys:
		del_bkp_ctlg_entries(inst_no, each)

else:
	print("GHADMIN & GHTADMIN keys are not present, delete manually")
	exit(0)

exit(0)
