import mpd
import urllib
import thread
import threading
import signal
import time
import logging
import traceback
import cherrypy
import json

class MpdSource:
    def __init__(self, client):
        self._client = client

    def handlers(self): return [self.handle_mpd_uri, self.handle_mpd_album, self.handle_mpd_playlist]
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
            songs = self._client.search("title", track_name, "artist", artist)
            if len(songs) > 0:
                return {"_mpd_uri": songs[0]["file"]}
        return False

    def search_titles(self, text):
        for song in self._client.search("title", text):
            yield TrackAction(song["file"], song["title"], song.get("artist", ""), song.get("time"))
    def search_albums(self, text):
        albums = {}
        for song in self._client.search("album", text):
            album = song["album"]
            if album != "":
                key = (song["artist"], album)
                if key not in albums:
                    albums[key] = []
                albums[key].append(TrackAction(
                  song["file"], song.get("title", "??"),
                  song.get("artist", ""), song.get("time")))
        for key, tracks in albums.items():
            (artist, album) = key
            yield AlbumAction(artist, album, tracks)

    def albums(self):
        self._client.albums()

    def playlists(self):
        for entry in self._client.listplaylists():
            name = entry["playlist"]
            yield ( { "_mpd_playlist": name}, name, name )

    def _play_track(self, track_url):
        self._client.clear()
        self._client.add(track_url)
        self._client.play()

    def _play_album(self, album_key):
        (artist, album) = album_key.split("/")
        self._client.clear()
        for song in self._client.find("artist", artist, "album", album):
            self._client.add(song["file"])
        self._client.play()

    def _play_playlist(self, name):
        self._client.clear()
        self._client.load(name)
        self._client.play()

class TrackAction():
    def __init__(self, url, track, artist, duration):
        self._url = url
        self._track = track
        self._artist = artist
        self._duration = duration
    def value(self):
        return { "_mpd_uri": self._url, "track_name": self._track, "artist": self._artist, "duration":self._duration }
    def shortname(self):
        return self._track
    def longname(self):
        return self._track + " (" + self._artist + ")"
    def children(self):
        return []

class AlbumAction():
    def __init__(self, artist, title, tracks):
        self._artist = artist
        self._title = title
        self._tracks = tracks
    def value(self):
        return {"artist": self._artist, "album":self._title, "_mpd_album": self._artist + "/" + self._title}
    def shortname(self):
        return self._title
    def longname(self):
        return self._title + " (" + self._artist + ")"
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


