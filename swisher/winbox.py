import server
import winstart

def runMpd():
    config = server.load_config("swisher.conf")
    current_dir = winstart.find_current_dir()
    instance = server.createMpdController(current_dir, config, [])
    winstart.run(instance)

def main():
    runMpd()

if __name__ == "__main__":
    main()
