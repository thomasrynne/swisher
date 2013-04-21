import threading

#Maintains a dictionary of values eg { mpd:Stopped, reader:Ready}
#And has a blocking method next_status which returns when
#the status changes. This is used for http long polling
class Notifier:
    def __init__(self):
        self.clients = {}
        self.lock = threading.RLock()
        self.event = threading.Event()
        self.running = threading.Event()
        self.running.set()
        self._status = {}

    def status(self):
        with self.lock:
            return self._status

    def stop(self):
        self.event.set()
        self.running.clear()

    def notify(self, code, status):
        with self.lock:
            if code not in self._status or self._status[code] != status:
                self._status[code] = status
                self.event.set()
                self.event.clear()

    def next_status(self, current):
        if not self.running.is_set():
            return { "stopping": True }
        my_value = self.status()
        if current != my_value:
            return { "action": "update", "state": my_value}
        else:
            r = self.event.wait(30) #long poll timeout
            if not self.running.is_set():
                return { "action": "stopping" } #tell browser to back off
            my_value = self.status()
            if current != my_value:
                return { "action": "update", "state": my_value }
            else:
                return {}

