from actions import ActionRegistry

class Shell:
    def __init__(self, actions):
        self.actions = actions
        self.commands = { "poweroff": ("Power Off", "sudo poweroff") }
        self.actions.register("shell", "Actions", self._shell_command,
         [ ActionRegistry(code,value[0]) for code,value in self.commands.items() ])

    def _shell_command(self, name):
        command = self.commands[name][1]
        os.system(command)

