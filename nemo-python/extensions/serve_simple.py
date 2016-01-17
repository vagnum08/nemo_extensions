# This example is contributed by Martin Enlund
import os
import signal
import urllib
import subprocess

from gi.repository import Nemo, GObject

served_files = {}
start_port = 8000

class ServeFolderExtension(Nemo.MenuProvider, GObject.GObject):
    def __init__(self):
        print 'Serve Folder ', os.getpid()
        pass

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

    def _open_process(self, file):
        filename = urllib.unquote(file.get_uri()[7:])
        os.chdir(filename)
#        call = os.system('%s -e "python -m SimpleHTTPServer" &' % terminal)

        # The os.setsid() is passed in the argument preexec_fn so
        # it's run after the fork() and bgnome-terminalefore  exec() to run the shell.
        port = self._find_port(self._used_ports(served_files))
        cmd = 'python -m SimpleHTTPServer {}'.format(port)
        print cmd
        proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, preexec_fn=os.setsid)
        cmd = 'notify-send "Serving {}" " @ http://localhost:{}" -t 5000;'.format(filename, port)
        subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, preexec_fn=os.setsid)
        print proc.pid
        served_files[file]=[proc, port]

    def menu_activate_cb(self, menu, file):
        self._open_process(file)

    def menu_activate_cb_2(self, menu, file):
        print 'killing process ', served_files[file][0].pid
        os.killpg(served_files[file][0].pid, signal.SIGTERM)  # Send the signal to all the process groups
        del served_files[file]

    def menu_background_activate_cb(self, menu, file):
        self._open_process(file)

    def get_file_items(self, window, files):
        if len(files) != 1:
            return

        file = files[0]
        if not file.is_directory() or file.get_uri_scheme() != 'file':
            return

        if file not in served_files:
            item = Nemo.MenuItem(name='NemoPython::serve_file_item',
                                     label='Serve folder' ,
                                     tip='Serve %s' % file.get_name())
            item.connect('activate', self.menu_activate_cb, file)
        else:
            item = Nemo.MenuItem(name='NemoPython::serve_file_item',
                                     label='Stop serving' ,
                                     tip='Open Terminal In %s' % file.get_name())
            item.connect('activate', self.menu_activate_cb_2, file)

        return item,

    def get_background_items(self, window, file):
        item = Nemo.MenuItem(name='NemoPython::serve_item',
                                 label='Serve Here',
                                 tip='Open Terminal In This Directory')
        item.connect('activate', self.menu_background_activate_cb, file)
        return item,
