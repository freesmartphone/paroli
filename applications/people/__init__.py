# -*- coding: utf-8 -*-
#    Paroli
#
#    copyright 2009 OpenMoko
#
#    This file is part of Paroli.
#
#    Paroli is free software: you can redistribute it and/or modify it
#    under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    Paroli is distributed in the hope that it will be useful, but
#    WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
#    General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with Paroli.  If not, see <http://www.gnu.org/licenses/>.

from logging import getLogger
logger = getLogger('applications.people')

from os.path import join, dirname
from ecore.x import ECORE_X_VIRTUAL_KEYBOARD_STATE_OFF, ECORE_X_VIRTUAL_KEYBOARD_STATE_ON
from elementary import Button, Entry, Table
from paroli.gui import ElementaryListWindow, ElementaryList, ElementaryLayout, ElementaryListSubwindow
from tichy.service import Service
from tichy.application import Application
from tichy.tasklet import WaitFirst, Wait, tasklet
from paroli.sim import SIMContact

class People(Application):
    name = 'People'
    icon = 'icon.png'
    category = 'launcher' # So that we see the app in the launcher

    def run(self, parent, standalone=False):

        ##set edje file to be used
        ##TODO: make one edje file per plugin
        self.edje_file = join(dirname(__file__),'people.edj')

        ##get contact service and list of all contacts
        self.contact_service = Service.get('Contacts')
        self.contacts = self.contact_service.contacts

        ##sort contact by name
        def comp(m1, m2):
            return cmp(str(m1.name).lower(), str(m2.name).lower())

        ##generate app-window
        self.window = ElementaryListWindow(self.edje_file, "main", "list", None, None, True)
        self.edje_obj = self.window.main_layout

        self.list_label = [('label','name')]
        self.item_list = ElementaryList(self.contacts, self.window, self.edje_file, "item", self.list_label, comp, True)

        self.item_list.add_callback("contact_details", "*", self.contact_details)
        self.item_list.add_callback("send_all", "fold-back", self.self_test)
        self.item_list.add_callback("create_message", "*", self.create_msg)

        self.edje_obj.add_callback("back-button", "*", self.signal)
        self.edje_obj.add_callback("add_contact", "*", self.create_contact)
        self.edje_obj.add_callback("*", "dict", self.openDict)

        ##wait until main object emits back signal or delete is requested

        #self.window.scroller.elm_obj.focus()
        #self.item_list.jump_to_index('q')
        parent.emit("unblock")

        yield WaitFirst(Wait(self.window, 'delete_request'),Wait(self.window, 'back'))
        logger.info('People closing')
        #self.main.emit('closed')

        self.window.delete()
        #del self.item_list
    
    def openDict(self, emission, signal, source):
        if signal == "opening":
            self.dictButtons = []
            self.dictTable = Table(self.window.window.elm_obj)
            self.dictTable.show()
            self.dictTable.layer_set(99)
            self.edje_obj.elm_obj.content_set("dict-window",self.dictTable)
            counter_x = 0
            counter_y = 0
            keys = self.item_list.letter_index.keys()
            keys.sort()
            for i in keys:
                button = Button(self.window.window.elm_obj)
                button.label_set(i)
                button.on_mouse_up_add(self.item_list.jump_to_index, i)
                self.dictButtons.append(button)
                button.show()
                self.dictTable.pack(button, counter_x*20, round((counter_y / 5) + 0.5) * 20 , 20, 20)
                counter_y += 1
                if counter_x == 4:
                    counter_x = 0
                else:
                    counter_x += 1
            
        elif signal == "closing":
            logger.info("closing")
            for i in self.dictButtons :
                i.hide()
                if not i.is_deleted():
                    del i
    
    def signal(self, emission, signal, source):
        """ Callback function. It invokes, when the "back" button clicked."""
        logger.info("signal() emmision: %s, signal: %s, source: %s",
                    str(emission), str(signal), str(source))
        self.window.emit('back')


    ##DEBUG FUNCTIONS
    ## general output check
    def self_test(self, *args, **kargs):
        txt = "self test called with args: ", args, "and kargs: ", kargs
        logger.info(txt)

    def create_contact(self, emission, source, param):
        service = Service.get('ContactCreate')
        service.create(self.window).start()

    def contact_details(self, emission, source, param, item):
        number = str(item[0].tel)
        name = unicode(item[0].name).encode("utf-8")
        detail_layout =  ElementaryLayout(self.window.window, self.edje_file, "contact_details")
        edje_obj = detail_layout.elm_obj.edje_get()
        edje_obj.part_text_set('name-text',str(name).encode('utf8'))
        edje_obj.part_text_set('number-text',str(number).encode('utf8'))
        detail_layout.elm_obj.show()
        self.window.main_layout.elm_obj.hide()
        self.window.bg.elm_obj.content_set("content-swallow", detail_layout.elm_obj)

        def _update_values(contact, edje, *args, **kargs):
            edje.part_text_set('name-text',unicode(contact.name).encode('utf8'))
            edje.part_text_set('number-text',str(contact.tel).encode('utf8'))
            self.contacts.emit("inserted")

        oid = item[0].connect('modified', _update_values, edje_obj)

        ##add callback for delete button
        edje_obj.signal_callback_add("delete_contact", "*", self.delete_contact, item[0], detail_layout)

        ##add callback for edit buttons
        edje_obj.signal_callback_add("*", "edit", self.edit_contact, item[0], detail_layout)

        ##add callback for calling
        edje_obj.signal_callback_add("call_contact", "*", self.call_contact, item[0])

        ##add callbacks for back button
        edje_obj.signal_callback_add("close_details", "*", detail_layout.delete)
        edje_obj.signal_callback_add("close_details", "*", self.window.restore_orig)

    #editing
    def edit_contact(self, emission, signal, source, contact, layout):
        logger.info("people->edit_contact")
        service = Service.get('ContactCreate')
        service.create(self.window, "", "", contact, signal, layout).start()

    def call_contact(self, emission, source, param, contact):
        number = contact.tel.value
        name = unicode(contact)
        caller_service = Service.get('TeleCaller2')
        caller_service.call("window", number, name).start()

    #deleting

    def delete_contact(self, emission, signal, source, item, layout):
        self.delete_contact_taskl(emission, signal, source, item, layout).start()

    @tasklet
    def delete_contact_taskl(self, emission, signal, source, item, layout):
        logger.info("delete contact called")
        try:
            self.contact_service.remove(item)
            if isinstance(item, SIMContact):
                logger.info("is SIMContact")
                yield item.delete()
                #self.sim_service = Service.get('SIM')
                #logger.info("remove contact %s from sim", item.name)
                #yield WaitDBus(self.sim_service.gsm_sim.DeleteEntry, 'contacts',item.sim_index)

        except Exception, ex:
            logger.exception("Got error %s", ex)
        else:
            layout.delete()
            self.window.restore_orig()

        yield None

    def create_msg(self, emission, source, param, item):
        service = Service.get('MessageCreate')
        service.write(self.window, 'reply', item[0].tel).start()

