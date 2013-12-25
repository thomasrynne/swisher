import os.path
import os
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

        
def run(instance, stops):
    cardreader = windowscardreader.WindowsCardReader(
        instance.cardmanager.on_card,
        instance.cardmanager.update_devices_count
    )
    instance.start()
    cardreader.start()
    tray = systray.App('Swisher', instance.swisher_dir() + '\winresources\icon.ico')
    def do_openpage(a): os.startfile("http://localhost:3344")
    def do_exit(a):
        for s in stops: s.stop()
        instance.stop()
        cardreader.stop()
    tray.on_quit = do_exit
    openpage = systray.MenuItem(title='Open webpage', name='Open')
    openpage.onclick = do_openpage
    tray.add_menuitem(openpage)
    tray.start()
