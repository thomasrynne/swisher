import cherrypy
import json
import logging

class Action:
    def __init__(self, name, code, f):
        self.name = name
        self.code = code
        self.f = f
        self.value = {"action": self.code}


# CardManager uses this to determine what to do with a given card
class Actions():
    def __init__(self, cardstore, players, actions):
        self._cardstore = cardstore
        self._players = players
        self._actions = actions
        self._actions_by_code = {}
        for p in players:
            self._actions += p.actions()
        for a in actions:
            self._actions_by_code[a.code] = a.f
        self._actions_by_code["stop"] = self._stop
        self._actions_by_code["pause"] = self._pause
        self._actions_by_code["next"] = self._next
        self._actions_by_code["previous"] = self._previous
        self._current_player = None

    def invoke(self, value):
        print "Invoke: " + str(value)
        r = self._handle_action(value)
        if r: return {}
        for player in self._players:
            ok = self._attempt_play(player, value)
            if ok:
                self._change_player(player)
            else:
                extras = self._enrich(value)
                if extras:
                    ok2 = self._attempt_play(player, dict(extras, **value))
                    if ok2:
                        self._change_player(player)
                        return extras
        return {}

    def _change_player(self, player):
        if self._current_player != player:
            if self._current_player: self._current_player.stop()
            self._current_player = player
    def _stop(self):
        if self._current_player:
            self._current_player.stop()
        else:
            for p in self._players: p.stop()
    def _pause(self):
        if self._current_player:
            self._current_player.pause()
        else:
            for p in self._players: p.pause()
    def _next(self):
        if self._current_player:
            self._current_player.next()
        else:
            for p in self._players: p.next()
    def _previous(self):
        if self._current_player:
            self._current_player.previous()
        else:
            for p in self._players: p.previous()

    def _attempt_play(self, player, value):
        for h in player.handlers():
            r = h(value)
            if r:
                return True
        return False

    def _enrich(self, value):
        for p in self._players:
            for e in p.enrichers():
                extras = e(value)
                if extras:
                    return extras
        return None

    def _handle_action(self, value):
        code = value.get("action")
        if code:
            handler = self._actions_by_code.get(code)
            if not handler:
                print self._actions_by_code
                cherrypy.log("Unknown action code : '" + code + "'", severity=logging.ERROR)
            else:
                handler()
                return True
        return False

    def actions(self):
        return [
            Action("Stop", "stop", self._stop),
            Action("Pause", "pause", self._pause) ] + self._actions

class ActionsPage():
    def __init__(self, context, actions):
        self._context = context
        self._actions = actions
    @cherrypy.expose
    def index(self):
        return self._context.render("actions.html","Actions", actions=self._actions.actions())

