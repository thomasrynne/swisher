
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

def load_config(config_file):
    try:
        return yaml.load(file(config_file)) or {}
    except IOError:
        return {}

def create(current_dir, config, extra_pages):
    mpdhost = config.get("mpd-host", "localhost")
    mpdport = config.get("mpd-port", 6600)
    httpport = config.get("http-port", 3344)
    cardsfile = config.get("cards-file", "cards.txt")
    jamendo_clientid = config.get("jamendo-clientid", "")
    jamendo_username = config.get("jamendo-username", "")
    use_card_service = config.get("use-card-service", False)
    log = config.get("log", False)

    instance = Server(current_dir, cardsfile, log, mpdhost, mpdport,
      httpport, jamendo_clientid, jamendo_username, use_card_service, extra_pages)
    return instance

class Server:
    def __init__(self, resources_path, cardsfile, log, mpdhost, mpdport,
      http_port, jamendo_clientid, jamendo_username, use_cardservice, extra_pages):
        self.notifier = notifier.Notifier()
        self.cardstore = cards.CardStore(cardsfile, use_cardservice)
        self.mpdplayer = mpdplayer.MpdPlayer(mpdhost, mpdport, self.notifier.notify)
        self.mpdsource = mpdsource.MpdSource(self.mpdplayer.client)
        radios = radiosource.RadioSource(self.mpdplayer)
        self.shell = shell.Shell()

        handlers = self.mpdsource.handlers() + [radios.play_radio]
        enrichers = [self.mpdsource.enrich_track]
        pages = []
        pages += extra_pages
        
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

        self.actions = actions.Actions(self.cardstore, 
          handlers,
          enrichers,
          self.mpdplayer.actions() + self.shell.actions())
        self.cardmanager = cardmanager.CardManager(self.cardstore, self.actions, self.notifier.notify)

        pages += [
            ("Cards", lambda c: web.CardsPage(c, self.cardstore)),
            ("Mpd", lambda c: mpdsource.SearchPage(c, self.mpdsource)),
            ("Playlists", lambda c: mpdsource.PlaylistPage(c, self.mpdsource)),
            ("Radio", lambda c: radiosource.RadioPage(c, radios)),
            ("Actions", lambda c: actions.ActionsPage(c, self.actions)),
        ]
        self.web = web.Web(resources_path, log, http_port, ["box-functions.js"], pages)
        self.web.root.longPoll = web.LongPollStatus(self.notifier)
        self.web.root.action = web.ActionPage(self.actions, self.cardmanager)
        self.web.root.action.exposed = True

    def start(self):
        self.mpdplayer.start()
        self.web.start()
    def stop(self):
        cherrypy.log("Stopping swisher", severity=logging.INFO)
        self.notifier.stop()
        self.web.stop()
        self.mpdplayer.stop()

