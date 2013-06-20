import actions

class Shell:
    def __init__(self):
        pass
    def actions(self):
        return [actions.Action("Poweroff", "poweroff", self._poweroff)]
    def _poweroff(self):
        os.system("sudo poweroff")

