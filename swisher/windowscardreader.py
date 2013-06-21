import Queue
import threading
import win32api
import win32con
import pyHook
import time
import pythoncom
import sys
import os
import signal

class BufferedEvent:
    def __init__(self, timestamp, keycode, isup):
        self.timestamp = timestamp
        self.keycode = keycode
        self.isup = isup

class JobEntry:
    def __init__(self, delay, keycode, isup):
        self.delay = delay
        self.keycode = keycode
        self.isup = isup

class WindowsCardReader:
    def __init__(self, on_card, on_devices_change):
        self._running = False
        self._on_card = on_card
        self._on_devices_change = on_devices_change
        self._number_event_buffer = []
        self._fake_key = win32con.VK_CLEAR
        self._job_queue = Queue.Queue()
        self._hm = pyHook.HookManager()
        self._hm.KeyDown = self._on_key
        self._hm.KeyUp = self._on_key
        self._hm.HookKeyboard()
        self._modifiers = { 160:False, 161:False, 162:False, 163:False }
        self._on_devices_change(1)
    def start(self):
        self._running = True
        def go(f):
           thread = threading.Thread(target=f)
           thread.daemon = False
           thread.start()
           return thread
        self._wakeup_thread = go(self._worker)
    def stop(self):
        self._running = False
        self._send_jobs([])
	    
    def _no_modifiers(self):
        r = True
        for v in self._modifiers.values():
            if v: r = False
        return r
    def _on_key(self, event):
        #print ( event.Key, event.KeyID, event.Transition, str(event.Injected))
        #if event.Key == 'Q': #while debugging
        #    sys.exit()
        isdown = event.Transition == 0
        isup = not isdown
        if event.KeyID in self._modifiers:
            self._modifiers[event.KeyID] = isdown
        is_fake_key = event.Injected and (event.KeyID == self._fake_key)
        is_buffering = len(self._number_event_buffer) > 0
        number = event.KeyID-48
        is_number = (number >= 0) and (number <= 9) and (not event.Alt) and self._no_modifiers()
        if event.Injected and not is_fake_key:
            return True
        elif is_buffering:
            if not is_fake_key:
                self._buffer(event) #if we have started buffering we buffer this to keep the order
            if not is_fake_key and not is_number and event.KeyID != 13:
                self._replay_buffer() #we should should have completed a card by now
            else:
                card_so_far = self._extract_card()
                if ( (event.KeyID == 13) and isup ):
                    if len(card_so_far) >= 7:
                        #print("ok total ", self._time_since_start(event))
                        self._on_card(card_so_far[-7:])
                        self._number_event_buffer = []
                    else:
                        #print("Got cr up and buffer is: " + card_so_far)
                        self._replay_buffer()
                else:
                    if self._time_since_last_key(event) > 40:#reader's maximum event inverval is 15ms
                        #print("cancel beacuse inverval ", self._time_since_last_key(event))
                        self._replay_buffer()
                    elif self._time_since_start(event) > 180:    #reader's maximum total time is 115ms
                        #print("cancel because total ", self._time_since_start(event))
                        self._replay_buffer()
                    else:
                        #do nothing and wait for the next key or fake event
                        if is_fake_key: #we got the wakeup check but so far it still looks like a card
                            self._send_wakeup(0.010) #we need a wakeup in case nothing else happens
            return False
        elif is_fake_key:
            return False #this is a left over fake key
        else:
            if is_number:
                self._buffer(event)
                self._send_wakeup(0.041)
                return False
            else:
                return True

    def _worker(self):
        while self._running:
            for entry in self._job_queue.get():
                time.sleep(entry.delay)
                if entry.isup:
                    win32api.keybd_event(entry.keycode, 0, win32con.KEYEVENTF_KEYUP, 0)
                else:
                    win32api.keybd_event(entry.keycode, 0, 0, 0)

    def _buffer(self, event):
        self._number_event_buffer.append( BufferedEvent(event.Time, event.KeyID, event.Transition) )
    def _replay_buffer(self):
        self._send_jobs( [ JobEntry(0.001, bevent.keycode,bevent.isup) for bevent in self._number_event_buffer] )
        self._number_event_buffer = []
    def _send_wakeup(self, delay):
        self._send_jobs( [JobEntry(delay, self._fake_key, True)] )
    def _send_jobs(self, jobs):
        self._job_queue.put(jobs)
        
    def _extract_card(self):
        return "".join([ str(bevent.keycode-48) for bevent in self._number_event_buffer if bevent.isup and bevent.keycode!=13])
    def _time_since_last_key(self, event):
        if event.Injected:
            return event.Time-self._number_event_buffer[-1].timestamp
        else:
            return 0
    def _time_since_start(self, event):
        return event.Time - self._number_event_buffer[0].timestamp
    def _last_interval(self):
        if len(self._number_event_buffer) == 1:
            return 0
        else:
            return self._number_event_buffer[-1].timestamp - self._number_event_buffer[-2].timestamp

def main():            
    def on_card(card):
        print ("CARD:"+card)
    def on_device(count):
        pass
        #os.system(r"""C:\Users\thomas\AppData\Roaming\Spotify\spotify.exe --uri spotify:track:2KtWHutIK9LTXxdv5Pz9no""")

    reader = WindowsCardReader(on_card, on_device)
    def signal_handler(signal, frame):
        reader.stop()
    signal.signal(signal.SIGINT, signal_handler)
    reader.blocking_start()
    pythoncom.PumpMessages()

if __name__ == "__main__":
    main()
