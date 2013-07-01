
import logging
import traceback

#handles card swipes
# responsible for card recording and lock modes
class CardManager:
  def __init__(self, card_store, actions, notice):
    self.card_store = card_store
    self.actions = actions
    self.notice_f = notice
    self.locked = False
    self.record_mode = False
    self.device_count = 0

  def notice(self):
    text = ""
    if self.device_count == 0:
        text = "No reader"
    elif self.record_mode:
        text = "Record mode for " + self.record_mode[1]
    elif self.locked:
        text = "Locked"
    elif self.device_count == 1:
        text = "Ready"
    else:
        text = "Ready (" + str(self.device_count) + ")"
    self.notice_f("reader", text)

  def alert(self, text):
    print "Alert: " + text

  #puts this manager into record mode, so the next card will be associated
  #with the action type and value provided
  def record(self, value, name):
    self.record_mode = (value, name)
    self.locked = False
    self.notice()

  def cancel_record(self):
    self.record_mode = False
    self.locked = False
    self.notice()
    self.alert("Record cancelled")

  def lock(self):
      self.locked = True
      self.notice()
  def unlock(self):
      self.locked = False
      self.notice()

  def update_devices_count(self, n):
      self.device_count = n
      self.notice()

  def on_card(self, card):
      try:
        if self.record_mode:
          (value, name) = self.record_mode
          self.card_store.store(card, value)
          self.record_mode = False
          self.notice()
          self.alert("Card recorded")
        else:
          result = self.card_store.lookup_card(card)
          if not result:
            self.alert("Unknown card: " + card)
          else:
            if result.get("action") == "unlock":
                self.unlock()
            else:
                if self.locked:
                    self.alert("Ignoring...locked")
                elif result.get("action") == "lock":
                    self.lock()
                else:
                    self._invoke(card, result)
      except:
        print traceback.format_exc()
        logging.exception("card event handling failed")

  def _invoke(self, card, value):
      result = self.actions.invoke(value)
      if not result:
          pass#card failed
      else:
          if result != True:
                #store enriched values
                self.card_store.store(card, {"enrich": result})
