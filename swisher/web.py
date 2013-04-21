
import cherrypy
import json
from mako.template import Template
from mako.lookup import TemplateLookup
from cherrypy.lib.static import serve_file
import os.path
import printer
import thread
import time
import Queue
import json

class RootPage:
  def __init__(self, dir, context, actions):
      self.dir = dir
      self.context = context
      self.actions = actions

  @cherrypy.expose
  def index(self, search=""):
      template = self.context.get_template("search.html")
      results = self.actions.find(search)
      return template.render(
          title="Home",
          tabs=self.context.tabs(),
          stats=self.actions.stats(),
          search=search, results=results)

  @cherrypy.expose
  def default(self, name):
      template = self.context.get_template("list.html")
      return template.render(
          title=name,
          tabs=self.context.tabs(),
          actions=self.actions.values_for(name))

  @cherrypy.expose
  def assets(self, name):
      return serve_file(os.path.abspath(self.dir + "/assets/" + name))

  @cherrypy.expose
  def search(self, text=None):
    results = self.actions.find(text)
    template = self.context.get_template("search-results.html")
    return template.render(results=results)

class CardsPage:
  def __init__(self, context, card_store, actions):
    self.context = context
    self.card_store = card_store
    self.actions = actions
  @cherrypy.expose
  def index(self):
    template = self.context.get_template("cards.html")
    return template.render(
        title="Cards",
        tabs=self.context.tabs(),
        cards=self.cards_with_name())
  def cards_with_name(self):
    for number, action in self.card_store.cards():
      name = "Unknown"
      try:
          name = self.actions.lookup(action[0], action[1])
      except:
          pass
      yield (number, action[0], action[1], name)

class ActionPage:
  def __init__(self, actions, card_manager):
    self.actions = actions
    self.card_manager = card_manager
  @cherrypy.expose
  def invoke(self, prefix=None, value=None):
    self.actions.invoke(prefix, value)
  @cherrypy.expose
  def record(self, prefix=None, value=None):
    self.card_manager.record(prefix, value)

class CardPrinter:
    def __init__(self, context):
        self.context = context

    @cherrypy.expose
    def index(self):
        template = self.context.get_template("printer-six.html")
        return template.render(
            title="Card Printer",
            tabs=self.context.tabs())

    @cherrypy.expose
    def createPDFx6(self, card1cover, card2cover, card3cover,
                        card4cover, card5cover, card6cover,
                        card1title, card2title, card3title,
                        card4title, card5title, card6title):
        cherrypy.response.headers['Content-Type']= 'application/pdf'
        return printer.buildPDFx6(1,
            [ card1cover, card2cover, card3cover,
              card4cover, card5cover, card6cover])

class LongPollStatus:
    def __init__(self, notifier):
        self.notifier = notifier

    @cherrypy.expose
    def status(self, **current):
        changed_status = self.notifier.next_status(current)
        return json.dumps(changed_status)

class WebContext:
    def __init__(self, template, actions):
        self.template = template
        self.actions = actions
    def get_template(self, name):
        return self.template.get_template(name)
    def tabs(self):
        return ["Search"] + self.actions.groups() + [ "Cards", "Card Printer" ]

class Web:
  def __init__(self, dir, logfile, port, actions, card_store, card_manager, notifier):
    self.dir= dir
    self.logfile = logfile
    self.port = port
    self.context = WebContext(TemplateLookup(directories=[dir+'/templates']), actions)
    self.actions = actions
    self.card_store = card_store
    self.card_manager = card_manager
    self.root = RootPage(dir, self.context, self.actions)
    self.root.Action = ActionPage(self.actions, self.card_manager)
    self.root.Action.exposed = True
    self.root.Cards = CardsPage(self.context, self.card_store, self.actions)
    self.root.CardPrinter = CardPrinter(self.context)
    self.root.longPoll = LongPollStatus(notifier)

  def start(self):
    thread.start_new_thread(self._run, ())
  def _run(self):
    cherrypy.quickstart(self.root, config={
        'global': {
          'environment': 'production',
          'log.screen': not self.logfile,
          'log.access_file': False,
          'log.error_file': self.logfile,
          'server.socket_host': "0.0.0.0",
          'server.socket_port': self.port,
          'server.thread_pool': 10
        }
    })
  def stop(self):
    cherrypy.engine.exit()
