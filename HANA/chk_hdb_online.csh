#!/bin/csh

####################################################################################################################################
####################################################################################################################################
## Author             : Kuldeep Rajpurohit
## Version            : v1
## Creation Date      : 25/05/2023
## Functionality      : Check script for HANA DB alive
## Reviewer           : Vijaykumar
## Update Date        : 25/05/2023
####################################################################################################################################
####################################################################################################################################


set sid=$SAPSYSTEMNAME
set user=$sid"adm"
set host=$HOST
set hostname=`hostname -f`
set serv=`hdbsql -U BKPMON -ajx "select status, value from sys.m_system_overview where name='All Started'"`

touch /tmp/db_alive.log
echo "Hello!\n" >> /tmp/db_alive.log

set flag=0
if ($serv == '"OK","Yes"') then
    echo "HANA DB ${sid} is up\n" >> /tmp/db_alive.log
else
    set flag=1
    echo "HANA DB ${sid} is Down\n" >> /tmp/db_alive.log
endif

set date=`date`
echo "Checked : ${date}\n" >> /tmp/db_alive.log
echo "Kind regards from ${host}\n" >> /tmp/db_alive.log

echo "Yours,\n${sid}\n\n" >> /tmp/db_alive.log

cat /tmp/db_alive.log

if ($flag == 1) then
    cat /tmp/db_alive.log | mailx -r ${user}@${hostname} -s "Labs IT HANA DB Alive Check Report for ${sid} on ${host}" DL_5F97A8BB7883FF027EE82632@global.corp.sap
endif

rm -rf /tmp/db_alive.log
