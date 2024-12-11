from math import inf
import random
from main import make_move, get_possible_moves, print_cards_status, set_banners
import copy

def find_varys(cards):
    '''
    This function finds the location of Varys on the board.

    Parameters:
        cards (list): list of Card objects

    Returns:
        varys_location (int): location of Varys
    '''

    varys = [card for card in cards if card.get_name() == 'Varys']

    varys_location = varys[0].get_location()

    return varys_location

def heuristic(player):
    banners = player.get_banners()
    return sum(banners.values())

def getScore(cards, player1, player2, turn): # turn indicating wether it's player1 or player2
    if len(cards) == 0:
        if calculate_winner(player1, player2) == 1:
            return 10e9
        elif calculate_winner(player1, player2) == 2:
            return -10e9
    else:
        if turn == 1:
            return heuristic(player1)
        else:
            return -heuristic(player2)

def minimax(player1, player2, cards, depth, alpha, beta, player): # player should be either player1 or player2, turn is either 1 or -1
    move = None
    
    print()
    
    print(f'player: {player}')
    print("card len: ", len(cards))
    
    print()

    if depth == 0 or len(cards) == 0: # either hit tree depth defined limit or someone won
        print("getScore", getScore(cards, player1, player2, player))
        return [move, getScore(cards, player1, player2, player)]
    
    else:
        print(f'possible moves: {get_possible_moves(cards)}')
        for moves in get_possible_moves(cards):
            current_cards = copy.deepcopy(cards)
            current_player1_status = copy.deepcopy(player1)
            current_player2_status = copy.deepcopy(player2)

            print(f'current move: {moves}')
            if player == 1:
                make_move(cards, moves, player1)
            else: # this should be -1 tho
                make_move(cards, moves, player2)

            score = minimax(player1, player2, cards, depth - 1, alpha, beta, -player)
            if player == 1:
                if score[1] > alpha:
                    alpha = score[1]
                    move = moves

            else:
                if score[1] < beta:
                    beta = score[1]
                    move = moves

            # trying to undo what has been done
            # ok the whole point of this is just to restore stuffs and that should be just fine
            cards = current_cards
            player1 = current_player1_status
            player2 = current_player2_status

            if alpha >= beta:
                break

        if player == 1:
            if move == None:
                print("dude!") # this gone cause issues or sth?
            return [move, alpha]

        else:
            if move == None:
                print("dude!")
            return [move, beta]

def get_move(cards, player1, player2):
    '''
    This function gets the move of the player.

    Parameters:
        cards (list): list of Card objects
        player1 (Player): the player
        player2 (Player): the opponent
    
    Returns:
        move (int): the move of the player
    '''
    
    limit = 3 # should be fine tuned based on the time limit
    player1_copy = copy.deepcopy(player1)
    player2_copy = copy.deepcopy(player2)

    result = minimax(player1_copy, player2_copy, cards, limit, -inf, inf, -1)
    print("best move: ", result[0])
    return result[0]

# the heuristic function should be learnable by an alpha or sth, tweaking it a whole lot will prolly result in sth good