import win32com.client
import cherrypy
import pykka
import pythoncom
import threading
import time

def create_factory(config):
    def create_itunes(notifier):
        return ITunesPlayer()
    return create_itunes

class ITunesPlayer:
    def __init__(self): pass
    def shutdown(self): self.ref.stop()
    def pause(self): self.proxy.pause_play()
    def stop(self): self.proxy.stop()
    def next(self): self.proxy.next()
    def previous(self): self.proxy.previous()
    def script_files(self): return []
    def enrichers(self): return []
    def pages(self): return [("iTunes", lambda c: ITunesPage(c, self))]
    def start(self):
        actor = ITunesController()
        self.actor_ref = actor.start()
        self.proxy = self.actor_ref.proxy()
    def shutdown(self): self.actor_ref.stop()
    def handlers(self): return [self._handle_track, self._handle_playlist]
    def actions(self): return []
    
    def playlists(self): return self.proxy.playlists().get()
    def search_tracks(self, text): return self.proxy.search_tracks(text).get()
    def selected_tracks(self): return self.proxy.selected_tracks().get()
    def play_track(self, track_id): return self.proxy.play_track(track_id).get()
    def play_playlist(self, playlist_name): return self.proxy.play_playlist(self, playlist_name).get()
    
    def _handle_track(self, value):
        trackidtext = value.get("_trackid")
        if trackidtext:
            trackid = self._parse_trackid(trackidtext)
            self.proxy.play_track(trackid)
        return trackidtext
    def _handle_playlist(self, value):
        playlist_name = value.get("_itunes_playlist_name")
        if playlist_name:
            self.proxy.play_playlist(playlist_name)
        return playlist_name

    def _parse_trackid(self, text):
        (high, low) = text.split(":")
        return TrackID(high, low)

class ITunesController(pykka.ThreadingActor):
    def __init__(self):
        super(ITunesController, self).__init__()
    def on_start(self):
        pythoncom.CoInitialize()
        self.iTunes = win32com.client.gencache.EnsureDispatch("iTunes.Application")
    def pause_play(self): self.iTunes.PlayPause()
    def stop(self): self.iTunes.Stop()
    def next(self): self.iTunes.NextTrack()
    def previous(self): self.iTunes.BackTrack()
    def search_tracks(self, text):
        return self._create_tracks(self.iTunes.LibraryPlaylist.Search(text, 1))
    def selected_tracks(self):
        return self._create_tracks(self.iTunes.SelectedTracks)
    def playlists(self):
        r = []
        for playlist in self.iTunes.Sources(1).Playlists:
            r.append(ITunesPlaylist(playlist.Name))
        return r
    def play_track(self, track_id):
        track = self.iTunes.LibraryPlaylist.Tracks.ItemByPersistentID(track_id.high, track_id.low)
        if track:
            self.iTunes.Pause() #if the requested track is already play is ignored but we want it to start again
            track.Play()
    def play_playlist(self, playlist_name):
        for playlist in self.iTunes.Sources(1).Playlists:
            if playlist.Name == playlist_name:
                playlist.PlayFirstTrack()
    def _create_tracks(self, tracks):
        result = []
        for track in (tracks or []):
            result.append(ITunesTrack(track.Name, track.Album, track.Artist,
              TrackID(
                self.iTunes.ITObjectPersistentIDHigh(track),
                self.iTunes.ITObjectPersistentIDLow(track))
            ))
        return result
 
class ITunesTrack:
    def __init__(self, name, album, artist, id):
        self._name = name
        self._album = album
        self._artist = artist
        self._id = id
    def artist(self): return self._artist
    def value(self):
        return { "_trackid": self._id.text(), "track_name": self._name, "artist": self._artist }
    def shortname(self):
        return self._name
    def longname(self):
        return self._name + " (" + self._artist + ")"
    def children(self):
        return []

class ITunesPlaylist:
    def __init__(self, playlist_name):
        self._playlist_name = playlist_name
    def value(self):
        return { "_itunes_playlist_name": self._playlist_name }
    def shortname(self):
        return self._playlist_name
    def longname(self):
        return self._playlist_name
    def children(self):
        return []
class TrackID:
    def __init__(self, high, low):
        self.high = high
        self.low = low
    def text(self): return str(self.high) + ":" + str(self.low)

class ITunesPage:
    def __init__(self, context, player):
        self._context = context
        self._player = player

    @cherrypy.expose
    def index(self, search=""):
        results = []
        print "search", search
        if search == "":
            selected = self._player.selected_tracks()
            playlists = self._player.playlists()
            return self._context.render("itunes-home.html", "iTunes", selected=selected, playlists=playlists)
        else:
            results =  self._player.search_tracks(search)
            return self._context.render("itunes-search.html", "iTunes", search=search, results=results, )
        
def main():
    import thread
    import time
    player = ITunesPlayer()
    player.start()
    time.sleep(1)
    def go():
        print "go", threading.current_thread()
        #import pythoncom
        #pythoncom.CoInitialize()
        for p in player.playlists():
            print p.playlist_name
    thread.start_new_thread(go, ())
    time.sleep(5)
    player.shutdown()
#main()
#player = ITunesPlayer()
#for p in player.playlists():
#    print p.playlist_name
##player.play_playlist("pepper")
#for t in player.search_tracks("christmas"):
#    print t._id
#track = player.play_track( TrackID(-773375687, -2107655760) )

#for s in iTunes.Sources:
#    p = iTunes.LibraryPlaylist.Playlists()
    
#for t in r:
#    print t.Name
#    print t.Album
#    print t.Artist
#    print t.Time
    #t.Play()
    #print iTunes.ITObjectPersistentIDHigh(t)
    #print iTunes.ITObjectPersistentIDLow(t)
    #x = iTunes.ItemByPersistentID(iTunes.ITObjectPersistentIDLow(t), iTunes.ITObjectPersistentIDHigh(t))
    #print x
    
#t[0].Play()