
import os.path
import thread
import urllib
import httplib
import urllib2
import json

#Stores the association between a card number and an action
#Actions take the form type:value for example album:abbey_road
class CardStore:
  def __init__(self, cardsfile, remote_store_enabled):
    self._cardsFilename = cardsfile
    self._remote_store_enabled = remote_store_enabled
    self._by_card_number = {}
    self._actions = []
    if os.path.exists(self._cardsFilename):
      fh = open(self._cardsFilename)
      for line in fh:
        number = line[:line.find("=")]
        actionType = line[line.find("=")+1:line.find(":")]
        actionValue = line[line.find(":")+1:].strip()
        self._actions.append( (number, (actionType, actionValue)) )
        self._by_card_number[number] = (actionType, actionValue)
      fh.close()

  def store(self, number, actionType, actionValue):
    self._local_store(number, actionType, actionValue)
    if self._remote_store_enabled:
        thread.start_new_thread(self._remote_store, (number, actionType, actionValue))
  def _local_store(self, number, actionType, actionValue):
    fh = open(self._cardsFilename, 'a')
    fh.write(number + "=" + actionType + ":" + actionValue + "\n")
    fh.close()
    self._by_card_number[number] = (actionType, actionValue)
    self._actions.append( (number, (actionType, actionValue)) )

  def lookup_card(self, card):
    result = self._by_card_number.get(card)
    if not result and self._remote_store_enabled:
        result = self._remote_lookup(card)
        if result:
            self._local_store(card, result[0], result[1])
    return result

  def cards(self):
    return self._actions

  def _remote_store(self, number, actionType, actionValue):
    json_value = json.dumps( {"type":actionType, "value":actionValue} )
    data = urllib.urlencode({'cardnumber' : number, 'value' : json_value })
    request = urllib2.Request('http://swisher.herokuapp.com/store', data)
    response = urllib2.urlopen(request)

  def _remote_lookup(self, number):
    connection = httplib.HTTPConnection("swisher.herokuapp.com")
    connection.request("GET", "/read?cardnumber="+number)
    response = connection.getresponse()
    print str(response.status)
    if response.status != 200:
        return None
    else:
        data = response.read()
        values = json.loads(data)[0]
        return (values["type"], values["value"])

