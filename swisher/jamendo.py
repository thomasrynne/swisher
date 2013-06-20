import httplib
import json
import cherrypy
import thread
import urllib

#Adds actions for the Jamendo radio stations and tracks
class JamendoActionHandler:
    def __init__(self, player, jamapi):
        self.player = player
        self.jamapi = jamapi

    def handlers(self): return [self.play_track, self.play_album, self.play_radio]
    def enrichers(self): return [self.enrich_track]

    def play_track(self, value):
        jamendo_track = value.get("jamendo_track")
        if jamendo_track:
            self._play_track(jamendo_track)
        return jamendo_track
    def play_album(self, value):
        jamendo_album = value.get("jamendo_album")
        if jamendo_album:
            self._play_album(jamendo_album)
        return jamendo_album
    def play_radio(self, value):
        radio = value.get("jamendo_radio")
        if radio:
            self._play_radio(radio)
        return radio

    def enrich_track(self, value):
        (track_name, artist) = (value.get("track_name"), value.get("artist"))
        if track_name and artist:
            trackids = track_title_artist_search
            if len(trackids) > 0:
                return {"jamendo_track": tracks[0]}
        return False

    def _play_radio(self, code):
        stream = self.jamapi.request("radios/stream", name=code)[0]["stream"]
        self.player.play(stream)

    def _play_track(self, trackid):
        self.player.play(self.jamapi.track_url(trackid))

    def _play_album(self, albumid):
        track_urls = []
        for track in self.jamapi.requestOne("albums/tracks", id=albumid)["tracks"]:
            track_urls.append( self.jamapi.track_url(track["id"]) )
        self.player.play_all(track_urls)


class JamendoApi:
    def __init__(self, clientID):
        self.clientID = clientID

    def track_url(self, trackid):
        return "http://api.jamendo.com/v3.0/tracks/file?client_id=" + self.clientID + "&id=" + trackid

    def list_radios(self):
        result = self.request("radios")
        for entry in result:
            yield ({"jamendo_radio": entry["name"]}, entry["dispname"])

    def list_mytracks(self, username):
        userid = self.requestOne("users", name=username)["id"]
        result = self.request("users/tracks", id=userid, limit=50)
        artist_cache = {}
        def artist_name(artistid):
            if artistid not in artist_cache:
                artist_cache[artistid] = self.request("artists", id=artistid)[0]["name"]
            return artist_cache[artistid]
        for r in result[0]["tracks"]:
            artistid = r["artist_id"]
            artist = artist_name(artistid)
            yield self._track_tuple(r["id"], r["name"], artist)

    def _track_tuple(self, trackid, trackname, artist):
        return ({"jamendo_track":trackid, "track_name": trackname, "artist":artist},
              trackname, trackname + " [" + artist +"]")

    def track_title_artist_search(self, title, artist):
        for track in self.request("tracks", name=title, artist_name=artist, order="popularity_total", limit=30):
            yield track["id"]

    def track_search(self, text):
        if text != "":
            for track in self.request("tracks", namesearch=text, order="popularity_total", limit=30):
                yield self._track_tuple(track["id"], track["name"], track["artist_name"])
    def album_search(self, text):
        if text != "":
            for album in self.request("albums", namesearch=text, order="popularity_total", limit=30):
                yield ({"jamendo_album": album["id"], "album": album["name"], "artist": album["artist_name"]},
                          album["name"], album["name"] + " [" + album["artist_name"] + "]")

    def requestOne(self, path, **params):
        return self.request(path, **params)[0]

    def request(self, path, **params):
        connection = httplib.HTTPConnection("api.jamendo.com")
        url = "/v3.0/" + path + "?client_id=" + self.clientID + "&format=json" + "".join(
          ["&"+name+"="+str(value).replace(" ", "+") for name, value in params.items()])
        connection.request("GET", url)
        response = connection.getresponse()
        data = response.read()
        j = json.loads(data)
        connection.close()
        results = j["results"]
        return results

class RadioPage:
  def __init__(self, context, jamendo):
    self.context = context
    self.jamendo = jamendo
  @cherrypy.expose
  def index(self):
    return self.context.render("jamendo-radio.html", "Jamendo Radio",
        radios=self.jamendo.list_radios())

class LikesPage:
  def __init__(self, context, jamendo, default_user):
    self.context = context
    self.jamendo = jamendo
    self.default_user = default_user
  @cherrypy.expose
  def index(self, username=""):
    if username=="":
        username = self.default_user
    if username=="":
        mytracks = []
    else:
        mytracks = self.jamendo.list_mytracks(username)
    return self.context.render("jamendo-likes.html", "Jamendo Likes", tracks=mytracks, username=username)

class SearchPage:
  def __init__(self, context, jamendo):
    self.context = context
    self.jamendo = jamendo
  @cherrypy.expose
  def index(self, search=""):
    return self.context.render("jamendo-search.html", "Jamendo Search",
        search=search, tracks=self.jamendo.track_search(search), albums=self.jamendo.album_search(search))


