import cherrypy
import urllib
import json

class RadioSource:
    def __init__(self, mpdplayer):
        self._mpdplayer = mpdplayer
        self._radiourls = { #hard coded list for now, should find radio stream service
            "bbc4": ("BBC Radio 4", "http://www.bbc.co.uk/radio/listen/live/r4_aaclca.pls"),
            "bbcws": ("BBC World Service", "http://www.bbc.co.uk/worldservice/meta/tx/nb/live/eneuk.pls"),
            "bbc5": ("BBC 5 Live", "http://www.bbc.co.uk/radio/listen/live/r5l_aaclca.pls"),
            "magic": ("Magic", "http://tx.whatson.com/icecast.php?i=magic1054.mp3.m3u"),
            "heart": ("Heart", "http://media-ice.musicradio.com/HeartLondonMP3.m3u"),
            "jazzfm": ("Jazz FM", "http://listen.onmyradio.net:8002/listen.pls")
        }

    def radios(self):
        for code, value in self._radiourls.items():
            yield ({"swisher_radio": code}, value[0], value[0])

    def play_radio(self, value):
        radio_code = value.get("swisher_radio")
        if radio_code:
            self._play_radio(radio_code)
        return radio_code

    def _play_radio(self, code):
        url = self._radiourls [code][1]
        m3u = False

        if url.endswith(".m3u"):
            m3u = urllib.urlopen(url).read().strip()
        elif url.endswith(".pls"):
            for line in urllib.urlopen(url):
                if line.startswith("File1="):
                    m3u = line.replace("File1=", "").strip()
        if m3u:
            self._mpdplayer.play(m3u)
        else:
            pass

class RadioPage:
    def __init__(self, context, radio):
        self._context = context
        self._radio = radio
    @cherrypy.expose
    def index(self):
        return self._context.render("list.html","Radio", entries=self._radio.radios())

