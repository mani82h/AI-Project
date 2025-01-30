import json
import copy
from math import inf
from config import Config
from house_utils import house_member_count, houses
from heuristic_utils import banner_difference_score, who_has_more
from board_utils import house_variance, house_weight_change, get_neighbors, find_varys
from main_sim_no_gui import make_move, get_possible_moves, print_cards_status, set_banners, calculate_winner, make_companion_move
import random

config_set = False
config = Config()
weights = None

def set_config(new_config):
    global config
    config = new_config

def load_config_from_file(file_path):
    global config
    global weights
    with open(file_path, 'r') as file:
        config_data = json.load(file)
        config_data.pop('weight_names', None)
        config_data.pop('fitness_score', None)
        config = Config(**config_data)
        weights = config.get_weights_dict()

def heuristic(player, opponent, cards, varys_location):
    banners = player.get_banners()
    opponent_banners = opponent.get_banners()
    score = 0
    house_variances = house_variance(cards)

    for card in cards:
        if card.get_name() == 'Varys':
            continue

        house = card.get_house()
        location = card.get_location()

        # Check if capturing this card would secure a banner
        if banners.get(house) + 1 >= opponent_banners.get(house):
            count = house_member_count[house]
            if banners.get(house) + 1 >= (count // 2 + 1):
                score -= (banners.get(house) - count // 2) * 30.0
            else:
                score += weights["capture_banner_bonus"]

        # Row and column priority
        neighbors = get_neighbors(location)
        for neighbor_loc in neighbors:
            neighbor_card = next((c for c in cards if c.get_location() == neighbor_loc), None)
            if neighbor_card and neighbor_card.get_house() == house:
                score += weights["row_col_priority"]

        # General banner count
        score += banners.get(house, 0) * house_weight_change(banners.get(house), opponent_banners.get(house), house)

        # House variance
        if house in house_variances:
            score -= house_variances[house] * weights["house_variance_weight"]

    return score

def getScore(cards, player1, player2, turn):
    if len(cards) == 0:
        if calculate_winner(player1, player2) == 1:
            return 10e9
        elif calculate_winner(player1, player2) == 2:
            return -10e9
    else:
        varys_location = find_varys(cards)
        if turn == 1:
            return weights["who_has_more"] * who_has_more(player1, player2) + weights["banner_difference_score"] * banner_difference_score(player1, player2) + weights["heuristic"] * heuristic(player1, player2, cards, varys_location)
        else:
            return -weights["who_has_more"] * who_has_more(player2, player1) + -weights["banner_difference_score"] * banner_difference_score(player2, player1) -weights["heuristic"] * heuristic(player2, player1, cards, varys_location)

def minimax(player1, player2, cards, depth, alpha, beta, player):
    move = None

    if depth == 0 or len(get_possible_moves(cards)) == 0:  # Either hit depth limit or game over
        return [move, getScore(cards, player1, player2, player)]

    for moves in get_possible_moves(cards):
        current_cards = copy.deepcopy(cards)
        current_player1_status = copy.deepcopy(player1)
        current_player2_status = copy.deepcopy(player2)

        if player == 1:
            make_move(cards, moves, player1)
        else:
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

        # Restore game state
        cards = current_cards
        player1 = current_player1_status
        player2 = current_player2_status

        if alpha >= beta:
            break
    
    if player == 1:
        return [move, alpha]
    else:
        return [move, beta]

def get_valid_ramsay(cards):
    '''
    This function gets the possible moves for Ramsay.

    Parameters:
        cards (list): list of Card objects
    
    Returns:
        moves (list): list of possible moves
    '''

    moves=[]

    for card in cards:
        moves.append(card.get_location())
    
    return moves

def get_valid_jon_sandor_jaqan(cards):
    '''
    This function gets the possible moves for Jon Snow, Sandor Clegane, and Jaqen H'ghar.

    Parameters:
        cards (list): list of Card objects
    
    Returns:
        moves (list): list of possible moves
    '''

    moves=[]

    for card in cards:
        if card.get_name() != 'Varys':
            moves.append(card.get_location())
    
    return moves

def get_move(cards, player1, player2, companion_cards=None, choose_companion=False):
    global config_set
    if config_set == False:
        load_config_from_file('temp_config.json')
        config_set = True

    # Depth limit for minimax
    limit = 3

    # rn choosing companion randomly, later on this should be done better
    if choose_companion:
        # Choose a random companion card if available
        if companion_cards:
            selected_companion = random.choice(list(companion_cards.keys())) # Randomly select a companion card
            move = [selected_companion] # Add the companion card to the move list
            choices = companion_cards[selected_companion]['Choice'] # Get the number of choices required by the companion card
            
            # with open('logs.txt', 'w') as f:
            #     f.write(choices)

            if choices == 1:  # For cards like Jon Snow
                move.append(random.choice(get_valid_jon_sandor_jaqan(cards)))
            
            elif choices == 2:  # For cards like Ramsay
                valid_moves = get_valid_ramsay(cards)

                if len(valid_moves) >= 2:
                    move.extend(random.sample(valid_moves, 2))
                
                else:
                    move.extend(valid_moves)  # If not enough moves, just use what's available
                
                
            elif choices == 3:  # Special case for Jaqen with an additional companion card selection
                valid_moves = get_valid_jon_sandor_jaqan(cards)

                if len(valid_moves) >= 2 and len(companion_cards) > 0:
                    move.extend(random.sample(valid_moves, 2))
                    move.append(random.choice(list(companion_cards.keys())))
                
                else:
                    # If there aren't enough moves or companion cards, just return what's possible
                    move.extend(valid_moves)
                    move.append(random.choice(list(companion_cards.keys())) if companion_cards else None)
        
            return move

    player1_copy = copy.deepcopy(player1)
    player2_copy = copy.deepcopy(player2)

    result = minimax(player1_copy, player2_copy, cards, limit, -inf, inf, 1)
    return result[0]