from pypokerengine.players import BasePokerPlayer
from time import sleep
from pprint import pprint

class RaisedPlayer(BasePokerPlayer):

  def __init__(self):
      self.uuid = ""
      self.round = 0 # current_round
      self.small_blind = True
      self.first_action = True # of a new round, occur in preflop, to determine who's small_blind

      # opponents properties for classification (loose/tight, passive/aggressive)
      # loose if (round - folded)/round (GP%) >= 28%
      # passive if raise_count - call_count <= 0
      # 4 stages: preflop, flop, turn, river
      self.opp_folded = 0 # games where opponent fold
      self.opp_raise = 0 # number of hands raised of opponent
      self.opp_call = 0  

  def declare_action(self, valid_actions, hole_card, round_state):
    
    if self.first_action: # our bot has 1st action (b4 receiving 1st game update) -> bot is small_blind
      self.small_blind = True
      self.uuid = round_state['action_histories']['preflop'][0]['uuid']
      self.first_action = False

    opp_class = self.update_opponent_classifification()

    #print("\nraise_count: " + str(self.opp_raise))
    #print("call_count: " + str(self.opp_call))
    #pprint(opp_class)

    for i in valid_actions:
        if i["action"] == "raise":
            action = i["action"]
            return action  # action returned here is sent to the poker engine
    action = valid_actions[1]["action"]
    return action # action returned here is sent to the poker engine

  def receive_game_start_message(self, game_info):
    pass

  def receive_round_start_message(self, round_count, hole_card, seats):
    self.round = round_count
    self.first_action = True
    

  def receive_street_start_message(self, street, round_state):
    pass

  def receive_game_update_message(self, action, round_state):

    if self.first_action: # got 1st game update before declare 1st action -> opponent small_blind
      self.small_blind = False
      self.uuid = round_state['action_histories']['preflop'][1]['uuid']
      self.first_action = False

    if action['player_uuid'] != self.uuid:
      opp_action = action['action']
      if opp_action == 'raise':
        self.opp_raise += 1
      if opp_action == 'call':
        self.opp_call += 1
      if opp_action == 'fold':
        self.opp_folded += 1      
    
  def receive_round_result_message(self, winners, hand_info, round_state):
    # logFile = open('logfile.txt', 'a')
    # pprint(round_state, logFile)
    # print("opp fold: " + str(self.opp_folded))
    pass

  def update_opponent_classifification(self):
    tightness = True
    GP_percentage = (self.round - self.opp_folded) / float(self.round)
    if GP_percentage < 0.28:
      tightness = False
    
    aggressiveness = True
    if self.opp_raise - self.opp_call <= 0:
      aggressiveness = False

    return {
      'tightness': tightness,
      'aggressiveness': aggressiveness
    }

  # Utility functions to get observable environment var
  def get_pot(self, round_state):
    return round_state['pot']['main']['amount']      

  # Get our own stack. For opponent stack = 1000 - our stack - pot
  def get_stack(self, round_state):
    seats = round_state['seats']
    if seats[0]['uuid'] == self.uuid:
      return seats[0]['stack']
    else:
      return seats[1]['stack'] 

def setup_ai():
  return RaisePlayer()
