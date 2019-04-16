from pypokerengine.players import BasePokerPlayer
from pypokerengine.engine.hand_evaluator import HandEvaluator
from pypokerengine.engine.card import Card
from ast import literal_eval
import random as rand
import numpy as np
import tensorflow as tf
from numpy import array
from keras.models import Sequential
from keras.layers import Dense
from keras.optimizers import Adam
from keras import backend as K
import pprint


class SmartPlayer(BasePokerPlayer):

    def __init__(self):
        BasePokerPlayer.__init__(self)
        # --------------INFO FOR DQN---------------- #
        self.state_size = 5  # number of features
        self.action_size = 3  # number of actions
        self.memory = []  # stores every step of the game
        self.gamma = 0.95  # discount rate
        self.epsilon = 1.0  # exploration rate
        self.epsilon_min = 0.01
        self.epsilon_decay = 0.99
        self.learning_rate = 0.001
        self.batch_size = 32
        self.model = self._build_model()
        self.states = []
        self.actions = []
        self.in_game_reward = 0
        self.final_reward = 0
        self.beginning_stack = 0
        self.final_stack = 0
        # ---------------INFO FOR EHS ---------------- #
        with open('file.txt') as f:
          raw_table = f.readlines()[0]
          self.hole_table = literal_eval(raw_table)
        # ---------------INFO FOR OPP CLASSIFICATION---------------- #
        self.uuid = ""
        self.round = 0 # current_round
        self.small_blind = True
        self.first_action = True # of a new round, occur in preflop, to determine who's small_blind
        self.unanswered_raise = False # from opponent
        self.current_street = 0
        # opponents properties for classification (loose/tight, passive/aggressive)
        # loose if (round - folded)/round (GP%) >= 28%
        # passive if raise_count - call_count <= 0
        # 4 stages: preflop, flop, turn, river
        self.opp_folded = 0  # games where opponent fold
        self.opp_raise = 0  # number of hands raised of opponent
        self.opp_call = 0

    def declare_action(self, valid_actions, hole_card, round_state):
        # ----------OPP CLASS---------- #
        if self.first_action: # our bot has 1st action (b4 receiving 1st game update) -> bot is small_blind
            self.small_blind = True
            self.uuid = round_state['action_histories']['preflop'][0]['uuid']
            self.first_action = False

        # input space size 4 = {1,2,3,4} corresponds to { tightness: True/False, 'aggressiveness' =  True/False }
        opp_class = self.update_opponent_classification()
        # pot, input space = int 0 < x <= 1000
        pot = self.get_pot(round_state)
        # our current stack, input space = int 0 < x <= 1000
        stack = self.get_stack(round_state)
        gain_ratio = (self.beginning_stack - stack) / float(pot)
        # progress, input space size 4 = {1,2,3,4} corresponds to { 'preflop', 'flop', 'turn', 'river' }
        # there are also 'showdown' & 'finished' but declare_action will not get call during those
        progress = self.current_street

        ehs = self.EHS(hole_card, round_state['community_card'])

        # ----------PREDICT ACTION--------- #
        state = array([ehs, opp_class, gain_ratio, stack, progress])
        state = np.reshape(state, [1, self.state_size])
        # map actions to indices, 0 - fold, 1 - call, 2 - raise
        action_index = self.predict_action(state)
        if action_index == 2 and len(valid_actions) == 2:
            action_index = 1
        if action_index == 2 and len(valid_actions) == 1:
            action_index = 0
        if action_index == 1 and len(valid_actions) == 1:
            action_index = 0
        self.states.append(state)
        self.actions.append(action_index)
        if action_index == 0:
            return 'fold'
        if action_index == 1:
            return 'call'
        if action_index == 2:
            return 'raise'

    def receive_game_start_message(self, game_info):
        pass

    def receive_round_start_message(self, round_count, hole_card, seats):
        self.round = round_count
        self.first_action = True
        self.current_street = 0
        for s in seats:
            if s['uuid'] == self.uuid:
                self.beginning_stack = s['stack']

    def receive_street_start_message(self, street, round_state):
        self.current_street += 1

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
        for s in round_state['seats']:
            if s['uuid'] == self.uuid:
                self.final_stack = s['stack']
                break
        if winners[0]['uuid'] == self.uuid:
            self.final_reward = round_state['pot']['main']['amount']
        else:
            self.final_reward = self.final_stack - self.beginning_stack
        # self._remember_examples()  # at the end of each round, record all the training examples (turn on for training only)

    # -----------------DQN MODEL------------------ #
    def _huber_loss(self, y_true, y_pred, clip_delta=1.0):
        error = y_true - y_pred
        cond = K.abs(error) <= clip_delta
        squared_loss = 0.5 * K.square(error)
        quadratic_loss = -0.5 * K.square(clip_delta) + clip_delta * K.abs(error)
        return K.mean(tf.where(cond, squared_loss, quadratic_loss))

    def _build_model(self):
        model = Sequential()
        model.add(Dense(24, input_dim=self.state_size, activation='relu'))
        model.add(Dense(24, activation='relu'))
        model.add(Dense(self.action_size, activation='linear'))
        model.compile(loss=self._huber_loss, optimizer=Adam(lr=self.learning_rate))
        return model

    def _remember_examples(self):
        for i in range(len(self.actions)-1):
            self.memory.append((self.states[i], self.actions[i], self.in_game_reward, self.states[i + 1], 0))
        if len(self.actions) > 0:
            self.memory.append((self.states[len(self.actions)-1], self.actions[len(self.actions)-1],
                            self.final_reward, self.states[len(self.actions)-1], 1))
        self.states = []  # reset for next round
        self.actions = []
        self.final_reward = 0

    def predict_action(self, state):
        if np.random.rand() <= self.epsilon: # randomness
            return rand.randrange(self.action_size)
        act_values = self.model.predict(state)
        return np.argmax(act_values[0])  # returns action

    def exp_replay(self):
        minibatch = rand.sample(self.memory, self.batch_size)
        for state, action, reward, next_state, done in minibatch:
            target = reward
            if not done:
                target = (reward + self.gamma * np.amax(self.model.predict(next_state)[0]))
            target_f = self.model.predict(state)
            target_f[0][action] = target
            self.model.fit(state, target_f, epochs=1, verbose=1)
        if self.epsilon > self.epsilon_min:
            self.epsilon *= self.epsilon_decay

    def load(self, name):
        self.model.load_weights(name)

    def save(self, name):
        self.model.save_weights(name)

    # -------------------EHS------------------ #
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
        probability = self.hole_table.get((card1[1], card2[1], suited)) if self.hole_table.get((card1[1], card2[1], suited)) is not None else self.hole_table.get((card2[1], card1[1], suited))
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
        return p_win/len(opp_possible_hole_cards)

    def EHS(self, hole_card, community_card):
        if len(community_card) == 0:
            return self.EHS_0(hole_card)
        if len(community_card) == 3 or len(community_card) == 4:
            return self.EHS_3_4(hole_card, community_card)
        else:
            return self.EHS_3_4(hole_card, community_card)

    def generate_cards(self, hole_card, community_card):
        community_card_new = [card for card in community_card]
        original_deck_set = set(range(1,53))
        hole_card_set = set([Card.from_str(card).to_id() for card in hole_card])
        community_card_set = set([Card.from_str(card).to_id() for card in community_card])
        revealed_set = hole_card_set.union(community_card_set)
        cheat_deck = list(original_deck_set - revealed_set)
        opp_hole_card = []
        while len(community_card_new) < 5:
            idx = rand.choice(cheat_deck)
            new_card = Card.from_id(idx).__str__()
            community_card_new.append(new_card)
            cheat_deck.remove(idx)
        while len(opp_hole_card) < 2:
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
        cheat_deck = list(original_deck_set - revealed_set)
        opp_possible_hole_card_id = self.combinations(cheat_deck, 2)
        opp_possible_hole_cards = [[Card.from_id(id_pair[0]), Card.from_id(id_pair[1])] for id_pair in opp_possible_hole_card_id]
        return opp_possible_hole_cards

    # -------------------OPP CLASSIFICATION------------------ #
    def update_opponent_classification(self):
        tightness = True
        GP_percentage = (self.round - self.opp_folded) / float(self.round)
        if GP_percentage < 0.28:
            tightness = False
        aggressiveness = True
        if self.opp_raise - self.opp_call <= 0:
            aggressiveness = False
        if tightness and aggressiveness:
            return 4
        elif tightness and (not aggressiveness):
            return 3
        elif (not tightness) and aggressiveness:
            return 2
        else:
            return 1

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
    return SmartPlayer()
