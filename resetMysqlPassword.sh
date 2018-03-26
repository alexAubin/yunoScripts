
. /usr/share/yunohost/helpers.d/string
. /usr/share/yunohost/helpers.d/package

new_pwd=$(ynh_string_random 10)

ynh_package_is_installed "mariadb-server-10.0" \
    && mysql_pkg="mariadb-server-10.0" \
    || mysql_pkg="mysql-server-5.5"

debconf-set-selections << EOF
$mysql_pkg mysql-server/root_password password $new_pwd
$mysql_pkg mysql-server/root_password_again password $new_pwd
EOF

# reconfigure Debian package
dpkg-reconfigure -freadline -u "$mysql_pkg" 2>&1

echo "$new_pwd" >> /etc/yunohost/mysql
chmod 400 /etc/yunohost/mysql

mysqladmin -s -u root -p"$new_pwd" reload
