import os.path
import server
import windowscardreader
import sys
from systray import systray
import notifier
import server

def find_current_dir():
    if getattr(sys, 'frozen', None):
        return sys._MEIPASS + '\\swisher'
    else:
        return os.path.dirname(__file__)

        
def run(instance):
    cardreader = windowscardreader.WindowsCardReader(
        instance.cardmanager.on_card,
        instance.cardmanager.update_devices_count
    )
    instance.start()
    cardreader.start()
    tray = systray.App('Swisher', instance.swisher_dir() + '\winresources\icon.ico')
    #def do_settings(a): tray.show_message("A", "BBBBBB")
    def do_exit(a):
        instance.stop()
        cardreader.stop()
    tray.on_quit = do_exit
    #settings = systray.MenuItem(title='Settings', name='Settings')
    #settings.onclick = do_settings
    #tray.add_menuitem(settings)
    tray.start()
