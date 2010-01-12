#!/usr/bin/env python
import os
import cPickle
import ClientForm
import cookielib
import urllib2
import gtk
import threading
gtk.gdk.threads_init()
import Queue

class Threaded_Http_Request(object):
    def __init__(self):
        self.queue = Queue.Queue()
    
    def url_open(self, url, callback=None, extra_args=[]):
        """Run in a seperate thread"""
        conn = threading.Thread(target=self._url_open, args=(
            [url]))
        conn.start()
        while gtk.events_pending():
            gtk.main_iteration(True)
        if callback is not None:
            result = callback(self.queue.get(), *extra_args)
            return result
    
    def _url_open(self, url):
        request = urllib2.urlopen(url)
        self.queue.put(request)


class WebForm(object):
    def __init__(self, HOME_DIR):
        self.HOME_DIR = HOME_DIR
        self.url_request = Threaded_Http_Request()
        

    
    def load_form(self, pickle_name):
        """Return form if it was loaded from pickle else None"""
        try:
            f = open(self.HOME_DIR + os.sep + pickle_name, "r")
            form = cPickle.load(f)
            f.close()
            print "Successfully loaded %s" % pickle_name
            return form
        except IOError:
            print "Pickle not found: %s" % pickle_name
            return None
        
    def save_form(self, obj, pickle_name):
        f = open(self.HOME_DIR + os.sep + pickle_name, "w")
        form = cPickle.dump(obj, f)
        f.close()       
        
    
    def login(self, username, password):
        """Logs in to check details are correct, and sets current texts left
        Returns True if login was successful else False"""
        self.username = username
        self.password = password
        cookieJar = cookielib.CookieJar()
        opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cookieJar))
        opener.addheaders = [("User-agent","Mozilla/5.0 (compatible)")]
        urllib2.install_opener(opener)
        form = self.load_form("login.pickle")
        if form is None:
            result = self.url_request.url_open("https://www.o2.co.uk/login", self.login_cb)
        else:
            result = self.login_cb(form, True)
        return result
        
    
    def parse_form(self, request, index):
        forms = ClientForm.ParseResponse(request)
        request.close()
        return forms[index]
    
    def login_cb(self, form, is_parsed=False):
        """Called when we recieve the login http request"""
        if not is_parsed:
            form = self.parse_form(form, 1)
            self.save_form(form, "login.pickle")
        form["USERNAME"]  = self.username
        form["PASSWORD"] = self.password
        return self.url_request.url_open(form.click(), self.check_login)
        
        
    def check_login(self, request):
        for line in request.readlines():
            if line.startswith('<META HTTP-EQUIV="Refresh" CONTENT="0; URL=http://www.o2.co.uk/">'):
                request.close()
                return True
            else:
                self.error = "Incorrect login details."
                os.unlink(self.HOME_DIR + "username")
                request.close()
                return False
        
        
    def send_message(self, to, message, free):
        free_setting = 1 if free else 0
        paid_setting = not free_setting
        self.compose_form.find_control("compose.paymentType").set(free_setting, "free")
        self.compose_form.find_control("compose.paymentType").set(paid_setting, "paid")
        self.compose_form["compose.to"] = to
        self.compose_form["compose.message"] = message
        self.url_request.url_open(self.compose_form.click(nr=10), self.msg_sent_cb)
        
    def msg_sent_cb(self, request):
        """Check the request and make sure the message was sent or get an error message"""
        return True
    
    
    def get_compose_form(self, tree=None):
        """Setting tree to None will create a new form pickle, otherwise we
        will grab text count data from the form"""
        url = "http://sendtxt.o2.co.uk/sendtxt/action/compose"
        if tree is not None:
            #get remaining texts then run compose form again to get a copy of the form
            self.url_request.url_open(url, self.parse_remaining_texts_cb, [tree])
            tree.select_valid_radio_button()
            self.get_compose_form(None)
            
        else:   
            self.compose_form = self.load_form("form.pickle")
            if self.compose_form is None:
                self.url_request.url_open(url, callback=self.set_compose_form)
    
    def set_compose_form(self, result):
        self.compose_form = self.parse_form(result, 1)
        self.save_form(self.compose_form, "form.pickle")
            
    def parse_remaining_texts_cb(self, request, tree):
        for line in request:
            if line.startswith("var freeSmsRemaining"):
                tree.free_texts = tree.set_radio_button("free", line)
            elif line.startswith("var paidSmsRemaining"):
                tree.paid_texts = tree.set_radio_button("paid", line)
                break

    