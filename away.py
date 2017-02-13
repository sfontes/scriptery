#!/usr/bin/env python3
import dbus
from dbus.mainloop.glib import DBusGMainLoop
import subprocess
import psutil
import gi
gi.require_version('TelepathyGLib', '0.12')
from gi.repository import TelepathyGLib as Tp  # noqa
from gi.repository.GObject import MainLoop  # noqa


class Away:
    def __init__(self):
        DBusGMainLoop(set_as_default=True)
        self.mem = 'ActiveChanged'
        self.dest = 'org.gnome.ScreenSaver'
        self.bus = dbus.SessionBus()
        self.loop = MainLoop()
        self.bus.add_signal_receiver(self.catch, self.mem, self.dest)
        self.paused_before = False

    def is_running(self, name):
        processes = []
        for p in psutil.process_iter():
            try:
                if p.name() == name:
                    processes.append(p)
            except psutil.Error:
                pass
        if processes:
            return True
        else:
            return False

    def catch(self, away):
        am = Tp.AccountManager.dup()
        proxy_new = self.bus.get_object("org.mpris.MediaPlayer2.spotify",
                                        "/org/mpris/MediaPlayer2")
        event_manager = dbus.Interface(proxy_new,
                                       'org.mpris.MediaPlayer2.Player')
        properties_manager = dbus.Interface(proxy_new,
                                            'org.freedesktop.DBus.Properties')
        status = properties_manager.Get('org.mpris.MediaPlayer2.Player',
                                        'PlaybackStatus')

        if away == 1:  # Screensaver turned on
            print('INFO: Screen saver turned ON and Spotify was:'
                  ' {}'.format(status))
            if status == 'Playing':
                self.paused_before = False
                event_manager.PlayPause()
            else:
                self.paused_before = True
            if self.is_running('hexchat'):
                print('INFO: hexchat running, marking as AWAY')
                subprocess.call("hexchat -e -c AWAY", shell=True)
            subprocess.call(
                "ssh cruzseba-laptop.aka.amazon.com 'pmset displaysleepnow'",
                shell=True)
            am.set_all_requested_presences(Tp.ConnectionPresenceType.OFFLINE,
                                           'Offline', "")
        else:  # Screensaver turned off
            print('INFO: Screen saver turned OFF and Spotify was:'
                  ' {}'.format(status))
            if self.is_running('hexchat'):
                print('INFO: hexchat running, marking as BACK')
                subprocess.call("hexchat -e -c BACK", shell=True)
            if status == 'Paused' and not self.paused_before:
                event_manager.PlayPause()
            am.set_all_requested_presences(Tp.ConnectionPresenceType.AVAILABLE,
                                           'Available', "")


Away().loop.run()
