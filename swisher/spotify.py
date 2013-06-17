import httplib
import json
import cherrypy
import thread
import urllib

#
#  Text box for search or spotify uri
#  List matches with Z maybe links to album and artist searches
#   (album would list tracks, not sure about artist, maybe just albums)
#  also add offset support

class SpotifyDesktop:
    def __init__(self):
        pass
    def play(self, uri):
        #execute spotify.exe --uri " + uri
    def pause(self):
        pass
    def next(self):
        pass
    def previous(self):
        pass
    def _send_key(self, key):
        pass

#Adds actions for the Spotify uris
class JamendoActionHandler:
    def __init__(self, player, actions, jamapi):
        actions.register("spotify", self.play_uri)

    def play_uri(self, uri):
        pass

class SpotifyApi:
    def __init__(self):
        pass

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
        connection = httplib.HTTPConnection("ws.spotify.com")
        url = "/" + path + "?" + "".join(["&"+name+"="+str(value).replace(" ", "+") for name, value in params.items()])
        connection.request("GET", url)
        response = connection.getresponse()
        data = response.read()
        j = json.loads(data)
        connection.close()
        return j

class SpotifyPage:
  def __init__(self, context, spotifyapi):
    self.context = context
    self.spotifyapi = spotifyapi
  @cherrypy.expose
  def index(self, q=""):
    return self.context.render("spotify.html", "Spotify", self.spotifyapi.search(q))


