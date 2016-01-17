import os
import signal
import urllib
import subprocess

import miniupnpc


from gi.repository import Nemo, GObject

served_files = {}
start_port = 8000

class ServeFolderExtension(Nemo.MenuProvider, GObject.GObject):
    def __init__(self):
        print 'Serve Folder ', os.getpid()
        # create the object
        self.u = miniupnpc.UPnP()
        #print 'inital(default) values :'
        #print ' discoverdelay', u.discoverdelay
        #print ' lanaddr', u.lanaddr
        #print ' multicastif', u.multicastif
        #print ' minissdpdsocket', u.minissdpdsocket
        self.u.discoverdelay = 200;
        try:
        	print 'Discovering... delay=%u ms' % self.u.discoverdelay
        	ndevices = self.u.discover()
        	print ndevices, 'device(s) detected'
        	# select an igd
        	self.u.selectigd()
        	# display information about the IGD and the internet connection
        	print 'local ip address :', self.u.lanaddr
        	self.externalipaddress = self.u.externalipaddress()
        	print 'external ip address :', self.externalipaddress
        	# print u.statusinfo(), u.connectiontype()
        except Exception, e:
        	print 'Exception :', e

    def _used_ports(self, served_files):
        return sorted([value[1] for value in served_files.values()])

    def _find_port(self, used_ports):
        free_ports = []
        if used_ports:
            all_ports = range(start_port, used_ports[-1]+1)
            free_ports = [port for port in all_ports if port not in used_ports]
            if len(free_ports) < 1:
                free_ports.append(used_ports[-1]+1)
        else:
            free_ports.append(start_port)
        return free_ports[0]

    def _open_process(self, file,opt):
        filename = urllib.unquote(file.get_uri()[7:])
        os.chdir(filename)
#        call = os.system('%s -e "python -m SimpleHTTPServer" &' % terminal)

        # The os.setsid() is passed in the argument preexec_fn so
        # it's run after the fork() and bgnome-terminalefore  exec() to run the shell.
        port = self._find_port(self._used_ports(served_files))
        print port
        cmd = 'python -m SimpleHTTPServer {}'.format(port)
        print cmd
        proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, preexec_fn=os.setsid)
        if opt:
            b = self.u.addportmapping(port, 'TCP', self.u.lanaddr, port,
            	                    'UPnP IGD Tester port %u' % port, '')
            if b:
            	print 'Success. Now waiting for some HTTP request on http://%s:%u' % (self.externalipaddress ,port)
            cmd = 'notify-send "Serving {}" " @ http://{}:{}" -t 5000;'.format(filename,self.externalipaddress, port)
        else:
            cmd = 'notify-send "Serving {}" " @ http://localhost:{}" -t 5000;'.format(filename, port)
        subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, preexec_fn=os.setsid)
        print proc.pid
        served_files[file]=[proc, port]

    def menu_activate_cb(self, menu, file,opt):
        self._open_process(file,opt)

    def menu_activate_cb_2(self, menu, file):
        print 'killing process ', served_files[file][0].pid
        os.killpg(served_files[file][0].pid, signal.SIGTERM)  # Send the signal to all the process groups
        p = self.u.getgenericportmapping(served_files[file][1])
        port = served_files[file][1]
        filename = urllib.unquote(file.get_uri()[7:])
        if p==None:
            pass
        else:
            (port, proto, (ihost,iport), desc, c, d, e) = p
            b = self.u.deleteportmapping(port, proto)
            if b:
                print 'Successfully deleted port mapping'
            else:
                print 'Failed to remove port mapping'
            cmd = 'notify-send "Stopped serving {} " " @ http://{}:{}" -t 5000;'.format(filename,self.externalipaddress,port)
        del served_files[file]
        cmd = 'notify-send "Stopped serving {} " " @ http://localhost:{}" -t 5000;'.format(filename,port)
        subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, preexec_fn=os.setsid)

    def menu_background_activate_cb(self, menu, file,opt):
        self._open_process(file,opt)

    def get_file_items(self, window, files):
        if len(files) != 1:
            return

        file = files[0]
        if not file.is_directory() or file.get_uri_scheme() != 'file':
            return

        menuitem = Nemo.MenuItem(name='NemoPython::serve_file_item',
                                 label='Serve directory',
                                 tip='Serve the contents of the folder locally or globally on the network')
        submenu = Nemo.Menu()
        menuitem.set_submenu(submenu)
        if file not in served_files:
            item = Nemo.MenuItem(name='NemoPython::serve_file_item0',
                                     label='Serve locally...' ,
                                     tip='Serve %s locally' % file.get_name())
            item.connect('activate', self.menu_activate_cb, file, 0)
            submenu.append_item(item)
            item = Nemo.MenuItem(name='NemoPython::serve_file_item1',
                                     label='Serve globally...' ,
                                     tip='Serve %s globally' % file.get_name())
            item.connect('activate', self.menu_activate_cb, file,1)
            submenu.append_item(item)
        else:
            item = Nemo.MenuItem(name='NemoPython::serve_file_item0',
                                     label='Stop serving...' ,
                                     tip='Open Terminal In %s' % file.get_name())
            item.connect('activate', self.menu_activate_cb_2, file)
            submenu.append_item(item)
        return menuitem,

    def get_background_items(self, window, file):
        item = Nemo.MenuItem(name='NemoPython::serve_item',
                                 label='Serve Here',
                                 tip='Open Terminal In This Directory')
        item.connect('activate', self.menu_background_activate_cb, file,0)
        return item,
