class Shell:
    def __init__(self, actions):
        self.actions = actions
        self.actions.registerAction("Poweroff", "poweroff", self._poweroff)

    def _poweroff(self):
        os.system("sudo poweroff")

