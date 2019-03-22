from pypokerengine.players import BasePokerPlayer
import random as rand
import numpy as np
from keras.models import Sequential
from keras.layers import Dense
from keras.optimizers import Adam
from keras import backend as K
import tensorflow as tf
import pprint

class RandomPlayer(BasePokerPlayer):

  # information needed for DQN
  states = {}
  actions = {}
  in_game_reward = 0
  final_reward = 0

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
    elif r <= 0.9 and len(valid_actions ) == 3:
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


  # -----------------DQN MODEL------------------ #
  def __init__(self):
    BasePokerPlayer.__init__(self)
    self.state_size = 5  # number of features
    self.action_size = 3  # number of actions
    self.memory = list()  # stores every step of the game
    self.gamma = 0.95  # discount rate
    self.epsilon = 1.0  # exploration rate
    self.epsilon_min = 0.01
    self.epsilon_decay = 0.99
    self.learning_rate = 0.001
    self.model = self._build_model()

  def _huber_loss(self, y_true, y_pred, clip_delta=1.0):
    error = y_true - y_pred
    cond = K.abs(error) <= clip_delta
    squared_loss = 0.5 * K.square(error)
    quadratic_loss = 0.5 * K.square(clip_delta) + clip_delta * (K.abs(error) - clip_delta)
    return K.mean(tf.where(cond, squared_loss, quadratic_loss))

  def _build_model(self):
    model = Sequential()
    model.add(Dense(24, input_dim=self.state_size, activation='relu'))
    model.add(Dense(24, activation='relu'))
    model.add(Dense(self.action_size, activation='linear'))
    model.compile(loss=self._huber_loss, optimizer=Adam(lr=self.learning_rate))
    return model


  def remember_examples(self):
    for i in range(len(self.actions)-1):
      self.memory.append((self.states[i], self.actions[i], self.in_game_reward, self.states[i + 1], 0))
    self.memory.append((self.states[len(self.actions)-1], self.actions[len(self.actions)-1],
                        self.final_reward, self.states[len(self.actions)-1], 1))

  def decide_action(self, state):
    if np.random.rand() <= self.epsilon:
      return rand.randrange(self.action_size)
    act_values = self.model.predict(state)
    return np.argmax(act_values[0])  # returns action

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
