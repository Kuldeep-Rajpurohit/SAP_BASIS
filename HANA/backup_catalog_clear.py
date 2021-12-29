!/usr/bin/env python3.8

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

		check_G_keys_cmd = "su - {}adm -c \"hdbuserstore list\" | grep -i ADMIN".format(inst_no.lower())
		exists = linux_cmd(check_G_keys_cmd)
		if "GHADMIN" in exists and "GHTADMIN" in exists:
			return(True)
		else:
			return(False)
	except:
		return(False)


def del_bkp_ctlg_entries(inst_no, key):

	find_id_cmd = """su - {}adm -c "hdbsql -U {} <<EOF
select top 1 (BACKUP_ID),SYS_START_TIME,STATE_NAME FROM SYS.M_BACKUP_CATALOG where SYS_START_TIME <= ADD_DAYS(CURRENT_TIMESTAMP, -45) and ENTRY_TYPE_NAME= 'complete data backup' and STATE_NAME = 'successful' order by backup_id desc
exit
EOF" 2>&1 | grep -i successful
""".format(inst_no.lower(), key)


	id_output = linux_cmd(find_id_cmd)
	id = id_output.split(",")[0]
	print("{} ID is {}".format(key, id))

	get_count_cmd = """su - {}adm -c "hdbsql -U {} <<EOF
SELECT count (*) from SYS.M_BACKUP_CATALOG where BACKUP_ID < {}
exit
EOF" 2>&1 | tail -3 | head -1
""".format(inst_no.lower(), key, id)

	cnt = linux_cmd(get_count_cmd)
	print("{} count : {}".format(key, cnt))


	delete_entries_cmd = """su - {}adm -c "hdbsql -U {} <<EOF
backup catalog delete all before BACKUP_ID {}
exit
EOF" 2>&1
""".format(inst_no.lower(), key, id)

	linux_cmd(delete_entries_cmd)
        
	cnt = linux_cmd(get_count_cmd)
	print("Count After clearing old entries : {}".format(cnt))





sid_cmd = "cat /etc/fstab | grep -i sapdata1 | awk '{print $2}'"
inst_no = get_sid(sid_cmd)
#print("\nSID is {0}".format(inst_no))


key = check_G_key(inst_no)

if key:
#        print("GHADMIN & GHTADMIN keys are present")
	del_bkp_ctlg_entries(inst_no, 'GHADMIN')
	del_bkp_ctlg_entries(inst_no, 'GHTADMIN')

else:
	print("GHADMIN & GHTADMIN keys are not present, delete manually")
	exit(0)

exit(0)

