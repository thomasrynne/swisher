import mpd
import urllib
import thread
import threading
import signal
import time
import logging
import traceback
import cherrypy
import actions

#Registers stop/pause/.. actions and keeps the mpd status up to date
#Also exposes the play method for other classes
class MpdPlayer:
    def __init__(self, host, port, notify):
        self.host = host
        self.port = port
        self.notify = notify
        self.notification = mpd.MPDClient(use_unicode=True)
        self.notification.timeout = 15
        self.notification.idletimeout = 60
        self.client = mpd.MPDClient(use_unicode=True)
        self.client.timeout = 15
        self.cancel_connect = threading.Event()

    def start(self):
        self.cancel_connect.clear()
        def _current_status():
            song = self.notification.currentsong()
            status = self.notification.status()
            if status['state'] == 'stop':
                return "Stopped"
            elif status['state'] == 'pause':
                return "Paused"
            else:
                return song.get("title", "")
        def _keep_connected():
           retry_count = 0
           while not self.cancel_connect.is_set(): #reconnect loop
               try:
                   self.notification.connect(self.host, self.port)
                   self.client.connect(self.host, self.port)
                   retry_count = 0
                   latest_status = ""
                   while not self.cancel_connect.is_set(): #status loop
                       current_status = _current_status()
                       if latest_status != current_status:
                           latest_status = current_status
                           self.notify("mpd", latest_status)
                       try:
                           response = self.notification.idle()
                       except:
                           pass
               except: #connect/reconnect failed
                   #print traceback.format_exc()
                   pass
               #close connections to get in a consistent state
               try:
                   self.notification.disconnect()
               except:
                   pass
               try:
                   self.client.disconnect()
               except:
                   pass
               if retry_count == 1: #Allow one retry before assuming MPD is down
                   self.notify("mpd", "No MPD")
               self.cancel_connect.wait(min(retry_count*3,20)) #reconnect inverval
               retry_count = retry_count + 1
        thread.start_new_thread(_keep_connected, ())
    def stop(self):
        self.cancel_connect.set()
        self.notification.noidle()

    def actions(self):
        return [
          actions.Action("Stop", "stop", self.client.stop),
          actions.Action("Pause", "pause", self.client.pause),
          actions.Action("Next", "next", self.client.next),
          actions.Action("Previous", "previous", self.client.previous)]

    def play_all(self, urlorpaths):
        self.client.stop()
        self.client.clear()
        for item in urlorpaths:
            self.client.add(item)
        self.client.play()

    def play(self, urlorpath):
        self.play_all([urlorpath])

