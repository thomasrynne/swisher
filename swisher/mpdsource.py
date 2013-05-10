import mpd
import urllib
import thread
import threading
import signal
import time
import logging
import traceback
import cherrypy

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
    def __init__(self, actions, client):
        actions.register("track", self._play_track)
        actions.register("album", self._play_album)
        self._client = client

    def search_titles(self, text):
        for song in self._client.search("title", text):
            yield TrackAction(song["file"], song["title"], song.get("artist", ""))
    def search_albums(self, text):
        albums = {}
        for song in self._client.search("album", text):
            album = song["album"]
            if album != "":
                key = (song["artist"], album)
                if key not in albums:
                    albums[key] = []
                albums[key].append(TrackAction(song["file"], song.get("title", "??"), song.get("artist", "")))
        for key, tracks in albums.items():
            (artist, album) = key
            yield AlbumAction(artist, album, tracks)

    def albums(self):
        self._client.albums()

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

    def _playlist(self, name):
        self._client.clear()
        self._client.load(name)
        self._client.play()

class TrackAction():
    def __init__(self, url, track, artist):
        self._url = url
        self._track = track
        self._artist = artist
    def prefix(self):
        return "track"
    def code(self):
        return self._url
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
    def prefix(self):
        return "album"
    def code(self):
        return self._artist + "/" + self._title
    def shortname(self):
        return self._title
    def longname(self):
        return self._title + " (" + self._artist + ")"
    def children(self):
        return self._tracks
	
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


