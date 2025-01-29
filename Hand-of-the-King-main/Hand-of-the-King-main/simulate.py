import json
import copy
from math import inf
from config import Config
from house_utils import house_member_count, houses
from heuristic_utils import banner_difference_score, who_has_more
from board_utils import house_variance, house_weight_change, get_neighbors, find_varys
from main_sim import make_move, get_possible_moves, print_cards_status, set_banners, calculate_winner, make_companion_move

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

def get_move(cards, player1, player2, companion_cards=None, choose_companion=False):
    global config_set
    if config_set == False:
        load_config_from_file('temp_config.json')
        config_set = True

    # Depth limit for minimax
    limit = 2

    # Handle companion card logic if required
    if choose_companion and companion_cards:
        # Evaluate each companion card move
        best_score = -inf
        best_move = None

        for companion in companion_cards.keys():
            # Create a simulated move for this companion card
            current_cards = copy.deepcopy(cards)
            current_player1 = copy.deepcopy(player1)
            current_player2 = copy.deepcopy(player2)

            # Simulate the companion card action
            move = [companion]
            make_companion_move(current_cards, companion_cards, move, current_player1)

            score = getScore(current_cards, current_player1, current_player2, turn=1)
            if score > best_score:
                best_score = score
                best_move = move

        return best_move

    player1_copy = copy.deepcopy(player1)
    player2_copy = copy.deepcopy(player2)

    result = minimax(player1_copy, player2_copy, cards, limit, -inf, inf, 1)
    return result[0]


























    # def get_move(cards, player1, player2):
    #     '''
    #     This function gets the move of the player.

    #     Parameters:
    #         cards (list): List of Card objects.
    #         player1 (Player): The player.
    #         player2 (Player): The opponent.

    #     Returns:
    #         move (int): The move of the player.
    #     '''

    #     limit = 5 # Depth limit
        
    #     player1_copy = copy.copy(player1)
    #     player2_copy = copy.copy(player2)

    #     result = minimax(player1_copy, player2_copy, cards, limit, -inf, inf, 1)
    #     return result[0]