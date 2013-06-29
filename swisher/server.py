
import notifier
import web
import cardmanager
import cards
import mpdsource
import mpdplayer
import actions
import shell
import cherrypy
import logging
import radiosource
import jamendo
import yaml
import sys

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

def createMpdController(current_dir, config, extra_pages):
    mpdhost = config.get("mpd-host", "localhost")
    mpdport = config.get("mpd-port", 6600)
    httpport = config.get("http-port", 3344)
    cardsfile = config.get("cards-file", "cards.txt")
    jamendo_clientid = config.get("jamendo-clientid", "")
    jamendo_username = config.get("jamendo-username", "")
    use_card_service = config.get("use-card-service", False)
    log = config.get("log", False)

    notifierx = notifier.Notifier()
    mpdplayerx = mpdplayer.MpdPlayer(mpdhost, mpdport, notifierx.notify)
    mpdsourcex = mpdsource.MpdSource(mpdplayerx.client)
    radiosx = radiosource.RadioSource(mpdplayerx)
    shellx = shell.Shell()

    pages = extra_pages + [
        ("Mpd", lambda c: mpdsource.SearchPage(c, mpdsourcex)),
        ("Playlists", lambda c: mpdsource.PlaylistPage(c, mpdsourcex)),
        ("Radio", lambda c: radiosource.RadioPage(c, radiosx)),
    ]
    handlers = mpdsourcex.handlers() + [radiosx.play_radio]
    enrichers = [mpdsourcex.enrich_track]
    if jamendo_clientid:
        jamapi = jamendo.JamendoApi(jamendo_clientid)
        handler = jamendo.JamendoActionHandler(self.mpdplayer, jamapi)
        pages += [
            ("Jamendo Search", lambda c: jamendo.SearchPage(c, jamapi)),
            ("Jamendo Radio", lambda c: jamendo.RadioPage(c, jamapi)),
            ("Jamendo Likes", lambda c: jamendo.LikesPage(c, jamapi, jamendo_username)),
        ]
        handlers += handler.handlers()
        enrichers += handler.enrichers()

    actions = mpdplayerx.actions() + shellx.actions()
    services = [ mpdplayerx ] 
    instance = Server(current_dir, cardsfile, log, httpport, notifierx,
      use_card_service, handlers, enrichers, actions, pages, services)
    return instance
        
class Server:
    def __init__(self, resources_path, cardsfile, log, http_port, notifierx, use_cardservice, handlers, enrichers, actionsx, pages, services):
        self.notifier = notifierx
        self.cardstore = cards.CardStore(cardsfile, use_cardservice)
        self.services = services
        self._swisher_dir = resources_path

        self.actions = actions.Actions(self.cardstore, 
          handlers,
          enrichers,
          actionsx
        )
        self.cardmanager = cardmanager.CardManager(self.cardstore, self.actions, self.notifier.notify)

        pages += [
            ("Cards", lambda c: web.CardsPage(c, self.cardstore)),
            ("Actions", lambda c: actions.ActionsPage(c, self.actions)),
        ]
        self.web = web.Web(resources_path, log, http_port, ["box-functions.js"], pages)
        self.web.root.longPoll = web.LongPollStatus(self.notifier)
        self.web.root.action = web.ActionPage(self.actions, self.cardmanager)
        self.web.root.action.exposed = True

    def swisher_dir(self):
        return self._swisher_dir
    def start(self):
        self.web.start()
        for service in self.services:
            service.start()
    def stop(self):
        cherrypy.log("Stopping swisher", severity=logging.INFO)
        self.notifier.stop()
        self.web.stop()
        for service in self.services:
            service.stop()
