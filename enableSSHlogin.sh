#!/bin/bash
# 
# Enable ssh login for a user
#
# Usage : ./enableSSHlogin.sh username true
# 
# NB : This script is probably incomplete ... 
# You might need to also add `AllowUsers username` in the /etc/ssh/sshd_config
#

USER=$1

if [[ $2 == "true" ]]
then
    NEWLOGINSHELL="/bin/bash"
else 
    NEWLOGINSHELL="/bin/false"
fi

echo "dn: uid=$USER,ou=users,dc=yunohost,dc=org   
changetype: modify
replace: loginShell
loginShell: $NEWLOGINSHELL" | ldapmodify -D cn=admin,dc=yunohost,dc=org -h 127.0.0.1 -W
