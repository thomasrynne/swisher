import cherrypy

from ws4py.server.cherrypyserver import WebSocketPlugin, WebSocketTool
from ws4py.websocket import WebSocket
from ws4py.messaging import TextMessage
import actions
import json

def create_factory(config):
    def create(notify_function):
        return WebControl()
    return create

class WebControl:
    def __init__(self):
        self.connections = WebSocketConnections()

    def handlers(self): return [ self.play_youtube_handler ]
    def actions(self): return []
    def enrichers(self): return []
    def script_files(self): return ["jQuery.tubeplayer.min.js", "webplayer.js"]
    def pages(self): return [("YouTube", lambda c: YouTubeSearchPage(c))]
    def start(self): pass
    def shutdown(self): pass
    def stop(self): self.connections.send_to_active({"action": "stop"})
    def pause(self):
        print "Sending pause"
        self.connections.send_to_active({"action": "pause"})
    def play_youtube_handler(self, value):
        videoid = value.get("youtube_video")
        if videoid:
            self.connections.send_to_active({ "play_youtube": videoid })
        return videoid

class Page:
    @cherrypy.expose
    def index(self):
        pass


class CardReaderHandler(WebSocket):
    def __init__(self, connections, handler_id, sock, protocols, extensions, environ):
        WebSocket.__init__(self, sock, protocols, extensions, environ)
        self.connections = connections
        self.handler_id = handler_id

    def received_message(self, m):
        print "'"+m.data+"'"
        if m.data == "MAKEACTIVE":
            self.connections.make_active(self)
    def opened(self):
        self.connections.add(self)
    def closed(self, code, reason="No reason"):
        self.connections.remove(self)
    def bye(self):
        self.send("REPLACED")
    def hello(self):
        self.send("ACTIVE")


class WebSocketConnections:

    def __init__(self):
        self.sequence = 0
        self.handlers = {}
        self.active = None

    def handler_builder(self, sock, protocols=None, extensions=None, environ=None):
        hid = self.sequence
        self.sequence = self.sequence + 1
        return CardReaderHandler(self, hid, sock, protocols, extensions, environ)

    def add(self, handler):
        self.handlers[handler.handler_id] = handler
        if len(self.handlers) == 1:
            self.active = handler
            self.active.hello()
        self.pingAll()

    def remove(self, handler):
        del self.handlers[handler.handler_id]
        if self.active.handler_id == handler.handler_id and len(self.handlers) > 0:
            self.active = self.handlers[self.handlers.keys()[0]]
            self.active.hello()
            
    def make_active(self, handler):
        self.active.bye()
        self.active = handler
        self.active.hello()

    def pingAll(self):
        for handler in self.handlers.values()[:]:
            handler.send("PING")

    def send_to_active(self, message):
        if self.active:
            print message
            self.active.send(json.dumps(message))
        else:
            pass #need to launch webpage and wait for websocket connection


class YouTubeSearchPage:
  def __init__(self, context):
    self.context = context
  @cherrypy.expose
  def index(self, search=""):
    
    v = search.find("v=")
    videoid = None
    if v > 0:
        videoid = search[v+2:]
    return self.context.render("youtube.html", "You Tube", videoid=videoid)

