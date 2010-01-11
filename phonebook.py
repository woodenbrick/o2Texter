#!/usr/bin/env python
import sqlite3
import gtk

class Phonebook(object):
    def __init__(self, db, tree):
        self.conn = sqlite3.Connection(db)
        self.cursor = self.conn.cursor()
        self.cursor.execute("""
                            CREATE TABLE IF NOT EXISTS `phonebook` (
                                `name` varchar(100) NOT NULL,
                                `number` varchar(20) NOT NULL)""")
        self.conn.commit()
        self.tree = tree
        self.update_name_completer()
    
    def add_to_phonebook(self, button):
        name = self.tree.get_widget("new_name").title()
        number = self.tree.get_widget("new_number")
        result = self.cursor.execute("""SELECT * FROM phonebook WHERE name=?""",
                                     (name,)).fetchall()
        if len(result) != 0:
            message = gtk.MessageDialog(
                None, gtk.DIALOG_MODAL, gtk.MESSAGE_INFO,
                gtk.BUTTONS_YES_NO,"%s (%s) already exists in your phonebook. Overwrite?" % (
                    result[0][0], result[0][1]))
            resp = message.run()
            if resp == gtk.YES:
                self.cursor.execute("""UPDATE phonebook set number=? WHERE name=?""", (
                    number, name))
                self.conn.commit()
            message.destroy()
        elif not self.check_number(number):
            self.tree.get_widget("phonebook_info").set_text("Error: Invalid number")
        else:
            self.cursor.execute("""INSERT INTO phonebook (name, number) VALUES
                            (?, ?)""", (name, number))
            self.conn.commit()
            self.tree.get_widget("phonebook_info").set_text(
                "New user %s (%s) added to Phonebook" % (name, number))
    
    def update_name_completer(self):
        result = self.conn.execute("""SELECT * FROM phonebook""").fetchall()
        completer = gtk.EntryCompletion()
        self.tree.get_widget("name").set_completion(completer)
        liststore = gtk.ListStore(str, str)
        completer.set_model(liststore)
        completer.set_text_column(0)
        completer.set_popup_completion(True)
        completer.set_inline_completion(True)
        for r in result:
            liststore.append([r[0], "(%s)" % r[1]])
        #set the phonebook model here also since it is the same
        self.tree.get_widget("phone_treeview").set_model(liststore)
        
    def check_number(self, number):
        """Checks if a phone number is valid
        returns the phone number in the correct format if True
        else false"""
        #re.match()
        return number