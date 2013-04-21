import sys
import os
import thread
import evdev
import time
import select
import pyinotify
import signal
import threading

#Captures card events and calls the provided on_card function
#This implementation uses evdev so the linux kernel needs to
#support this (most do) and the user must have access to
# /dev/input/* (this is often achieved by being in the input group)
class CardReader:
    
    class FileSystemEventHandler(pyinotify.ProcessEvent):
        def __init__(self, reader):
            self.reader = reader
        def process_IN_CREATE(self, event):
            time.sleep(0.2) #device does not seem to be ready without this pause
            self.reader.add_device_if_match(event.pathname)
            self.reader.devices_change()

        def process_IN_DELETE(self, event):
            if event.pathname in self.reader.open_keyboards:
                device = self.reader.open_keyboards[event.pathname]
                try:
                    device.close()
                except:
                    pass
                del self.reader.open_keyboards[event.pathname]
                self.reader.devices_change()

    def __init__(self, grab_device, on_card, on_devices_change):
        self.grab_device = grab_device.strip()
        self.on_card = on_card
        self.on_devices_change = on_devices_change
        self.running = True
        self.open_keyboards = {}
        self.event = threading.Event()
        self.wakeup_pipe = os.pipe()
        self.wm = pyinotify.WatchManager()
        wdd = self.wm.add_watch('/dev/input', pyinotify.IN_DELETE | pyinotify.IN_CREATE)
        self.fsnotifier = pyinotify.ThreadedNotifier(self.wm, self.FileSystemEventHandler(self))


    def start(self):
        #starts a thread which reads keyboard events
        th = threading.Thread(target=self._run)
        th.daemon = False
        th.start()

    def list_all_devices(self):
        for name in os.listdir("/dev/input"):
            path = "/dev/input/" + name
            if evdev.util.is_device(path):
                yield path

    def add_keyboards(self):
        for path in self.list_all_devices():
            self.add_device_if_match(path)

    #adds the device if it is a keyboard and optionally
    #if its device name matches the speficied grab device
    def add_device_if_match(self, path):
        try:
            device = evdev.InputDevice(path)
            if self.is_keyboard(device):
                if self.grab_device == "":
                   self.open_keyboards[path] = device
                else:
                    if device.name.strip() == self.grab_device:
                        self.open_keyboards[path] = device
                        device.grab()
                    else:
                        device.close()
            else:
                device.close()
        except:#IOError: [Errno 25] Inappropriate ioctl for device (on mouse)
            pass

    def is_keyboard(self, device):
        capabilities = device.capabilities()
        #1 means keyboard or anything with buttons, 2 means the '1' key
        return 1 in capabilities and 2 in capabilities[1]

    def stop(self):
        self.running = False
        self.fsnotifier.stop()
        self.wakeup_reader_thread()
        self.close_all()
    def close_all(self):
        for path,device in self.open_keyboards.items():
            if self.grab_device != "":
                device.ungrab()
            device.close()
        self.open_keyboards = {}

    def devices_change(self):
        self.update_status()
        self.wakeup_reader_thread()

    def wakeup_reader_thread(self):
        os.write(self.wakeup_pipe[1], 'x')
        self.event.set()
        self.event.clear()

    def update_status(self):
        count = len(self.open_keyboards)
        self.on_devices_change(count)

    def _run(self):
        keys = []
        self.add_keyboards()
        self.update_status()
        self.fsnotifier.start()
        while self.running:
            if len(self.open_keyboards) == 0:
                self.event.wait()
            while self.running:
              try:
               r,w,x = select.select(self.open_keyboards.values() + [self.wakeup_pipe[0]], [], [])
               for fd in r:
                if (type(self.wakeup_pipe[0]) == type(fd)) and (self.wakeup_pipe[0] == fd):
                  os.read(self.wakeup_pipe[0], 1)
                else:
                  for event in fd.read():
                   if event.type == evdev.ecodes.EV_KEY:
                    if event.value == 0 and 2 <= event.code and event.code <= 11:
                      num = event.code - 1
                      if num == 10:
                        num = 0
                      if len(keys) > 0 or num != 0: #we ignore the leading 3 zeros because sometimes they are missed
                        keys.append(str(num))
                      if len(keys) == 7:
                       card = "".join(keys)
                       del keys[:]
                       self.on_card(card)
              except select.error:
               pass
def list_devices():
    def on_card(card):
        pass
    def on_device():
        pass
    reader = CardReader("", on_card, on_device)
    reader.add_keyboards()
    for device in reader.open_keyboards.values():
        print device.name
    if len(reader.open_keyboards) == 0:
        print "No devices found"
    reader.close_all()

def main():
    def on_card(card):
        print "CARD:" + card
    def on_devices_change(n):
        print "Devices: " + n
    reader = CardReader("", on_card, on_devices_change)
    def signal_handler(signal, frame):
        reader.stop()
    signal.signal(signal.SIGINT, signal_handler)
    reader.start()
    signal.pause()


if __name__ == "__main__":
    main()
