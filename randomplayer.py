from pypokerengine.players import BasePokerPlayer
import random as rand
import pprint

class RandomPlayer(BasePokerPlayer):

  def __init__(self):
      self.uuid = ""
      self.round = 0 # current_round
      self.small_blind = True
      self.first_action = True # of a new round, occur in preflop, to determine who's small_blind

      self.unanswered_raise = False # from opponent

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
    # valid_actions format => [raise_action_pp = pprint.PrettyPrinter(indent=2)
    #pp = pprint.PrettyPrinter(indent=2)
    #print("------------ROUND_STATE(RANDOM)--------")
    #pp.pprint(round_state)
    #print("------------HOLE_CARD----------")
    #pp.pprint(hole_card)
    #print("------------VALID_ACTIONS----------")
    #pp.pprint(valid_actions)
    #print("-------------------------------")
    r = rand.random()
    if r <= 0.5:
      call_action_info = valid_actions[1]
    elif r<= 0.9 and len(valid_actions ) == 3:
      call_action_info = valid_actions[2]
    else:
      call_action_info = valid_actions[0]
    action = call_action_info["action"]
    return action  # action returned here is sent to the poker engine

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
        self.unanswered_raise = True
      if opp_action == 'call':
        self.opp_call += 1
      if opp_action == 'fold':
        self.opp_folded += 1      

  def receive_round_result_message(self, winners, hand_info, round_state):
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

  def call_or_check(self):
    if self.unanswered_raise:
      # any action including call will answer the raise thus flip it here
      self.unanswered_raise = False
      return 'call'
    else:
      # no opponent unanswered raise so a call would cost 0 -> effectively a check
      return 'check'

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
  return RandomPlayer()
