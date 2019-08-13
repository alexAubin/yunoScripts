#!/bin/bash

#
# THIS WILL ERASE YOUR WHOLE LDAP BASE AND OTHER THINGS
# !!!!! DON'T RUN THIS IN PRODUCTION !!!!!
#

# Remove and purge slapd without removing dependencies
dpkg --purge --force-depends slapd

# Remove nginx conf
rm -rf $(ls /etc/nginx/conf.d/* -d | grep -v "yunohost\|global\|ssowat")
# Remove all yunohost stuff
rm -rf /etc/yunohost/
# Remove all certs / ssl stuff
rm -f /etc/ssl/certs/ca-yunohost_crt.pem
rm -f /etc/ssl/certs/*yunohost*.pem
rm -f /etc/ssl/*/yunohost_*.pem 
rm -f /usr/share/yunohost/yunohost-config/ssl/yunoCA/

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


# Reconfigure yunohost to run the postinst script that will re-init everything
dpkg-reconfigure yunohost