##Service to store some info
class ContactCreate(Service):
    service = 'ContactCreate'

    def __init__(self):
        super(ContactCreate, self).__init__()

    @tasklet
    def init(self):
        yield self._do_sth()

    def _do_sth(self):
        pass

    def create(self, window, number="", name="", contact=None, mode=None, layout=None):
        return CreateContact(window, number, name, contact, mode, layout)

    def contactList(self, window, layout):
        ret = ListContacts(window, layout)
        #print ret
        return ret

class ListContacts(Application):

    name = 'ListContactsApp'

    def run(self, parent, layout, *args, **kargs):

        self.edje_file = join(dirname(__file__), 'people.edj')
        self.list_layout =  ElementaryListSubwindow(parent, self.edje_file, "main", "list")

        edje_obj = self.list_layout.main_layout.elm_obj.edje_get()

        edje_obj.signal_emit('list_only_mode', "*")

        self.list_layout.main_layout.elm_obj.show()

        ##get contact service and list of all contacts
        self.contact_service = Service.get('Contacts')
        self.contacts = self.contact_service.contacts

        ##sort contact by name
        def comp(m1, m2):
            return cmp(str(m1.name).lower(), str(m2.name).lower())

        self.list_label = [('label','name')]
        self.item_list = ElementaryList(self.contacts, self.list_layout, self.edje_file, "item", self.list_label, comp)

        self.item_list.signal_send('list_only_mode', "*")

        parent.main_layout.elm_obj.hide()
        layout.elm_obj.hide()

        parent.bg.elm_obj.content_set("content-swallow", self.list_layout.main_layout.elm_obj)

        self.item_list.add_callback("contact_details", "*", self.contact_clicked)

        yield Wait(self.list_layout, 'picked')

        self.list_layout.main_layout.delete()
        parent.restore_orig()
        layout.elm_obj.show()

        yield self.contact

    def contact_clicked(self, emission, signal, source, item):
        self.contact = item[0]
        self.list_layout.emit('picked')

