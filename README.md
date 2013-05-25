Swisher
-------
Swisher is a fun way to play music at home.  
You associate songs with physical cards and then wave them past a pad to play the song.

![Picture of Swisher whiteboard](http://thomasrynne.github.io/swisher/swisher-small.jpg)

You can see it in use on [this 30s video](http://youtu.be/uHGl409gA08).

Hardware Requirements
---------------------
- To use it you need a 'driverless USB RFID 125khz reader' and some 125khz RFID cards
- It costs about £20 ($30) in total for a reader and 30 cards (postage can be quite slow and the price for the cards is very variable) 
- You also need a PC and speakers
- It was created with a [Raspberry Pi](http://www.raspberrypi.org) in mind but any Linux PC will do

Software Dependencies
---------------------
- MPD/Mopidy - Swisher is an [mpd](http://mpd.wikia.com) client so you need a working mpd installation first. It also works with [Mopidy](http://www.mopidy.com/) an alternative mpd server which plays music from multiple sources.
- evdev - a linux kernel module which is usually already present
   (check you have the directory /dev/input)

Installing
----------
    > sudo apt-get install python-dev python-setuptools
    > git clone https://github.com/thomasrynne/swisher.git
    > cd swisher
    > python setup.py install
    > swisher

 Go to http://localhost:3344 with a browser and you should see the swisher web page

Using
-----
 The swisher webpage lets you search for tracks and albums and lists some radio stations. Search for a song and press play first to check that playing is working.
 
 To associate cards with songs you press the zigzag button of the song and then
 swipe the card. After that swiping the card should play the song.

 As well as songs, 'actions' can be associated with cards so you can make
 cards for stop/next/previous... See the /Actions page

The Cards
---------
 There are many ways to use the physical cards. Here are some suggestions:

- Stack of cards with song names written on sticky labels on the card
- Stick pictures on the cards (for example album covers)
- Put magnets on the card and keep the cards on a fridge or magnetic whiteboard
 - You can also bend the end of the cards in very hot water 
    which makes it easier to take them of the whiteboard
 - Magnets intended for shower doors are cheap and the right strength
- Cut round the antenna to make the cards smaller and stick them to toys
 - Hold the card against a bright light to see where the antenna is
 - Don't cut off the RFID chip which is usually a dot just outside the
   round antenna

- You can also get keyring RFID tags. I have not tried these yet.

Please experiment yourself and let me know what works.

Optional  Configuration
-----------------------

 Driverless RFID readers behave like a usb keyboard and simulate typing
 in the card number when a card is waved as if it was entered through a keyboard.
 This means numbers get entered in the active terminal.

 If you want to suppress this you can tell swisher which
 device is the rfid reader and it will grab and suppress the fake
 key presses.

 Run "swisher --list-devices" before and after plugging in the USB RFID reader
 to see the name of your RFID reader. Then use 
  the --grab-device argument or specify grab-device: 'name' in /etc/swisher.conf
  if you are using the init script (see below)

 By default swisher connects to mpd on localhost 6600
 You can change this with the mpd-host and mpd-port properties
 
 By default the swisher web server listens on 3344
 You can change this with the http-port property

### Start on Boot

    > sudo cp misc/init.d.swisher /etc/init.d/swisher
    > sudo cp misc/swisher.conf /etc
    > sudo update-rc.d swisher defaults

### Jamendo

 [Jamendo](http://www.jamendo.com) hosts free music for personal use.
 If you set the value jamendo-username: in the configuration file
 Jamendo pages are added to the swisher web page. You can 
 use these pages to associate cards with tracks on Jamendo.

