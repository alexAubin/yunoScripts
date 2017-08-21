#!/bin/bash

#
# THIS WILL ERASE YOUR WHOLE LDAP BASE AND OTHER THINGS
# !!!!! DON'T RUN THIS IN PRODUCTION !!!!!
#

# Remove and purge slapd without removing dependencies
dpkg --purge --force-depends slapd

debconf-set-selections << EOF
slapd slapd/password1 password yunohost
slapd slapd/password2 password yunohost
slapd slapd/domain string yunohost.org
slapd shared/organization string yunohost.org
slapd slapd/allow_ldap_v2 boolean false
slapd slapd/invalid_config boolean true
slapd slapd/backend select MDB
EOF

apt-get install slapd --reinstall

rm -f /etc/yunohost/installed
dpkg-reconfigure yunohost
