#!/usr/bin/env python
import sys
sys.path.append("authclients")
import cPickle
import ClientForm
import cookielib as ClientCookie
import gtk
import cookielib

class WebForm(object):
    def __init__(self, HOME_DIR):
        self.HOME_DIR = HOME_DIR

    
    def load_form(self, pickle_name):
        """Return form if it was loaded from pickle else None"""
        try:
            f = open(self.HOME_DIR + pickle_name, "r")
            form = compose_form = cPickle.load(f)
            f.close()
            return form
        except IOError:
            return None
        
    
    def login(self, username, password):
        """Logs in to check details are correct, and sets current texts left
        Returns True if login was successful else False"""
        while gtk.events_pending():
            gtk.main_iteration(False)
        cookieJar = ClientCookie.CookieJar()
        opener = ClientCookie.build_opener(ClientCookie.HTTPCookieProcessor(cookieJar))
        opener.addheaders = [("User-agent","Mozilla/5.0 (compatible)")]
        ClientCookie.install_opener(opener)
        try:
            fp = ClientCookie.urlopen("https://www.o2.co.uk/login")
        except:
            self.error = "Problem connecting to O2."
            return False
        while gtk.events_pending():
            gtk.main_iteration(True)
        forms = ClientForm.ParseResponse(fp)
        fp.close()
        form = forms[1]
        form["USERNAME"]  = username
        form["PASSWORD"] = password
        fp = ClientCookie.urlopen(form.click())
        for line in fp.readlines():
            if line.startswith('<META HTTP-EQUIV="Refresh" CONTENT="0; URL=http://www.o2.co.uk/">'):
                fp.close()
                return True
            else:
                self.error = "Incorrect login details."
                os.unlink(self.HOME_DIR + "username")
                fp.close()
                return False
        
        
    def send_message(self, to, message, free):
        free_setting = 1 if free else 0
        paid_setting = not free_setting
        self.compose_form.find_control("compose.paymentType").set(free_setting, "free")
        self.compose_form.find_control("compose.paymentType").set(paid_setting, "paid")
        self.compose_form["compose.to"] = to
        self.compose_form["compose.message"] = message
        fp = ClientCookie.urlopen(self.compose_form.click(nr=10))
        fp.close()
        
    
    def get_compose_form(self, tree):
        
        while gtk.events_pending():
            gtk.main_iteration(False)
        fp = ClientCookie.urlopen("http://sendtxt.o2.co.uk/sendtxt/action/compose")
        
        for line in fp:
            if line.startswith("var freeSmsRemaining"):
                tree.free_texts = tree.set_radio_button("free", line)
            elif line.startswith("var paidSmsRemaining"):
                tree.paid_texts = tree.set_radio_button("paid", line)
                break
        tree.select_valid_radio_button()

        if not self.load_form(self.HOME_DIR + os.sep + "form.pickle"):
            fp = ClientCookie.urlopen("http://sendtxt.o2.co.uk/sendtxt/action/compose")
            self.compose_form = ClientForm.ParseResponse(fp)[1]
            f = open(self.HOME_DIR + os.sep + "form.pickle", "w")
            cPickle.dump(self.compose_form, f)
            f.close()
            

    