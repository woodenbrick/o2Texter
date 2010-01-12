#!/usr/bin/env python
import sys
import os
import socket
import re
import gtk
import gtk.glade
import cPickle
from phonebook import Phonebook
from form import WebForm

socket.setdefaulttimeout(15)
__version__ = "0.01"
__author__ = ("Daniel Woodhouse <wodemoneke@gmail.com>",)

class O2Texter(object):
    def __init__(self):
        try:
            HOME_DIR = os.path.join(os.environ['HOME'], ".o2texter")
        except KeyError:
            HOME_DIR = os.path.join(os.environ['HOMEPATH'], ".o2texter")
        try:
            os.mkdir(HOME_DIR)
        except OSError:
            pass
        try:
            self.tree = gtk.glade.XML("texter.glade")
        except:
            #find glade dir
            self.tree = gtk.glade.XML("/usr/share/02texter/texter.glade")
        self.tree.signal_autoconnect(self)
        
        self.phonebook = Phonebook(HOME_DIR + os.sep + "phonebook", self.tree)
        self.form = WebForm(HOME_DIR)
        self.tree.signal_autoconnect(self.phonebook)
        #self.tree.get_widget("texter").show()
        while gtk.events_pending():
            gtk.main_iteration(True)
        #create column for phonebook
        col = gtk.TreeViewColumn("Name")
        cell = gtk.CellRendererText()
        col.pack_start(cell, True)
        col.set_attributes(cell, text=0)
        self.tree.get_widget("phone_treeview").append_column(col)
        col = gtk.TreeViewColumn("Phone")
        cell = gtk.CellRendererText()
        col.pack_start(cell, True)
        col.set_attributes(cell, text=1)
        self.tree.get_widget("phone_treeview").append_column(col)
        
        self.free_texts = 0
        self.paid_texts = 0
        self.message_count = 0
        self.set_limits(self.tree.get_widget("free").get_active())
        
        #get username and password
        try:
            f = open("username", "r")
            self.username, self.password = cPickle.load(f)
            f.close()
            self.tree.get_widget("texter").show()
            self.tree.get_widget("main_info").set_text("Logging in...")
            if self.form.login(self.username, self.password):
                self.tree.get_widget("main_info").set_text("Retrieving account details...")
                self.form.get_compose_form(self)
                self.tree.get_widget("main_info").set_text("")
            else:
                self.tree.get_widget("main_info").set_text(self.form.error)
                #XXX set a retry timout
        except IOError:
            self.tree.get_widget("login_window").show()
    
    def login_clicked(self, *args):
        self.username = self.tree.get_widget("uname").get_text()
        self.password = self.tree.get_widget("pass").get_text()
        f = open("username", "w")
        cPickle.dump([self.username, self.password], f)
        f.close()
        self.tree.get_widget("login_window").hide()
        self.tree.get_widget("texter").show()
        if self.form.login():
            self.get_compose_form()
    
    def change_case(self, entry, *args):
        entry.set_text(entry.get_text().title())
        
    def textbody_changed(self, textbody, key):
        char_count = textbody.get_buffer().get_char_count()
        if char_count < 1:
            self.message_count = 0
        elif char_count < self.total_limit / 3:
            self.message_count = 1
        elif char_count < (self.total_limit / 3) * 2:
            self.message_count = 2
        else:
            self.message_count = 3
        self.tree.get_widget("character_count").set_text("%s/%s %s/3" % (
            char_count, self.total_limit, self.message_count))
        if char_count > self.total_limit:
            self.tree.get_widget("main_info").set_text("Maximum of %s characters allowed.  Please shorten your message" % self.total_limit)
            self.tree.get_widget("send").set_sensitive(False)
        elif char_count < 1:
            self.tree.get_widget("send").set_sensitive(False)
        else:
            self.tree.get_widget("main_info").set_text("")
            self.tree.get_widget("send").set_sensitive(True)
            
    def free_toggled(self, button):
        self.set_limits(button.get_active())
        self.textbody_changed(self.tree.get_widget("textbody"), None)
            
    def set_limits(self, free):
        if free:
            self.total_limit = 444
        else:
            self.total_limit = 480
            
    def set_radio_button(self, widgetname, counter, clean=False):
        if not clean:
            counter = int(counter.strip(";\r\n").split(" = ")[1])
        self.tree.get_widget(widgetname).set_label("%s %s texts remaining" % (
            counter, widgetname))
        self.tree.get_widget(widgetname).set_sensitive(counter)
        return counter
    
    
    def on_clear_clicked(self, button):
        pass
    
    def gtk_main_quit(self, *args):
        gtk.main_quit()
        
        
    def select_valid_radio_button(self):
        """return True if the user can send texts"""
        if self.free_texts > 0:
            self.tree.get_widget("free").set_active(True)
        elif self.paid_texts > 0:
            self.tree.get_widget("paid").set_active(True)
        else:
            self.tree.get_widget("main_info").set_text("You cannot send any texts")
            self.tree.get_widget("textbody").set_sensitive(False)
            self.tree.get_widget("send").set_sensitive(False)
        

    def open_phonebook(self, button):
        self.tree.get_widget("phonebook").show()
        
    def close_phonebook(self, window, *args):
        window.hide()
        return True
    
    def choose_from_phonebook(self, treeview, path, col):
        """When the user doubleclicks a name in the phonebook it will be placed
        in the reciever TextEntry box"""
        self.tree.get_widget("phonebook").hide()
        model = treeview.get_model()
        iter = model.get_iter(path)
        self.tree.get_widget("name").set_text(model.get_value(iter,0))
        self.tree.get_widget("textbody").grab_focus()
    
    def on_send_clicked(self, button):
        self.tree.get_widget("main_info").set_text("Sending message...")
        while gtk.events_pending():
            gtk.main_iteration(False)
        buffer = self.tree.get_widget("textbody").get_buffer()
        message = buffer.get_text(*buffer.get_bounds()).strip()
        #check this is a valid number or name in db
        number = self.phonebook.get_number(self.tree.get_widget("name").get_text())
        self.form.send_message(number, message, self.tree.get_widget("free").get_active())
        self.tree.get_widget("main_info").set_text("")
        buffer.set_text("")
        #deduct messages
        if self.tree.get_widget("free").get_active():
            self.free_texts -= self.message_count
            self.set_radio_button("free", self.free_texts, clean=True)
        else:
            self.paid_texts -= self.message_count
            self.set_radio_button("paid", self.paid_texts, clean=True)
            

def run():
    texter = O2Texter()
    gtk.main()

if __name__ == "__main__":
    run()
