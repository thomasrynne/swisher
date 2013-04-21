import notifier
import web
import cardreader
import cardmanager
import cards
import mpdsource
import actions
import shell
import cherrypy
import logging

class Server:
    def __init__(self, resources_path, cardsfile, log, grab_device, mpdhost, mpdport, http_port):
        self.notifier = notifier.Notifier()
        self.card_store = cards.CardStore(cardsfile)
        self.actions = actions.Actions()
        self.card_manager = cardmanager.CardManager(self.card_store, self.actions, self.notifier.notify)
        self.card_reader = cardreader.CardReader(
            grab_device,
            self.card_manager.on_card_f(),
            self.card_manager.on_devices_change_f()
        )
        self.mpdsource = mpdsource.MpdSource(mpdhost, mpdport, self.actions, self.notifier.notify)
        self.shell = shell.Shell(self.actions)
        self.web = web.Web(resources_path, log, http_port,
          self.actions, self.card_store, self.card_manager, self.notifier)
    def start(self):
        self.mpdsource.start()
        self.card_reader.start()
        self.web.start()
    def stop(self):
        cherrypy.log("Stopping swisher", severity=logging.INFO)
        self.notifier.stop()
        self.web.stop()
        self.card_reader.stop()

