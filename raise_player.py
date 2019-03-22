from pypokerengine.players import BasePokerPlayer
from time import sleep
from pprint import pprint

class RaisedPlayer(BasePokerPlayer):
  # name of our bot, I think hardcode cause looking at the round_state data there's no other way to identify whose action is who
  name = "FT2" 
  round = 0 # current_round
  seat = 0
  update_sb = True
  small_blind = True

  opp_action = True # odd-even hack to check if the game_update is opponent action

  # opponents properties for classification (loose/tight, passive/aggressive)
  # loose if (round - folded)/round (GP%) >= 28%
  # passive if raise_count - call_count <= 0
  # 4 stages: preflop, flop, turn, river
  folded = 0 # games where opponent fold
  raise_count = 0 # number of hands raised of opponent
  call_count = 0  

  def declare_action(self, valid_actions, hole_card, round_state):
    
    opp_class = self.update_opponent_classifification()

    # print("\n")
    # pprint(opp_class)
    # print("\n")

    for i in valid_actions:
        if i["action"] == "raise":
            action = i["action"]
            return action  # action returned here is sent to the poker engine
    action = valid_actions[1]["action"]
    return action # action returned here is sent to the poker engine

  def receive_game_start_message(self, game_info):
    if game_info['seats'][0]['name'] == self.name:
      self.seat = 0
    else:
      self.seat = 1

  def receive_round_start_message(self, round_count, hole_card, seats):
    self.round = round_count
    self.update_sb = True # Flag signalling new ground to update seat position
    

  def receive_street_start_message(self, street, round_state):
    # small rant: at every round start should have info containing who's the small blind & big blind
    # but nope round_state doesn't get pass so have to check here, questionable original code decision
    if self.update_sb:
      if round_state['small_blind_pos'] == self.seat:
        self.small_blind = True
        self.opp_action = False # odd-even switch, opponent big_blind so start 2nd each street
      else:
        self.small_blind = False
        self.opp_action = True
      update_sb = False

  def receive_game_update_message(self, action, round_state):
    if self.opp_action:
      action = round_state['action_histories'][round_state['street']][-1]['action']
      if action == "RAISE":
        self.raise_count += 1
      if action == "CALL":
        self.call_count += 1

    old_bool = self.opp_action
    self.opp_action = not old_bool # switch since next action would be ours

    # logFile = open('logfile.txt', 'a')
    # pprint(round_state, logFile)
    
  def receive_round_result_message(self, winners, hand_info, round_state):
    logFile = open('logfile.txt', 'a')
    pprint(round_state, logFile)
    opponent_seat = 1 - self.seat
    if round_state['seats'][opponent_seat]['state'] == "folded":
      self.folded += 1

    # print("\n Total opponent fold " + str(self.folded))
    # print("Total opponent raise: " + str(self.raise_count))
    # print("Total opponent call: " + str(self.call_count) + "\n")

  def update_opponent_classifification(self):
    tightness = True
    GP_percentage = (self.round - self.folded) / float(self.round)
    if GP_percentage < 0.28:
      tightness = False
    
    aggressiveness = True
    if self.raise_count - self.call_count <= 0:
      aggressiveness = False

    return {
      'tightness': tightness,
      'aggressiveness': aggressiveness
    }

  # Utility functions to get observable environment var
  def get_pot(self, round_state):
    return round_state['pot']['main']['amount']      

  def get_seat_position(self, round_state):
    if round_state['seats'][0]['name'] == self.name:
      return 0
    else:
      return 1

  # Get our own stack. For opponent stack = 1000 - our stack - pot
  def get_stack(self, round_state):
    return round_state['seats'][seat]['stack'] 

def setup_ai():
  return RaisePlayer()
