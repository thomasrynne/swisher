import cherrypy
import json

class Action:
    def __init__(self, name, code, f):
        self.name = name
        self.code = code
        self.f = f
        self.value = {"action": self.code}


# CardManager uses this to determine what to do with a given card
class Actions():
    def __init__(self, cardstore, handlers, enrichers, actions):
        self._cardstore = cardstore
        self._handlers = handlers
        self._enrichers = enrichers
        self._actions = actions
        self._actions_by_code = {}
        for a in actions:
            self._actions_by_code[a.code] = a.f

    def invoke(self, value):
        ok = self._attempt_play(value)
        if not ok:
            extras = self._enrich(value)
            if extras:
                ok2 = self._attempt_play(dict(extras, **value))
                if ok2:
                    return extras
        return {}

    def _attempt_play(self, value):
        for h in [self._action_handler] + self._handlers:
            r = h(value)
            if r:
                return True
        return False

    def _enrich(self, value):
        for e in self._enrichers:
            extras = e(value)
            if extras:
                return extras
        return None

    def _action_handler(self, value):
        code = value.get("action")
        if code:
            handler = self._actions_by_code.get(code)
            if not handler:
                cherrypy.log("Unknown action code : " + code, severity=logging.ERROR)
            else:
                handler()
        return None
    def actions(self):
        return self._actions

class ActionsPage():
    def __init__(self, context, actions):
        self._context = context
        self._actions = actions
    @cherrypy.expose
    def index(self):
        return self._context.render("actions.html","Actions", actions=self._actions.actions())

