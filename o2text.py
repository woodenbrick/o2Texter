#!/usr/bin/env python
import sys
import os
sys.path.append("authclients")
import ClientForm
import ClientCookie
import sqlite3
import socket
import re
socket.setdefaulttimeout(15)
__version__ = "0.01"
__author__ = ("Daniel Woodhouse <wodemoneke@gmail.com>",)

class O2Texter(object):
    def __init__(self):
        self.conn = sqlite3.Connection("phonebook")
        self.cursor = self.conn.cursor()
        self.cursor.execute("""
                            CREATE TABLE IF NOT EXISTS `phonebook` (
                                `name` varchar(100) NOT NULL,
                                `number` varchar(20) NOT NULL)""")
        self.conn.commit()
        try:
            if sys.argv[1] == "add":
                self.add_to_phonebook()
            elif sys.argv[1] == "phonebook":
                self.print_phonebook()
            else:
                #we assume the user is giving us 2 arguments: a number/phonebook user
                #and the message
                to = sys.argv[1]
                try:
                    to = int(to)
                except ValueError:
                    result = self.cursor.execute("""SELECT number FROM phonebook WHERE
                                        name=?""", (to.title(),)).fetchone()
                    if result is None:
                        print 'No user with that name exists in the phonebook'
                        return
                    else:
                        to = result[0]

                message = " ".join(sys.argv[2:])
                if self.login():
                    self.send_text(to, message)
        except IndexError:
            print "Incorrect arguments"
        
    def login(self):
        """Logs in to check details are correct, and sets current texts left
        Returns True if login was successful else False"""
        try:
            f = open("login-details", "r")
            self.username = f.readline()
            self.password = f.readline()
            f.close()
        except IOError:
            f = open("login-details", "w")
            self.username = raw_input("username: ")
            self.password = raw_input("password: ")
            f.write(self.username + "\n")
            f.write(self.password + "\n")
            f.close()

        cookieJar = ClientCookie.CookieJar()        
        opener = ClientCookie.build_opener(ClientCookie.HTTPCookieProcessor(cookieJar))
        opener.addheaders = [("User-agent","Mozilla/5.0 (compatible)")]
        ClientCookie.install_opener(opener)
        print "Logging in...",
        #try:
        fp = ClientCookie.urlopen("https://www.o2.co.uk/login")
        #except:
        #    print("Problem connecting to O2.")
        #    return False
        forms = ClientForm.ParseResponse(fp)
        fp.close()
        print("Done.")
        form = forms[1]
        form["USERNAME"]  = self.username
        form["PASSWORD"] = self.password
        fp = ClientCookie.urlopen(form.click())
        for line in fp.readlines():
            if line.startswith('<META HTTP-EQUIV="Refresh" CONTENT="0; URL=http://www.o2.co.uk/">'):
                fp.close()
                return True
            else:
                print("Incorrect login details.")
                os.unlink("login-details")
                fp.close()
                return False
        
        
    def add_to_phonebook(self):
        name = raw_input("Name: ").title()
        result = self.cursor.execute("""SELECT * FROM phonebook WHERE name=?""", (name,)).fetchall()
        if len(result) != 0:
            choice = raw_input('User %s already exists. (O)verwrite, (R)ename or (C)ancel)' % name)
            if choice.upper() == "C":
                return
            if choice.upper() == "R":
                self.add_to_phonebook()
                return
            if choice.upper() == "O":
                pass
        number = self.check_number(raw_input("Number: "))
        if not number:
            print 'Incorrect format for number'
            return False
        self.cursor.execute("""INSERT INTO phonebook (name, number) VALUES
                            (?, ?)""", (name, number))
        self.conn.commit()
        print 'New user (%s, %s) added to Phonebook' % (name, number)
    
    def print_phonebook(self):
        result = self.cursor.execute("""SELECT * FROM phonebook""").fetchall()
        print "-" * 10 + " Phonebook " + "-" * 10
        for item in result:
            print item[0], item[1]
        print "-" * 30
    
    def send_text(self, to, message):

        fp = ClientCookie.urlopen("http://sendtxt.o2.co.uk/sendtxt/action/compose")
        form = ClientForm.ParseResponse(fp)[1]
        form["compose.to"] = to
        form["compose.message"] = message
        fp = ClientCookie.urlopen(form.click(nr=10))
        fp.close()
        
    def check_number(self, number):
        """Checks if a phone number is valid
        returns the phone number in the correct format if True
        else false"""
        #re.match()
        return number


texter = O2Texter()
