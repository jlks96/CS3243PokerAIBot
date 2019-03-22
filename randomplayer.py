from pypokerengine.players import BasePokerPlayer
from pypokerengine.engine.hand_evaluator import HandEvaluator
from pypokerengine.engine.card import Card
import random as rand
import pprint
import itertools.combination as combination

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
    original_deck_set = range(1,53)
    hole_card_set = set([card.to_id for card in hole_card])
    community_card_set = set([card.to_id for card in community_card])
    revealed_set = hole_card_set + community_card_set
    cheat_deck = list(original_deck_set - revealed_set) // TO TEST!!!!
    opp_hole_card = []
    while(len(community_card) < 5):
      idx = rand.choice(cheat_deck)
      new_card = Card.from_id(idx)
      community_card.append(new_card)
      cheat_deck.remove(idx)
    while(len(opp_hole_card) < 2):
      idx = rand.choice(cheat_deck)
      new_card = Card.from_id(idx)
      opp_hole_card.append(new_card)
      cheat_deck.remove(idx)
    return community_card, opp_hole_card 

  def get_all_possible_opp_hole(hole_card, community_card):
    original_deck_set = range(1,53)
    hole_card_set = set([card.to_id for card in hole_card])
    community_card_set = set([card.to_id for card in community_card])
    revealed_set = hole_card_set + community_card_set
    cheat_deck = list(original_deck_set - revealed_set) // TO TEST!!!!
    opp_possible_hole_card_id= combination(cheat_deck, 2)
    opp_possible_hole_cards = [[Card.from_id(id_pair[0]), Card.from_id(id_pair[1])] for id_pair in opp_possible_hole_card_id]
    return opp_possible_hole_cards

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
