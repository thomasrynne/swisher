import server
import winstart
import webcontrol
import mpdplayer
import mpdserver
import spotify
import itunesplayer
import sys
import os.path

def run():
    config = server.load_config("swisher.conf")
    current_dir = winstart.find_current_dir()
    log = server.Logger(open(os.path.dirname(current_dir) + "\\swisher-log.txt", "a"))
    sys.stdout = log
    sys.stderr = log    
    webcontrolx = webcontrol.create_factory(config)
    #mpdplayerx = mpdplayer.create_factory(config)
    spotifyx = spotify.create_factory(config)
    itunesx = itunesplayer.create_factory(config)
    players = [webcontrolx, spotifyx, itunesx] #mpdplayerx
    #mpdserverx = mpdserver.MpdServer(current_dir)
    #mpdserverx.start()
    instance = server.create_server(current_dir, config, players)
    winstart.run(instance, []) #[mpdserverx]

def main():
    run()

if __name__ == "__main__":
    main()
