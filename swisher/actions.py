import cherrypy

# CardManager uses this to determine what to do with a given card
class Actions():
    def __init__(self):
        self._handler_by_prefix = {}
        self._actions = []
        self._actions_by_code = {}
        self.register("action", self._action_handler)

    def register(self, prefix, handler):
        self._handler_by_prefix[prefix] = handler
    def invoke(self, prefix, actionValue):
        handler = self._handler_by_prefix.get(prefix)
        if not handler:
            cherrypy.log("Unknown action type : " + prefix, severity=logging.ERROR)
        else:
            handler(actionValue)

    def registerAction(self, name, code, handler):
        self._actions_by_code[code] = handler
        self._actions.append( (code, name) )
    def _action_handler(self, code):
        handler = self._actions_by_code.get(code)
        if not handler:
            cherrypy.log("Unknown action code : " + code, severity=logging.ERROR)
        else:
            handler()
    def actions(self):
        return self._actions

class ActionsPage():
    def __init__(self, context, actions):
        self._context = context
        self._actions = actions
    @cherrypy.expose
    def index(self):
        return self._context.render("actions.html","Actions", actions=self._actions.actions())

