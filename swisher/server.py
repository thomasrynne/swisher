
import notifier
import web
import cardmanager
import cards
import mpdplayer
import actions
import shell
import cherrypy
import logging
import radiosource
import jamendo
import yaml
import sys
from ws4py.server.cherrypyserver import WebSocketPlugin, WebSocketTool
from ws4py.websocket import WebSocket

class Logger(object):
    def __init__(self, file):
        self.terminal = sys.stdout
        self.log = file

    def write(self, message):
        self.terminal.write(message)
        self.log.write(message)

def load_config(config_file):
    try:
        return yaml.load(file(config_file)) or {}
    except IOError:
        return {}

def create_server(current_dir, config, player_factories):
    httpport = config.get("http-port", 3344)
    cardsfile = config.get("cards-file", "cards.txt")
    use_card_service = config.get("use-card-service", False)
    log = config.get("log", False)

    notifierx = notifier.Notifier()
    players = []
    for factory in player_factories:
        try:
            players += [factory(notifierx.notify)]
        except:
            print "Not starting player: " + str(factory)
    return Server(
      current_dir, cardsfile, log, httpport, notifierx,
      use_card_service, players)
        
class Server:
    def __init__(self,
       resources_path, cardsfile, log, http_port,
       notifierx, use_cardservice, players):
        self.notifier = notifierx
        self.cardstore = cards.CardStore(cardsfile, use_cardservice)
        self._swisher_dir = resources_path
        self.players = players
        self.actions = actions.Actions(self.cardstore, players, [])
        self.cardmanager = cardmanager.CardManager(self.cardstore, self.actions, self.notifier.notify)
        pages = []
        for player in players: pages += player.pages()
        pages += [
            ("Cards", lambda c: web.CardsPage(c, self.cardstore)),
            ("Actions", lambda c: actions.ActionsPage(c, self.actions)),
        ]

        script_files = []
        for p in players: script_files += p.script_files()
        self.web = web.Web(resources_path, log, http_port, script_files, "webplayer.html", pages)
        webcontrolx = players[0] #hack to get the web control player as this depends on websockets setup here
        WebSocketPlugin(cherrypy.engine).subscribe()
        cherrypy.tools.websocket = WebSocketTool()
        self.web.config.update({'/webcontrol': {
            'tools.websocket.on': True,
            'tools.websocket.handler_cls': webcontrolx.connections.handler_builder
        }})
        self.web.root.longPoll = web.LongPollStatus(self.notifier)
        self.web.root.action = web.ActionPage(self.actions, self.cardmanager)
        self.web.root.action.exposed = True

    def swisher_dir(self):
        return self._swisher_dir
    def start(self):
        self.web.start()
        for player in self.players:
            player.start()
    def stop(self):
        cherrypy.log("Stopping swisher", severity=logging.INFO)
        self.notifier.stop()
        self.web.stop()
        for player in self.players:
            player.shutdown()
