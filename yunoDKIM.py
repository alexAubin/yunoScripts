#!/usr/bin/python

#
# Quick and dirty script to check if mail sent are signed with DKIM
# - Requires to authenticate as a YunoHost user, so a dummy yunohost user is created
#   temporarily by this script...
# - Relies on dkimvalidator.com with dirty scraping /o\
#

import os
import sys
import time
import smtplib
import random
import requests

charlist = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890"

def main():

    if len(sys.argv) > 2:
        print "Too many arguments"
        return 1
    # Use main domain as default domain
    elif len(sys.argv) == 1:
        with open("/etc/yunohost/current_host") as f:
            domain = f.read().strip("\n")
    else:
        domain = sys.argv[1]

    # Generate a random ID for dkimvalidator.com
    ID = randomString(14)

    # Send a test mail to <the_ID>@dkimvalidator.com from root@<the_domain>
    dkimtester_password = create_test_user(domain)
    sendMail(ID, domain, dkimtester_password)
    delete_test_user()

    # Fetch results from 
    raw = getRawResults(ID)

    # Analyze and display results
    if raw == {}:
        print "Could not retrieve test result"
        return 1
    else:
        displayResults(parseRawResults(raw))
        return 0

def create_test_user(domain):

    password = randomString(30)
    os.system("yunohost user create dkimtester -f DKIM -l Tester -m dkimtester@%s -p %s" % (domain, password))
    return password

def delete_test_user():

    os.system("yunohost user delete dkimtester")


def randomString(size):

    return "".join([random.choice(charlist) for _ in range(size) ])


def sendMail(ID, domain, user_password):
    from_ = "dkimtester@%s" % domain
    to_ = "%s@dkimvalidator.com" % ID
    subject_ = "Hello DKIM validator !"
    text = "Lorem Ipsum"

    message = """\
From: %s
To: %s
Subject: %s
%s
""" % (from_, to_, subject_, text)

    print "Senting test mail to %s from %s ..." % (to_, from_)
    smtp = smtplib.SMTP("localhost")
    smtp.starttls()
    smtp.login("dkimtester", user_password)
    smtp.sendmail(from_, [to_], message)
    smtp.quit()


def getRawResults(ID):

    ID = ID.lower()
    
    found = False
    for i in range(5):
        print "Waiting for mail to be received and analyzed..."
        time.sleep(20)

        # Warning : this is HTTP
        cgi = "http://dkimvalidator.com/cgi-bin"
        roriginal = requests.get("%s/original.pl?email=%s" % (cgi, ID))
 
        if "I haven't received an email recently" in roriginal.text:
            print "Message not received yet, retrying..."
            continue
        else:
            found = True
            break

    if not found:
        return {}

    rdkim = requests.get("%s/dkim.pl?email=%s" % (cgi, ID))
    rspf  = requests.get("%s/spf.pl?email=%s"  % (cgi, ID))
    rspam = requests.get("%s/sa.pl?email=%s"   % (cgi, ID))

    results = {}
    results["Original"]     = roriginal.text
    results["DKIM"]         = rdkim.text
    results["SPF"]          = rspf.text
    results["SpamAssassin"] = rspam.text
    return results


def parseRawResults(raw):
    
    results = {}
    
    results["DKIM"] = {"status": "UNKNOWN", "descr": raw["DKIM"]}
    results["SPF"] = {"status": "UNKNOWN", "descr": raw["SPF"]}
    results["SpamAssassin"] = {"status": "UNKNOWN", "descr": raw["SpamAssassin"]}

    if "This message does not contain a DKIM Signature" in results["DKIM"]["descr"]:
        results["DKIM"] = { 
                             "status": "ERROR", 
                             "descr": "Your mails don't have any"
                                      " DKIM Signature in them."  
                          }
    elif "result = pass" in results["DKIM"]["descr"]:
        results["DKIM"] = { 
                             "status": "GOOD", 
                             "descr": "Your mails are correctly signed with DKIM !"
                          }


    if "Result code: pass" in results["SPF"]["descr"]:
        results["SPF"] = { 
                           "status": "GOOD",
                           "descr": "SPF record is okay !"
                         }
    elif "Result code: none" in results["SPF"]["descr"]:
        results["SPF"] = { 
                           "status": "ERROR",
                           "descr": "No SPF record found."
                         }

    if "Message is NOT marked as spam" in results["SpamAssassin"]["descr"]:
        results["SpamAssassin"] = { 
                                    "status": "GOOD",
                                    "descr": "Your mails are not marked as"
                                             " spam by SpamAssassin"
                                  }

    return results

def displayResults(results):

    print " "
    for key, value in results.items():
        print key
        print "-----"
        print "Status : %s" % value["status"]
        print "Description : %s" % value["descr"]
        print " "

main()