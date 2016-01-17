#!/usr/bin/python
# -*- coding: utf-8 -*-

# Licensed under the MIT license
# http://opensource.org/licenses/mit-license.php

# Copyright 2008 Frank Scholz <coherence@beebits.net>

""" Coherence and Nemo bridge to play a file with a DLNA/UPnP MediaRenderer

    usable as Nemo Extension

    for use an extension, copy it to ~/.Nemo/python-extensions
    or for a system-wide installation to /usr/lib/Nemo/extensions-2.0/python

    connection to Coherence is established via DBus

"""
import os
import time

from urllib import unquote
from gi.repository import Nemo, GObject #import nautilus

import dbus
from dbus.mainloop.glib import DBusGMainLoop
DBusGMainLoop(set_as_default=True)
import dbus.service

# dbus defines
BUS_NAME = 'org.Coherence'
OBJECT_PATH = '/org/Coherence'

class CoherencePlayExtension(GObject.GObject, Nemo.MenuProvider):

    def __init__(self):
        print "CoherencePlayExtension", os.getpid()
        self.coherence = None
        try:
            self.init_controlpoint()
        except:
            print "can't setup Coherence connection"

    def init_controlpoint(self):
        self.bus = dbus.SessionBus()
        self.coherence = self.bus.get_object(BUS_NAME,OBJECT_PATH)

    def get_file_items(self, window, files):
        if self.coherence == None:
            return
        if len(files) == 0:
            return

        for file in files:
            if file.is_directory() or file.get_uri_scheme() != 'file':
                return

        #pin = self.coherence.get_pin('Nemo::MediaServer::%d'%os.getpid())
        #print 'Pin:',pin
        #if pin == 'Coherence::Pin::None':
        #    return
        devices = self.coherence.get_devices(dbus_interface=BUS_NAME)
        i=0
        menuitem = None
        for device in devices:
            print device['friendly_name'],device['device_type']
            if device['device_type'].split(':')[3] == 'MediaRenderer':
                if i == 0:
                    menuitem = Nemo.MenuItem(name='CoherencePlayExtension::Play',
                                             label='Play on MediaRenderer',
                                             tip='Play the selected file(s) on a DLNA/UPnP MediaRenderer')
                    submenu = Nemo.Menu()
                    menuitem.set_submenu(submenu)

                item = Nemo.MenuItem(name='CoherencePlayExtension::Play%d' %i,
                                     label=device['friendly_name'], tip='')
                for service in device['services']:
                    service_type = service.split('/')[-1]
                    if service_type == 'AVTransport':
                        item.connect('activate', self.play,service, device['path'], files)
                        break
                submenu.append_item(item)
                i += 1

        if i == 0:
            return

        return menuitem,

    def play(self,menu,service,uuid,files):
        print "play",uuid,service,files
        #pin = self.coherence.get_pin('Nemo::MediaServer::%d'%os.getpid())
        #if pin == 'Coherence::Pin::None':
        #    return
        file = unquote(files[0].get_uri()[7:])
        file = os.path.abspath(file)

        uri = self.coherence.create_oob(file)

        #result = self.coherence.call_plugin(pin,'get_url_by_name',{'name':file})
        #print 'result', result
        print uri

        s = self.bus.get_object(BUS_NAME+'.service',service)
        print s
        s.action('stop','')
        s.action('set_av_transport_uri',{'current_uri':uri})
        s.action('play','')