class CreateContact(Application):

    name = 'CreateContactApp'

    def run(self, parent, number, name, contact, mode, layout, *args, **kargs):
        try:
            self.edje_file = join(dirname(__file__), 'people.edj')
            number_layout = 0
            text_layout = 0
            send = 0
            
            if contact != None:
                name = unicode(contact.name).encode("utf-8")
                number = str(contact.tel)
                layout.elm_obj.hide()
            
            if number == "":
                full = True
            else:
                full = False
            
            while True:
                if full or mode == "number":
                    parent.window.elm_obj.keyboard_mode_set(ECORE_X_VIRTUAL_KEYBOARD_STATE_OFF)
                    if number_layout == 0:
                        number_layout =  ElementaryLayout(parent.window, self.edje_file, "edit_number")
                        edje_obj = number_layout.elm_obj.edje_get()
                        edje_obj.part_text_set('num_field-text', number)
                        number_layout.elm_obj.show()
                        parent.main_layout.elm_obj.hide()
                    else:
                        number_layout.elm_obj.show()
                    parent.bg.elm_obj.content_set("content-swallow", number_layout.elm_obj)
                    i, args = yield WaitFirst(Wait(number_layout, 'back'), Wait(number_layout, 'next'))
                    if i == 0: #back
                        logger.debug("breaking")
                        break
                    if i == 1: #next
                        number_layout.elm_obj.hide()
                        number = edje_obj.part_text_get('num_field-text') 
                        if mode == "number":
                            send = 1
                            break
                
                if mode != "number":
                    parent.window.elm_obj.keyboard_mode_set(ECORE_X_VIRTUAL_KEYBOARD_STATE_ON)  
                    if text_layout == 0:
                        text_layout = ElementaryLayout(parent.window, self.edje_file, "CreateContact")
                        edje_obj = text_layout.elm_obj.edje_get()
                        text_layout.elm_obj.show()
                        parent.main_layout.elm_obj.hide()
                        textbox = Entry(parent.window.elm_obj)
                        textbox.single_line_set(True)
                        textbox.color_set(255, 255, 255, 255)
                        textbox.entry_set(name)
                        textbox.size_hint_weight_set(1.0, 1.0)
                        text_layout.elm_obj.content_set('entry', textbox)
                        textbox.editable_set(True)        
                    
                    else:
                        text_layout.elm_obj.show()
                    parent.bg.elm_obj.content_set("content-swallow", text_layout.elm_obj)
                    
                    textbox.focus()
                    textbox.show()
                    
                    i, args = yield WaitFirst(Wait(text_layout, 'back'),
                                              Wait(text_layout, 'save'))
                    
                    if i == 0: #back
                        if full:
                            text_layout.elm_obj.hide()
                            parent.window.elm_obj.keyboard_mode_set(ECORE_X_VIRTUAL_KEYBOARD_STATE_OFF)
                            continue
                        else:
                            break
                    if i == 1: #save
                        send = 1
                        break
            if send == 1:
                if text_layout:
                    text_layout.elm_obj.edje_get().signal_emit("save-notice","*")
                contacts_service = Service.get('Contacts')
                if contact not in contacts_service.contacts:
                    name = unicode(textbox.entry_get()).replace("<br>","").encode("utf-8")
                    new_contact = contacts_service.create(name.strip(),tel=str(number))
                    contacts_service.add(new_contact)
                    contacts_service.contacts.emit('inserted')
                else:
                    if mode == "name":
                        name = unicode(textbox.entry_get()).replace("<br>","").encode("utf-8")
                        logger.info("updating name")
                        contact.name = name.strip()
                    elif mode == "number":
                        logger.info("updating number")
                        contact.tel = number
                    layout.elm_obj.show()
            parent.window.elm_obj.keyboard_mode_set(ECORE_X_VIRTUAL_KEYBOARD_STATE_OFF)
            if number_layout:
                number_layout.delete()
            if text_layout:
                text_layout.delete()
            parent.restore_orig()    
            ret = "done"
            yield ret
        except Exception, e:
            logger.exception('run')

    def callback(self, *args, **kargs):
        logger.debug('callback %s %s', args, kargs)

    def err_callback(self, *args, **kargs):
        logger.debug('callback %s %s', args, kargs)
