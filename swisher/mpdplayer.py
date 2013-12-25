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

def create_factory(config): 
    mpdhost = config.get("mpd-host", "127.0.0.1")
    mpdport = config.get("mpd-port", 6600)
    #jamendo_clientid = config.get("jamendo-clientid", "")
    #jamendo_username = config.get("jamendo-username", "")
    def create(notifier_function):
        return MpdPlayer(mpdhost, mpdport, notifier_function)
    return create

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

    def script_files(self): return ["box-functions.js"]
    def pages(self):
        return [
          ("Files", lambda c: SearchPage(c, self)),
          ("Playlists", lambda c: PlaylistPage(c, self)),
        ]

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

    def shutdown(self):
        self.cancel_connect.set()
        try:
            self.notification.noidle()
        except:
            pass

    def stop(self): self.client.next()
    def pause(self): self.client.pause()

    def actions(self):
        return [
          actions.Action("Next", "next", self.client.next),
          actions.Action("Previous", "previous", self.client.previous),
          actions.Action("Update", "update", self.client.update),
          actions.Action("Rescan", "rescan", self.client.rescan),
        ]
    def enrichers(self): return [ self.enrich_track ]

    def play_all(self, urlorpaths):
        self.client.stop()
        self.client.clear()
        for item in urlorpaths:
            self.client.add(item)
        self.client.play()

    def play(self, urlorpath):
        self.play_all([urlorpath])

    def handlers(self):
        return [
          self.handle_mpd_uri, self.handle_mpd_album, self.handle_mpd_playlist
        ]
    def handle_mpd_uri(self, value):
        mpduri = value.get("_mpd_uri")
        if mpduri:
            self._play_track(mpduri)
        print("PLAY ", mpduri, value)
        return mpduri
    def handle_mpd_album(self, value):
        albumkey = value.get("_mpd_album")
        if albumkey:
            self._play_album(albumkey)
        return albumkey
    def handle_mpd_playlist(self, value):
        playlist = value.get("_mpd_playlist")
        if playlist:
            self._play_playlist(playlist)
        return playlist

    def enrich_track(self, value):
        (track_name, artist) = (value.get("track_name"), value.get("artist"))
        if track_name and artist:
            songs = self.client.search("title", track_name, "artist", artist)
            if len(songs) > 0:
                return {"_mpd_uri": songs[0]["file"]}
        return False

    def search_titles(self, text):
        for song in self.client.search("title", text):
            yield TrackAction(song["file"], song["title"], song.get("artist", ""), song.get("time"))
    def search_albums(self, text):
        albums = {}
        for song in self.client.search("album", text):
            album = song["album"]
            if album != "":
                if album not in albums:
                    albums[album] = []
                albums[album].append(TrackAction(
                  song["file"], song.get("title", "??"),
                  song.get("artist", ""), song.get("time")))
        for album, tracks in albums.items():
            yield AlbumAction(album, tracks)

    def albums(self):
        self.client.albums()

    def playlists(self):
        for entry in self.client.listplaylists():
            name = entry["playlist"]
            yield ( { "_mpd_playlist": name}, name, name )

    def _play_track(self, track_url):
        self.client.clear()
        self.client.add(track_url)
        self.client.play()

    def _play_album(self, album_key):
        (artist, album) = album_key.split("/")
        query = ["album", album]
        if artist != "Compilation":
            query += ["artist", artist]
        self.client.clear()
        for song in self.client.find(query):
            self.client.add(song["file"])
        self.client.play()

    def _play_playlist(self, name):
        self.client.clear()
        self.client.load(name)
        self.client.play()

class TrackAction():
    def __init__(self, url, track, artist, duration):
        self._url = url
        self._track = track
        self._artist = artist
        self._duration = duration
    def artist(self): return self._artist
    def value(self):
        return { "_mpd_uri": self._url, "track_name": self._track, "artist": self._artist, "duration":self._duration }
    def shortname(self):
        return self._track
    def longname(self):
        return self._track + " (" + self._artist + ")"
    def children(self):
        return []

class AlbumAction():
    def __init__(self, title, tracks):
        self._title = title
        self._tracks = tracks
    def value(self):
        return {"artist": self.artist(), "album":self._title, "_mpd_album": self.artist() + "/" + self._title}
    def artist(self):
        artists = set([track.artist() for track in self._tracks])
        print artists
        if len(artists) == 1: #perhaps pick the most common artist if < 3?
            return artists.pop()
        else:
            return "Compilation"
    def shortname(self):
        return self._title
    def longname(self):
        return self._title + " [" + self.artist() + "]"
    def children(self):
        return self._tracks

class PlaylistPage:
    def __init__(self, context, mpdsourcex):
        self._context = context
        self._mpdsource = mpdsourcex

    @cherrypy.expose
    def index(self):
        return self._context.render("list.html", "Playlists", entries=self._mpdsource.playlists())

class SearchPage:
    def __init__(self, context, mpdsourcex):
        self._context = context
        self._mpdsource = mpdsourcex

    @cherrypy.expose
    def index(self, search=""):
        results = []
        if search != "":
            for r in self._mpdsource.search_titles(search):
                results.append( r )
            for a in self._mpdsource.search_albums(search):
                results.append( a )
        return self._context.render("search.html", "Search", search=search, results=results)


