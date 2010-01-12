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
        model = self.tree.get_widget("phone_treeview").get_model()
        name = self.tree.get_widget("new_name").get_text().title()
        number = self.tree.get_widget("new_number").get_text()
        result = self.cursor.execute("""SELECT * FROM phonebook WHERE name=?""",
                                     (name,)).fetchall()
        if len(result) != 0:
            message = gtk.MessageDialog(
                None, gtk.DIALOG_MODAL, gtk.MESSAGE_INFO,
                gtk.BUTTONS_YES_NO,"%s (%s) already exists in your phonebook. Overwrite?" % (
                    result[0][0], result[0][1]))
            resp = message.run()
            if resp == gtk.RESPONSE_YES:
                self.cursor.execute("""UPDATE phonebook set number=? WHERE name=?""", (
                    number, name))
                self.conn.commit()
                for path in model:
                    print path[0]
                    if path[0] == name:
                        path[1] = number
                        break
            message.destroy()
        elif not self.check_number(number):
            self.tree.get_widget("phonebook_info").set_text("Error: Invalid number")
        else:
            self.cursor.execute("""INSERT INTO phonebook (name, number) VALUES
                            (?, ?)""", (name, number))
            self.conn.commit()
            self.tree.get_widget("phonebook_info").set_text(
                "%s added" % name)
            model.append([name, number])
        self.tree.get_widget("new_name").set_text("")
        self.tree.get_widget("new_number").set_text("")
    
    def delete_from_phonebook(self, button):
        model, iter = self.tree.get_widget("phone_treeview").get_selection().get_selected()
        if iter is None:
            self.tree.get_widget("phonebook_info").set_text("Please select an entry to delete")
        else:
            message = gtk.MessageDialog(
                None, gtk.DIALOG_MODAL, gtk.MESSAGE_INFO,
                gtk.BUTTONS_YES_NO,"Are you sure you want to delete %s (%s)?" % (
                    model.get_value(iter, 0), model.get_value(iter, 1)))
            resp = message.run()
            if resp == gtk.RESPONSE_YES:
                self.cursor.execute("""DELETE FROM phonebook WHERE name=?""", (
                    model.get_value(iter,0),))
                self.conn.commit()
            self.tree.get_widget("phonebook_info").set_text(
                "%s deleted" % model.get_value(iter, 0))
            model.remove(iter)
            message.destroy()
            
            
            
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
            liststore.append([r[0], r[1]])
        #set the phonebook model here also since it is the same
        self.tree.get_widget("phone_treeview").set_model(liststore)
        
    def check_number(self, number):
        """Checks if a phone number is valid
        returns the phone number in the correct format if True
        else false"""
        #re.match()
        return number
    
    def get_number(self, name):
        result = self.cursor.execute("""SELECT number from phonebook
                                     WHERE name=?""", (name,)).fetchone()
        try:
            return result[0]
        except IndexError:
            return name
        