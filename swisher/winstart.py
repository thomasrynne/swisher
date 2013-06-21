import os.path
import argparse
import server
import signal
import windowscardreader
import sys
from systray import systray

def load_config(config_file):
    try:
        return yaml.load(file(config_file)) or {}
    except IOError:
        return {}

def find_current_dir():
    if getattr(sys, 'frozen', None):
        return sys._MEIPASS
    else:
        return os.path.dirname(__file__)

def run():
    config = server.load_config("swisher.conf")
    current_dir = find_current_dir()
    instance = server.create(current_dir, config, [])
    cardreader = windowscardreader.WindowsCardReader(
        instance.cardmanager.on_card,
        instance.cardmanager.update_devices_count
    )
    instance.start()
    cardreader.start()
    tray = systray.App('Swisher', 'winresources\icon.ico')
    #def do_settings(a): tray.show_message("A", "BBBBBB")
    def do_exit(a):
        instance.stop()
        cardreader.stop()
    tray.on_quit = do_exit
    #settings = systray.MenuItem(title='Settings', name='Settings')
    #settings.onclick = do_settings
    #tray.add_menuitem(settings)
    tray.start()
        
def main():
    run()
    
if __name__ == "__main__":
    main()

