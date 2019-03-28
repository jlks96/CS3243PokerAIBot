from pypokerengine.api.game import setup_config, start_poker
from randomplayer import RandomPlayer
from raise_player import RaisedPlayer

num_game = 500
agent1_pot = 0
agent2_pot = 0
batch_size = 32

#TODO:config the config as our wish
config = setup_config(max_round=10, initial_stack=1000, small_blind_amount=10)

config.register_player(name="f1", algorithm=RandomPlayer())
config.register_player(name="FT2", algorithm=RaisedPlayer())

game_result = start_poker(config, verbose=1)

