import sys
import getopt
import time

from pypokerengine.api.game import setup_config, start_poker
from smartplayer import SmartPlayer
from randomplayer import RandomPlayer

# Default option
num_game = 5000
num_round = 500
initial_stack = 10000

small_blind = 20

def usage():
	print "usage: " + sys.argv[0] + " -n no_of_games -r max_rounds -i initial_stack -s small_blind_amount"


def initiate_game(config):
	# Init pot of players
	win_cnt = 0
	for game in range(1, 2):
		print "Game number: %d" % (game)
		start = time.time()
		game_result = start_poker(config, verbose = 0)
		end = time.time()
		print "Time take to play: %.4f seconds" % (end-start)
		agent1_pot = game_result['players'][0]['stack']
		agent2_pot = game_result['players'][1]['stack']
		print 'Player 1 pot: %d' %  (agent1_pot)
		print 'Player 2 pot: %d' %  (agent2_pot)
		if agent1_pot > agent2_pot:
			win_cnt += 1
	return win_cnt


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
	elif o == '-r': # max round for each game
		num_round = int(a)
	elif o == '-i': # initial stackss
		initial_stack = int(a)
	elif o == '-s': # small blind
		small_blind = int(a)
	else:
		usage()
		sys.exit(2)

smartPlayer = SmartPlayer()
randomPlayer = RandomPlayer()
 
config = set_config(smartPlayer, randomPlayer)
print 'Start training with: \nNo. of games: %d\nMax rounds: %d\nInitial stack: %d\nSmall blind amount: %d' % (num_game, num_round, initial_stack, small_blind)

for game_batch in range(0, num_game):
	win_cnt = initiate_game(config)
	smartPlayer.exp_replay()
	smartPlayer.save("dqn_model.h5")
	if game_batch > 0:
		smartPlayer.load("dqn_model.h5")