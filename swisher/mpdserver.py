import thread
import subprocess
import winstart
import time
import os.path

#launches the mpd.exe server
class MpdServer:
    def __init__(self, current_dir):
        self._root_dir = os.path.dirname(current_dir)
        self.process = False
    
    def start(self):
        thread.start_new_thread(self._run_mpd, ())
    
    def _run_mpd(self):
        exe = self._root_dir + "\\mpd-0.17.4-win32\\bin\\mpd.exe"
        conf = self._root_dir + "\\mpd-0.17.4-win32\\mpd.conf"
        startupinfo = subprocess.STARTUPINFO() 
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW #prevents a console appearing
        self.process = subprocess.Popen([exe, conf], startupinfo=startupinfo)
    def stop(self):
        if self.process:
            self.process.terminate()

if __name__ == "__main__":
    server = MpdServer(winstart.find_current_dir())
    server.start()
    time.sleep(10)