from pypokerengine.players import BasePokerPlayer
from pypokerengine.engine.hand_evaluator import HandEvaluator
import random as rand
import pprint

class RandomPlayer(BasePokerPlayer):

  def __init__(self):
    self.hole_table = [] // TODO: Generate lookup table of EHS to possible hole cards

  def EHS(self, hole_card, community_card):
    if len(community_card) == 2:
      return self.hole_table[hole_card]
    if len(community_card) == 3 or len(community_card) == 4:
      return EHS_3_4(hole_card, community_card)
    else:
      return EHS_5(hole_card, community_card)

  def EHS_3_4(hole_card, community_card):
    p_win = 0
    for iter in range(1000):
      community_card, opp_hole_card = generate_cards(hole_card, community_card) 
      p_score = HandEvaluator.eval_hand(hole_card, community_card)
      o_score = HandEvaluator.eval_hand(opp_hole_card, community_card)
      p_win += int(p_score > o_score)
    return p_win/1000
  
  def EHS_5(hole_card, community_card):
    opp_possible_hole_cards = get_all_possible_opp_hole(hole_card, community_card)
    p_win = 0
    for opp_hole_card in opp_possible_hole_cards:
      p_score = HandEvaluator.eval_hand(hole_card, community_card)
      o_score = HandEvaluator.eval_hand(opp_hole_card, community_card)
      p_win += int(p_score > o_score)
    return p_win/len(opp_possible_hole_cards) // SHOULD I DO LAPLACE TO PREVENT N/0 SITUATION?

  def generate_cards(hole_card, community_card):
    return []
    
  def get_all_possible_opp_hole(hole_card, community_card):
    return []

  def declare_action(self, valid_actions, hole_card, round_state):
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
    pass

  def receive_street_start_message(self, street, round_state):
    pass

  def receive_game_update_message(self, action, round_state):
    pass

  def receive_round_result_message(self, winners, hand_info, round_state):
    pass

def setup_ai():
  return RandomPlayer()
