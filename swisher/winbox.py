import server
import winstart

def run():
    config = server.load_config("swisher.conf")
    current_dir = winstart.find_current_dir()
    webcontrolx = webcontrol.create_factory(config)
    mpdplayerx = mpdplayer.create_factory(config)
    instance = server.create_server(current_dir, config, [mpdplayerx, webcontrolx])
    winstart.run(instance)

def main():
    run()

if __name__ == "__main__":
    main()
