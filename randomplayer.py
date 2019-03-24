from pypokerengine.players import BasePokerPlayer
import random as rand
import numpy as np
import tensorflow as tf
from numpy import array
from keras.models import Sequential
from keras.layers import Dense
from keras.optimizers import Adam
from keras import backend as K
import pprint


class RandomPlayer(BasePokerPlayer):

    def declare_action(self, valid_actions, hole_card, round_state):
        state = array([])  # TODO: compute the state ie feature values (SOMEBODY DO THIS PLEASE)
        state = np.reshape(state, [1, self.state_size])
        # eed to map actions to indices, 0 - fold, 1 - call, 2 - raise
        possible_action_indices = set()
        for a in valid_actions:
            if a['action'] == 'fold':
                possible_action_indices.add(0)
            if a['action'] == 'call':
                possible_action_indices.add(1)
            if a['action'] == 'raise':
                possible_action_indices.add(2)
        action_index = self.predict_action(state, possible_action_indices)
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
        for s in seats:
            if s['uuid'] == self.uuid:
                self.beginning_stack = s['stack']
                break
        pass

    def receive_street_start_message(self, street, round_state):
        pass

    def receive_game_update_message(self, action, round_state):
        pass

    def receive_round_result_message(self, winners, hand_info, round_state):
        for s in round_state['seats']:
            if s['uuid'] == self.uuid:
                self.final_stack = s['stack']
                break
        if winners['uuid'] == self.uuid:
            self.final_reward = round_state['pot']['main']['amount']
        else:
            self.final_reward = self.final_stack - self.beginning_stack
        self._remember_examples()  # at the end of each round, record all the training examples

    # -----------------DQN MODEL------------------ #
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
        self.model = self._build_model()
        self.states = []
        self.actions = []
        self.in_game_reward = 0
        self.final_reward = 0
        self.beginning_stack = 0
        self.final_stack = 0
        self.uuid = ""

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
        self.memory.append((self.states[len(self.actions)-1], self.actions[len(self.actions)-1],
                            self.final_reward, self.states[len(self.actions)-1], 1))
        self.states = []  # reset for next round
        self.actions = []
        self.final_reward = 0

    def predict_action(self, state, possible_action_indices):
        if np.random.rand() <= self.epsilon:
            return rand.randrange(len(possible_action_indices))  # randomness
        act_values = self.model.predict(state)
        sorted_action_indices = np.argsort(act_values[0])
        for i in sorted_action_indices:
            if i in possible_action_indices:
                return i

    def exp_replay(self, batch_size):
        minibatch = rand.sample(self.memory, batch_size)
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


def setup_ai():
    return RandomPlayer()
