import sys
import getopt

from pypokerengine.api.game import setup_config, start_poker
from raise_player import RaisePlayer
from smartplayer import SmartPlayer


# Default option
num_game = 10000
num_round = 1000
initial_stack = 10000

# agent1_pot = 0
# agent2_pot = 0
small_blind = 10

required_win_pct = 70


def usage():
    print "usage: " + sys.argv[0] + " -n no_of_games -r max_rounds -i initial_stack -s small_blind_amount"


def initiate_game(config):
    win_count = 0;
    for game in range(1, 101):
        print "Game number: " + str(game)
        game_result = start_poker(config, verbose = 0)
        # agent1_pot = agent1_pot + game_result['players'][0]['stack']
        # agent2_pot = agent2_pot + game_result['players'][1]['stack']
        if game_result['players'][0]['stack'] > game_result['players'][1]['stack']:
            win_count += 1
        # raiseplayer.exp_replay()
    return win_count


def set_config(player1, player2):
    config = setup_config(max_round=num_round, initial_stack=initial_stack, small_blind_amount=small_blind)
    config.register_player(name="f1", algorithm=player1)
    config.register_player(name="FT2", algorithm=player2)
    return config


try:
    opts, args = getopt.getopt(sys.argv[1:], 'n:r:i:s')
except getopt.GetoptError:
    usage()
    sys.exit(2)
    
for o, a in opts:
    if o == '-n': # number of games
        num_game = int(a)
    elif o == 'r': # max round for each game
        num_round = int(a)
    elif o == 'i': # initial stackss
        initial_stack = int(a)
    elif o == 's': # small blind
        small_blind = int(a)
    else:
        assert False, "unhandled option"

raiseplayer = RaisePlayer()
smartPlayer = SmartPlayer()

config = set_config(raiseplayer, smartPlayer)
print 'Start training with: \nNo. of games: %d\nMax rounds: %d\nInitial stack: %d\nSmall blind amount: %d' % (num_game, num_round, initial_stack, small_blind)

for game_batch in range(0, num_game/100):
    # Games are played in batch of 100
    win_pct = initiate_game(config)
    # When win % exceeds required %, swap player
    if win_pct > required_win_pct:
    	print 'Your player outplays the default player'
        config = set_config(smartPlayer, smartPlayer)
    smartPlayer.exp_replay()
	smartPlayer.save("./save/dqn_model.h5")
	if game_batch > 0:
		smartPlayer.load("./save/dqn_model.h5")