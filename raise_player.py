from pypokerengine.players import BasePokerPlayer
from time import sleep
from pprint import pprint

class RaisedPlayer(BasePokerPlayer):
  # name of our bot, I think hardcode cause looking at the round_state data there's no other way to identify whose action is who
  name = "FT2" 
  round = 0 # current_round
  seat = 0
  small_blind = True

  # opponents properties for classification (loose/tight, passive/aggressive)
  # loose if gameplay/current_round (GP%) >= 28%
  # passive if raise_count - call_count <= 0
  # 4 stages: preflop, flop, turn, river
  games_play = 0 # games where opponent did not fold i.e. we fold or both see to river
  raise_count = 0 # number of hands raised of opponent
  call_count = 0  

  def declare_action(self, valid_actions, hole_card, round_state):
    logFile = open('logfile.txt', 'a')
    pprint(round_state, logFile)

    self.new_round(round_state)

    for i in valid_actions:
        if i["action"] == "raise":
            action = i["action"]
            return action  # action returned here is sent to the poker engine
    action = valid_actions[1]["action"]
    return action # action returned here is sent to the poker engine

  def receive_game_start_message(self, game_info):
    pass

  def receive_round_start_message(self, round_count, hole_card, seats):
    pass

  def receive_street_start_message(self, street, round_state):
    pass

  def receive_game_update_message(self, action, round_state):
    pass

  def receive_round_result_message(self, winners, hand_info, round_state):
    pass

  # Utility functions to get observable environment var
  def get_pot(self, round_state):
    return round_state['pot']['main']['amount']

  # new round check, to update seat position, do every declare_action call
  def new_round(self, round_state): 
    if self.round != round_state['round_count']:
      self.round = round_state['round_count']
      self.seat = self.get_seat_position(round_state)
      if round_state['small_blind_pos'] == self.seat:
        self.small_blind = True
      else:
        self.small_blind = False

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
