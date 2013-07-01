
import os.path
import thread
import urllib
import httplib
import urllib2
import json
import datetime

#Stores the association between a card number and an action
#Actions take the form type:value for example album:abbey_road
class CardStore:
  def __init__(self, cardsfile, remote_store_enabled):
    self._cardsFilename = cardsfile
    self._remote_store_enabled = remote_store_enabled
    self._by_card_number = {}
    if os.path.exists(self._cardsFilename):
      fh = open(self._cardsFilename)
      for line in fh:
        entry = json.loads(line)
        number = entry["number"]
        value = entry["value"]
        datetime = entry["datetime"]
        self._add_entry(number, value)
      fh.close()

  def _add_entry(self, number, value):
    enrich = value.get("enrich")
    if enrich:
      self._by_card_number[number] = dict(self._by_card_number.get(number,{}), **value)
    else:
      self._by_card_number[number] = value

  def store(self, number, value):
    self._local_store(number, value)
    if self._remote_store_enabled:
        thread.start_new_thread(self._remote_store, (number, value))

  def _local_store(self, number, value):
    now = datetime.datetime.utcnow().isoformat()
    fh = open(self._cardsFilename, 'a')
    fh.write(json.dumps({"number": number, "datetime": now, "value":value}) + "\n")
    fh.close()
    self._add_entry(number, value)

  def lookup_card(self, card):
    result = self._by_card_number.get(card)
    if not result and self._remote_store_enabled:
        result = self._remote_lookup(card)
        if result:
            self._local_store(card, result)
    return result

  def cards(self):
    return self._by_card_number.items()

  def _remote_store(self, number, value):
    shared_value = {}
    for k,v in value.items(): #remove private _ values (which have path names or local ids)
        if not k.startswith("_"): shared_value[k] = v
    if shared_value:
        data = urllib.urlencode({'cardnumber' : number, 'value' : json.dumps(shared_value) })
        request = urllib2.Request('http://swisher.herokuapp.com/cardservice/store', data)
        response = urllib2.urlopen(request)

  def _remote_lookup(self, number):
    connection = httplib.HTTPConnection("swisher.herokuapp.com")
    connection.request("GET", "/cardservice/read?cardnumber="+number)
    response = connection.getresponse()
    print str(response.status)
    if response.status != 200:
        return None
    else:
        entries = json.loads(response.read())
        value = {}
        for entry in entries:
            value.update(entry)
        return value

