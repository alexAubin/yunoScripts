echo "Fixing / reloading firewall ..."
mv /etc/yunohost/hooks.d/post_iptable_rules/90-vpnclient /tmp/vpn-client-iptable-rules
yunohost firewall reload
service ynh-vpnclient stop
echo "Now starting back the VPN service ... it might take some time"
service ynh-vpnclient start
echo "Done. Hopefully that worked ! Have a good day !"
