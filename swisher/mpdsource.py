import mpd
import urllib
import thread
import threading
import signal
import time
import logging
import traceback
import cherrypy

from actions import ActionRegistry

class Track:
    def __init__(self, key, filename, name):
        self._key = key
        self._filename = filename
        self._name = name
    def prefix(self):
        return "track"
    def name(self):
        return self._name
    def filename(self):
        return self._filename
    def value(self):
        return self._key

class MpdSource:
    def __init__(self, host, port, actions, notify):
        self.host = host
        self.port = port
        self.actions = actions
        self.notify = notify
        self.notification = mpd.MPDClient(use_unicode=True)
        self.notification.timeout = 3
        self.notification.idletimeout = 60
        self.client = mpd.MPDClient(use_unicode=True)
        self.client.timeout = 3
        self.tracks = {}
        self.albums = {}
        self.playlists = []
        self.radiourls = {
            "bbc4": ("BBC Radio 4", "http://www.bbc.co.uk/radio/listen/live/r4_aaclca.pls"),
            "bbcws": ("BBC World Service", "http://www.bbc.co.uk/worldservice/meta/tx/nb/live/eneuk.pls"),
            "bbc5": ("BBC 5 Live", "http://www.bbc.co.uk/radio/listen/live/r5l_aaclca.pls"),
            "magic": ("Magic", "http://tx.whatson.com/icecast.php?i=magic1054.mp3.m3u"),
            "heart": ("Heart", "http://media-ice.musicradio.com/HeartLondonMP3.m3u"),
            "jazzfm": ("Jazz FM", "http://listen.onmyradio.net:8002/listen.pls")
        }
        self.add_static_actions()
        self.cancel_connect = threading.Event()
        self.needs_load = threading.Event()

    def start(self):
        self.cancel_connect.clear()
        self.needs_load.set()
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
        def _do_load():
            while not self.cancel_connect.is_set(): #load loop
                self.needs_load.wait()
                if not self.cancel_connect.is_set():
                    self.load()
                    self.needs_load.clear()

        thread.start_new_thread(_keep_connected, ())
        thread.start_new_thread(_do_load, ())
    def stop(self):
        self.cancel_connect.set()
        self.notification.noidle()

    def load(self):
        tracks = {}
        albums = {}
        connection = mpd.MPDClient(use_unicode=True)
        connection.connect(self.host, self.port)
        library = connection.listallinfo()
        for song in library:
            if 'title' in song:
                track_key = self.clean(song.get('artist',''))+"/"+self.clean(song['title'])
                tracks[track_key] = song
                if 'album' in song and song['album'] != "":
                    key = self.clean(song['album'])
                    if key not in albums:
                        albums[key] = (song['album'], [])
                    name = song['title']
                    if 'track' in song:
                        name = song['track'] + ". " + name
                    albums[key][1].append(Track(track_key,song['file'],name))
        playlists = []
        for playlist in connection.listplaylists():
            playlists.append( playlist["playlist"] )
        connection.disconnect()
        self.tracks = tracks
        self.albums = albums
        self.playlists = playlists
        self.add_database_actions()
        cherrypy.log("MPD tracks, albums & playlists loaded", severity=logging.INFO)

    def clean(self, text):
        return text.replace("'", "_").replace(" ", "_")

    def add_static_actions(self):
        self.actions.register("player", "Actions", self._handle_player,
         [ ActionRegistry("stop","Stop"), ActionRegistry("pause", "Pause"),
           ActionRegistry("next","Next"), ActionRegistry("previous", "Previous") ])
        self.actions.register("mpd", "Actions", self._mpd,
            [ActionRegistry("update", "Update MPD")])
        self.actions.register("volume", "Actions", self._volume,
            [ActionRegistry("high", "Volume High"),ActionRegistry("medium", "Volume Medium"),ActionRegistry("low", " Volume Low")])
        self.actions.register("radio", "Radio", self._radio,
         [ ActionRegistry(code,details[0]) for code,details in self.radiourls.items()])
    def add_database_actions(self):
        def create_children(tracks):
            return [ ActionRegistry(song['title']) for song in tracks]
        self.actions.register("track", "", self._track,
         [ ActionRegistry(key, song['title']) for key,song in self.tracks.items()])
        self.actions.register("album", "Albums", self._album,
         [ ActionRegistry(key,albuminfo[0],albuminfo[1]) for key,albuminfo in self.albums.items()])
        self.actions.register("playlist", "Playlists", self._playlist,
         [ ActionRegistry(name,name) for name in self.playlists])
    def _volume(self,value):
        if value == "high":
            self.client.setvol(100)
        if value == "medium":
            self.client.setvol(60)
        if value == "low":
            self.client.setvol(30)
    def _mpd(self,name):
        if name == "update":
            self.client.update(True) #should block
            self.needs_load.set()
    def _radio(self, code):
        url = self.radiourls[code][1]
        m3u = False

        if url.endswith(".m3u"):
            m3u = urllib.urlopen(url).read().strip()
        elif url.endswith(".pls"):
            for line in urllib.urlopen(url):
                if line.startswith("File1="):
                    m3u = line.replace("File1=", "").strip()
        if m3u:
            self.client.stop()
            self.client.clear()
            self.client.add(m3u)
            self.client.play()
        else:
            pass

    def _track(self, track_key):
        song = self.tracks[track_key]
        self.client.clear()
        self.client.add(song['file'])
        self.client.play()
    def _album(self, album_key):
        self.client.clear()
        for song in self.albums[album_key][1]:
            self.client.add(song.filename())
        self.client.play()
    def _playlist(self, name):
        self.client.clear()
        self.client.load(name)
        self.client.play()

    def _handle_player(self, command):
        if command == "stop":
            self.client.stop()
        if command == "next":
            self.client.next()
        if command == "previous":
            self.client.previous()
        if command == "pause":
            self.client.pause()

if __name__ == "__main__":
    class Actions:
      def register(self,a,b,c,d):
        pass
    def notify(code,text):
        print "NOTIFY " + code +":"+text
    mpdsource = MpdSource("localhost", 6600, Actions(), notify)
    mpdsource.start()
    time.sleep(1)
    for a in mpdsource.client.listplaylists():
        print a
    def signal_handler(signal, frame):
        mpdsource.stop()
    signal.signal(signal.SIGINT, signal_handler)
#    print mpdsource.client.idle()
#    print mpdsource.client.status()
#    print mpdsource.client.currentsong()
    signal.pause()



