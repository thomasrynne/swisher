
import os.path

#Stores the association between a card number and an action
#Actions take the form type:value for example album:abbey_road
class CardStore:
  def __init__(self, cardsfile):
    self.cardsFilename = cardsfile
    self.by_card_number = {}
    self.actions = []
    if os.path.exists(self.cardsFilename):
      fh = open(self.cardsFilename)
      for line in fh:
        number = line[:line.find("=")]
        actionType = line[line.find("=")+1:line.find(":")]
        actionParameter = line[line.find(":")+1:].strip()
        self.actions.append( (number, (actionType, actionParameter)) )
        self.by_card_number[number] = (actionType, actionParameter)
      fh.close()

  def store(self, number, actionType, actionValue):
    fh = open(self.cardsFilename, 'a')
    fh.write(number + "=" + actionType + ":" + actionValue + "\n")
    fh.close()
    self.by_card_number[number] = (actionType, actionValue)
    self.actions.append( (number, (actionType, actionParameter)) )

  def read(self, card):
    return self.by_card_number[card]

  def cards(self):
    return self.actions

