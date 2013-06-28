import server
import winstart
import notifier
import spotify

def runSpotify():
    cardsfile = "cards.txt"
    log = False
    httpport = 3344
    notifierx = notifier.Notifier()
    use_card_service = True
    spotifyplayer = spotify.SpotifyPlayer()
    handlers = spotifyplayer.handlers()
    enrichers = []
    actions = spotifyplayer.actions()
    spotifyapi = spotify.SpotifyApi()
    pages = [("Spotify", lambda c: spotify.SpotifySearchPage(c, spotifyapi))]
    services = []
    current_dir = winstart.find_current_dir()
    instance = server.Server(current_dir, cardsfile, log, httpport, notifierx,
      use_card_service, handlers, enrichers, actions, pages, services)
    winstart.run(instance)

def main():
    runSpotify()
    
if __name__ == "__main__":
    main()
