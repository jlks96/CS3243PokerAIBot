from pypokerengine.api.game import setup_config, start_poker
from randomplayer import RandomPlayer
from raise_player import RaisedPlayer

num_game = 500
agent1_pot = 0
agent2_pot = 0
batch_size = 32

#TODO:config the config as our wish
config = setup_config(max_round=10, initial_stack=1000, small_blind_amount=10)

randomPlayer = RandomPlayer()
config.register_player(name="f1", algorithm=randomPlayer)
config.register_player(name="FT2", algorithm=RaisedPlayer())

# uncomment below after saving a copy of the model (after first run)
# agent.load("./save/dqn_model.h5")

for game in range(1, num_game + 1):
    print("Game number: ", game)
    game_result = start_poker(config, verbose=0)
    agent1_pot = agent1_pot + game_result['players'][0]['stack']
    agent2_pot = agent2_pot + game_result['players'][1]['stack']
    randomPlayer.exp_replay()

randomPlayer.save("./save/dqn_model.h5")

