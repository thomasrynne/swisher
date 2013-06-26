import os.path
import signal
import yaml
import argparse
import server
import linuxcardreader

def load_config(config_file):
    try:
        return yaml.load(file(config_file)) or {}
    except IOError:
        return {}

def run(config):
    mpdhost = config.get("mpd-host", "localhost")
    mpdport = config.get("mpd-port", 6600)
    httpport = config.get("http-port", 3344)
    grabdevice = config.get("grab-device", "")
    cardsfile = config.get("cards-file", "cards.txt")
    jamendo_clientid = config.get("jamendo-clientid", "")
    jamendo_username = config.get("jamendo-username", "")
    use_card_service = config.get("use-card-service", False)
    log = config.get("log", False)

    current_dir = os.path.dirname(os.path.abspath(__file__))
    instance = server.Server(current_dir, cardsfile, log, mpdhost, mpdport,
      httpport, jamendo_clientid, jamendo_username, use_card_service, [])
    reader = linuxcardreader.LinuxCardReader(
        grabdevice,
        instance.cardmanager.on_card,
        instance.cardmanager.update_devices_count
    )
    instance.start()
    reader.start()
    def signal_handler(signal, frame):
        reader.stop()
        instance.stop()	
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    signal.pause()
    

def main():
    parser = argparse.ArgumentParser(description='RFID mpd client')
    parser.add_argument('--list-devices', action="store_true",
                   help='list all present keyboard and rfid reader devices')
    parser.add_argument('--config',  nargs=1, metavar="filename",
                   help='read from config file (same values as these options)')
    parser.add_argument('--grab-device', metavar='name', nargs=1,
                   help='grab and read events from the named device')
    parser.add_argument('--mpd-host', metavar='host', nargs=1,
                   help='the mpd server hostname (localhost)')
    parser.add_argument('--mpd-port', metavar='port', nargs=1,
                   help='the mpd port (6600)')
    parser.add_argument('--http-port', metavar='port', nargs=1,
                   help='the port to run the internal webserver on (3344)')
    parser.add_argument('--cards-file', metavar='filename', nargs=1,
                   help='the file to read and write the cards database to (cards.txt)')
    parser.add_argument('--log', metavar='filename', nargs=1,
                   help='write logs to this file instead of the console and supress web access logs')
    parser.add_argument('--quiet', action="store_true",
                   help='suppress non error logging')
    args = parser.parse_args()
    if args.list_devices:
        cardreader.list_devices()
    else:
        config = {}
        if args.config:
            config = load_config(args.config[0])
        if args.grab_device:
            config["grab-device"] = args.grab_device[0]
        if args.mpd_host:
            config["mpd-host"] = args.mpd_host[0]
        if args.mpd_port:
            config["mpd_port"] = args.mpd_port[0]
        if args.http_port:
            config["http-port"] = args.http_port[0]
        if args.cards_file:
            config["cards-file"] = args.cards_file[0]
        if args.log:
            config["log"] = args.log[0]
        run(config)

if __name__ == "__main__":
    main()

