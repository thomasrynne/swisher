import httplib
import json
import cherrypy
import thread
import urllib

#Adds actions for the Jamendo radio stations and tracks
class JamendoActionHandler:
    def __init__(self, player, actions, jamapi):
        actions.register("jamendo-radio", self.play_radio)
        actions.register("jamendo-track", self.play_track)
        actions.register("jamendo-album", self.play_album)
        self.player = player
        self.jamapi = jamapi

    def play_radio(self, code):
        stream = self.jamapi.request("radios/stream", name=code)[0]["stream"]
        self.player.play(stream)

    def play_track(self, trackid):
        self.player.play(self.jamapi.track_url(trackid))

    def play_album(self, albumid):
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
            yield (entry["name"], entry["dispname"])

    def list_mytracks(self, username):
        userid = self.requestOne("users", name=username)["id"]
        result = self.request("users/tracks", id=userid, limit=50)
        artist_cache = {}
        def artist_name(artistid):
            if artistid not in artist_cache:
                artist_cache[artistid] = self.request("artists", id=artistid)[0]["name"]
            return artist_cache[artistid]
        for r in result[0]["tracks"]:
            trackname = r["name"]
            trackid = r["id"]
            artistid = r["artist_id"]
            artist = artist_name(artistid)
            yield (trackid, trackname, artist)

    def track_search(self, text):
        if text != "":
            for track in self.request("tracks", namesearch=text, order="popularity_total", limit=30):
                yield (track["id"], track["name"], track["artist_name"]) 	
    def album_search(self, text):
        if text != "":
            for album in self.request("albums", namesearch=text, order="popularity_total", limit=30):
                yield (album["id"], album["name"], album["artist_name"]) 	

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


