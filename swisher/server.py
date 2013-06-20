
import notifier
import web
import cardreader
import cardmanager
import cards
import mpdsource
import mpdplayer
import actions
import shell
import cherrypy
import logging
import radiosource
import printer
import jamendo

class Server:
    def __init__(self, resources_path, cardsfile, log, grab_device, mpdhost, mpdport,
      http_port, jamendo_clientid, jamendo_username, use_cardservice):
        print("1", use_cardservice)
        self.notifier = notifier.Notifier()
        self.cardstore = cards.CardStore(cardsfile, use_cardservice)
        self.mpdplayer = mpdplayer.MpdPlayer(mpdhost, mpdport, self.notifier.notify)
        self.mpdsource = mpdsource.MpdSource(self.mpdplayer.client)
        radios = radiosource.RadioSource(self.mpdplayer)
        self.shell = shell.Shell()

        handlers = self.mpdsource.handlers() + [radios.play_radio]
        enrichers = [self.mpdsource.enrich_track]
        pages = []

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
        self.cardreader = cardreader.CardReader(
            grab_device,
            self.cardmanager.on_card,
            self.cardmanager.update_devices_count
        )

        pages += [
            ("Cards", lambda c: web.CardsPage(c, self.cardstore)),
            ("Mpd", lambda c: mpdsource.SearchPage(c, self.mpdsource)),
            ("Radio", lambda c: radiosource.RadioPage(c, radios)),
            ("Actions", lambda c: actions.ActionsPage(c, self.actions)),
            ("CardPrinter", lambda c: printer.CardPrinterPage(c))
        ]
        self.web = web.Web(resources_path, log, http_port, ["box-functions.js"], pages)
        self.web.root.longPoll = web.LongPollStatus(self.notifier)
        self.web.root.action = web.ActionPage(self.actions, self.cardmanager)
        self.web.root.action.exposed = True

    def start(self):
        self.mpdplayer.start()
        self.cardreader.start()
        self.web.start()
    def stop(self):
        cherrypy.log("Stopping swisher", severity=logging.INFO)
        self.notifier.stop()
        self.web.stop()
        self.cardreader.stop()
        self.mpdplayer.stop()

