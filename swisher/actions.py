import cherrypy

# Actions are registered with this and then made
# avaliable on the web page and as actions to be assoicated with cards
# When registering actions a prefix and list of values is supplied
# as well as a function to invoke when a card with the associated action
# is swished.
class ActionRegistry():
    def __init__(self, value, name, children=[]):
        self.value = value
        self.name = name
        self.children = children
class ActionNode():
    def __init__(self, prefix, value, name, children):
        self._prefix = prefix
        self._value = value
        self._name = name
        self._children = children
    def prefix(self): return self._prefix
    def value(self): return self._value
    def name(self): return self._name
    def children(self): return self._children

class ActionsForPrefix:
    def __init__(self, prefix, name, handler, listed):
        self.prefix = prefix
        self.name = name
        self.handler = handler
        self.listed = listed
        self.index = {} #item value -> (search key, ActionNode)
        for item in listed:
            self.index[item.value] = (self.to_key(item.name),
              ActionNode(prefix, item.value, item.name, item.children) )
    def to_key(self, value):
        lowercase = value.lower()
        initials = "".join(map( lambda t: t[0], lowercase.split()))
        return lowercase + " " + initials + " "

class Actions():
    def __init__(self):
      self.byprefix = {}
    def register(self, prefix, name, handler, listed):
      self.byprefix[prefix] = ActionsForPrefix(prefix, name, handler, listed)

    def groups(self):
        g = []
        for actionsforprefix in self.byprefix.values():
            name = actionsforprefix.name
            if name not in g: g.append(name)
        g.sort()
        return g

    def stats(self):
        for actionsforprefix in self.byprefix.values():
            yield (actionsforprefix.prefix, len(actionsforprefix.listed))

    def values_for(self, name):
        l = []
        for actionsforprefix in self.byprefix.values():
            if actionsforprefix.name == name:
                l.append( (actionsforprefix.prefix, actionsforprefix.listed) )
        return l
    
    def lookup(self, prefix, actionValue):
        return self.byprefix[prefix].index[actionValue][1].name()

    def invoke(self, prefix, actionValue):
        if prefix not in self.byprefix:
            cherrypy.log("Unknown action type : " + prefix, severity=logging.ERROR)
        else:
            self.byprefix[prefix].handler(actionValue)

    def find(self, text):
        if text != "":
            ltext = text.lower()
            for actionsforprefix in self.byprefix.values():
                for key, item in actionsforprefix.index.values():
                    if ltext in key:
                        yield item
