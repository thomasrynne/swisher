
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
    actions.registerAction("Lock", "lock", self.lock)
    actions.registerAction("Unlock", "unlock", self.unlock)

  def notice(self):
    text = ""
    if self.device_count == 0:
        text = "No reader"
    elif self.record_mode:
        text = "Record mode for " + self.record_mode[2]
    elif self.locked:
        text = "Locked"
    elif self.device_count == 1:
        text = "Ready"
    else:
        text = "Ready (" + self.device_count + ")"
    self.notice_f("reader", text)

  def alert(self, text):
    print "Alert: " + text

  #puts this manager into record mode, so the next card will be associated
  #with the action type and value provided
  def record(self, action_type, action_value, name):
    self.record_mode = (action_type, action_value, name)
    self.notice()

  def cancel_record(self):
    self.record_mode = False
    self.notice()
    self.alert("Record cancelled")

  def lock(self):
      self.locked = True
      self.notice()
  def unlock(self):
      self.locked = False
      self.notice()

  def on_devices_change_f(self):
    def update_devices_count(n):
      self.device_count = n
      self.notice()
    return update_devices_count

  #returns the function to use for handling card events
  #the function returned expectes a single string of the card number
  def on_card_f(self):
    def on_card(card):
      try:
        if self.record_mode:
          (action_type, action_value, name) = self.record_mode
          self.card_store.store(card, action_type, action_value)
          self.record_mode = False
          self.notice()
          self.alert("Card recorded")
        else:
          if card not in self.card_store.by_card_number:
            self.alert("Unknown card: " + card)
          else:
            (actionType, actionValue) = self.card_store.by_card_number[card]
            if self.locked and actionType != "action" and actionValue != "unlock":
              self.alert("Ignoring...locked")
            else:
              self.actions.invoke(actionType, actionValue)
      except:
        print traceback.format_exc()
        logging.exception("card event handling failed")
    return on_card
