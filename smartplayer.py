from pypokerengine.players import BasePokerPlayer
from pypokerengine.engine.hand_evaluator import HandEvaluator
from pypokerengine.engine.card import Card
from ast import literal_eval
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

    with open('file.txt') as f:
      raw_table = f.readlines()[0]
      self.hole_table = literal_eval(raw_table) # TODO: Generate lookup table of EHS to possible hole cards

  '''POLYFILL FOR ITERTOOLS.COMBINATIONS'''
  def combinations(self, iterable, r):
    # combinations('ABCD', 2) --> AB AC AD BC BD CD
    # combinations(range(4), 3) --> 012 013 023 123
    pool = tuple(iterable)
    n = len(pool)
    if r > n:
        return
    indices = list(range(r))
    yield tuple(pool[i] for i in indices)
    while True:
        for i in reversed(range(r)):
            if indices[i] != i + n - r:
                break
        else:
            return
        indices[i] += 1
        for j in range(i+1, r):
            indices[j] = indices[j-1] + 1
        yield tuple(pool[i] for i in indices)

  def EHS_0(self, hole_card):
    card1 = hole_card[0]
    card2 = hole_card[1]
    suited = card1[0] == card2[0]
    probability = self.hole_table.get((card1[1], card2[1], suited)) if self.hole_table.get((card1[1], card2[1], suited)) != None else self.hole_table.get((card2[1], card1[1], suited))
    return probability/100

  def EHS_3_4(self, hole_card, community_card):
    p_win = 0
    for iter in range(1000):
      community_card_new, opp_hole_card_new = self.generate_cards(hole_card, community_card)
      hole_card_new = [Card.from_str(card) for card in hole_card]
      p_score = HandEvaluator.eval_hand(hole_card_new, community_card_new)
      o_score = HandEvaluator.eval_hand(opp_hole_card_new, community_card_new)
      p_win += int(p_score > o_score)
    return p_win/1000
  
  def EHS_5(self, hole_card, community_card):
    opp_possible_hole_cards = self.get_all_possible_opp_hole(hole_card, community_card)
    p_win = 0
    hole_card_new = [Card.from_str(card) for card in hole_card]
    community_card_new = [Card.from_str(card) for card in community_card]
    for opp_hole_card in opp_possible_hole_cards:
      p_score = HandEvaluator.eval_hand(hole_card_new, community_card_new)
      o_score = HandEvaluator.eval_hand(opp_hole_card, community_card_new)
      p_win += int(p_score > o_score)
    return p_win/len(opp_possible_hole_cards) # SHOULD I DO LAPLACE TO PREVENT N/0 SITUATION?

  def EHS(self, hole_card, community_card):
    if len(community_card) == 0:
      return self.EHS_0(hole_card)
    if len(community_card) == 3 or len(community_card) == 4:
      return self.EHS_3_4(hole_card, community_card)
    else:
      return self.EHS_5(hole_card, community_card)

  def generate_cards(self, hole_card, community_card):
    community_card_new = [card for card in community_card]
    original_deck_set = set(range(1,53))
    hole_card_set = set([Card.from_str(card).to_id() for card in hole_card])
    community_card_set = set([Card.from_str(card).to_id() for card in community_card])
    revealed_set = hole_card_set.union(community_card_set)
    cheat_deck = list(original_deck_set - revealed_set) # TO TEST!!!!
    opp_hole_card = []
    while(len(community_card_new) < 5):
      idx = rand.choice(cheat_deck)
      new_card = Card.from_id(idx).__str__()
      community_card_new.append(new_card)
      cheat_deck.remove(idx)
    while(len(opp_hole_card) < 2):
      idx = rand.choice(cheat_deck)
      new_card = Card.from_id(idx).__str__()
      opp_hole_card.append(new_card)
      cheat_deck.remove(idx)
    community_card_new = [Card.from_str(card) for card in community_card_new]
    opp_hole_card = [Card.from_str(card) for card in opp_hole_card]
    return community_card_new, opp_hole_card 

  def get_all_possible_opp_hole(self, hole_card, community_card):
    original_deck_set = set(range(1,53))
    hole_card_set = set([Card.from_str(card).to_id() for card in hole_card])
    community_card_set = set([Card.from_str(card).to_id() for card in community_card])
    revealed_set = hole_card_set.union(community_card_set)
    cheat_deck = list(original_deck_set - revealed_set) # TO TEST!!!!
    opp_possible_hole_card_id= self.combinations(cheat_deck, 2)
    opp_possible_hole_cards = [[Card.from_id(id_pair[0]), Card.from_id(id_pair[1])] for id_pair in opp_possible_hole_card_id]
    return opp_possible_hole_cards

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
