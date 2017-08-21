#!/usr/bin/python2.7
# -*- coding: utf-8 -*-

#
# Quick and dirty script to check if a domain DNS conf match recommended conf
# for a Yunohost instance.
#

import json
import os
import sys
import subprocess
import re
import requests


# Take first resolver from /etc/resolv.dnsmasq.conf

resolver = subprocess.check_output("cat /etc/resolv.dnsmasq.conf".split()).split("\n")[0].split(" ")[1]

# Fetch ipv4 and ipv6...

try:
    ipv4 = requests.get("https://ip.yunohost.org/").text
except:
    ipv4 = None

try:
    ipv6 = requests.get("https://ip6.yunohost.org/").text
except:
    ipv6 = None


available_categories = ["basic", "xmpp", "mail"]
def usage_and_exit():
    print "Usage : "
    print "   python yunoCheckDNS.py your.domain.tld [--basic] [--mail] [--xmpp]"


def main():

    # Quick and dirty argument parsing

    selected_categories = []
    domain = None
    for arg in sys.argv[1:]:
        if arg.startswith("--"):
            arg = arg.replace("--", "")
            if arg not in available_categories:
                usage_and_exit()
            else:
                selected_categories.append(arg)
        else:
            if domain is not None:
                usage_and_exit()
            domain = arg

    if domain is None:
        usage_and_exit()
    if selected_categories == []:
        selected_categories = available_categories

    # Check choosen domain exists in yunohost

    if domain not in get_yunohost_domains():
        print "Error : domain %s is not configured in Yunohost !" % domain
        sys.exit(-1)

    # Get recommended dns conf

    dnsconf = _build_dns_conf(domain)

    # For each category, fetch current DNS record/value

    for category, records in dnsconf.items():
        if category not in selected_categories:
            continue
        for i, record in enumerate(records):
            currentValue = get_current_record(domain, record["name"], record["type"])
            dnsconf[category][i]["currentValue"] = currentValue

    # Analyze current values vs expected values
    for category, records in dnsconf.items():
        if category not in selected_categories:
            continue
        print " "
        print category
        print "-------"
        for i, record in enumerate(records):

            if record["expectedValue"] == "@":
                record["expectedValue"] = domain+'.'

            if record["currentValue"] == "":
                record["currentValue"] = "Nothing!"


            if record["expectedValue"] == record["currentValue"]:
                print "%s record for %s : OK! :)" % (record["type"], record["name"])
            else:
                print " "
                print "%s record for %s : Problem found :(" % (record["type"], record["name"])
                print "    Expected : %s " % record["expectedValue"]
                print "    Current  : %s " % record["currentValue"]
                print " "


def get_yunohost_domains():
    domainList = subprocess.check_output("yunohost domain list --output-as json".split())
    return json.loads(domainList)["domains"]


def get_current_record(domain, name, type_):
    if name == "@":
        command = "dig +short @%s %s %s" % (resolver, type_, domain)
    else:
        command = "dig +short @%s %s %s.%s" % (resolver, type_, name, domain)
    output = subprocess.check_output(command.split()).strip()
    output = output.replace("\;",";")
    if output.startswith('"') and output.endswith('"'):
        output = '"' + ' '.join(output.replace('"',' ').split()) + '"'
    return output


def _build_dns_conf(domain, ttl=3600):

    # Init output / groups
    dnsconf = {}
    dnsconf["basic"] = []
    dnsconf["xmpp"] = []
    dnsconf["mail"] = []

    def _dns_record(name, ttl, type_, value):

        return { "name": name,
                 "ttl": ttl,
                 "type": type_,
                 "expectedValue": value
        }

    # Basic ipv4/ipv6 records
    if ipv4:
        dnsconf["basic"].append(_dns_record("@", ttl, "A", ipv4))
        #dnsconf["basic"].append(_dns_record("*", ttl, "A", ipv4))

    if ipv6:
        dnsconf["basic"].append(_dns_record("@", ttl, "AAAA", ipv6))
        #dnsconf["basic"].append(_dns_record("*", ttl, "AAAA", ipv6))

    # XMPP
    dnsconf["xmpp"].append(_dns_record("_xmpp-client._tcp", ttl, "SRV", "0 5 5222 %s." % domain))
    dnsconf["xmpp"].append(_dns_record("_xmpp-server._tcp", ttl, "SRV", "0 5 5269 %s." % domain))
    dnsconf["xmpp"].append(_dns_record("muc", ttl, "CNAME", "@"))
    dnsconf["xmpp"].append(_dns_record("pubsub", ttl, "CNAME", "@"))
    dnsconf["xmpp"].append(_dns_record("vjud", ttl, "CNAME", "@"))

    # Email
    dnsconf["mail"].append(_dns_record("@", ttl, "MX", "10 %s." % domain))

        # SPF record
    spf_record = '"v=spf1 a mx'
    if ipv4:
        spf_record += ' ip4:{ip4}'.format(ip4=ipv4)
    if ipv6:
        spf_record += ' ip6:{ip6}'.format(ip6=ipv6)
    spf_record += ' -all"'

    dnsconf["mail"].append(_dns_record("@", ttl, "TXT", spf_record))

        # DKIM/DMARC record
    dkim_host, dkim_publickey = _get_DKIM(domain)
    if dkim_host:
        dnsconf["mail"].append(_dns_record(dkim_host, ttl, "TXT", dkim_publickey))
        dnsconf["mail"].append(_dns_record("_dmarc", ttl, "TXT", '"v=DMARC1; p=none"'))

    return dnsconf


def _get_DKIM(domain):
    DKIM_file = '/etc/dkim/{domain}.mail.txt'.format(domain=domain)

    if not os.path.isfile(DKIM_file):
        return (None, None)

    with open(DKIM_file) as f:
        dkim_content = f.read()

    dkim = re.match((
        r'^(?P<host>[a-z_\-\.]+)[\s]+([0-9]+[\s]+)?IN[\s]+TXT[\s]+[^"]*'
        '(?=.*(;[\s]*|")v=(?P<v>[^";]+))'
        '(?=.*(;[\s]*|")k=(?P<k>[^";]+))'
        '(?=.*(;[\s]*|")p=(?P<p>[^";]+))'), dkim_content, re.M | re.S
    )

    if dkim:
        return (dkim.group('host'),
                '"v={v}; k={k}; p={p}"'.format(
                v=dkim.group('v'), k=dkim.group('k'), p=dkim.group('p')))
    else:
        return (None, None)

main()