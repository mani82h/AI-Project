from math import inf
import copy
from main import make_move, get_possible_moves, print_cards_status, set_banners

house_priority = { # this should be adjusted dynamically by how accessible
    "Stark": 7,
    "Greyjoy": 6,
    "Lannister": 5,
    "Targaryen": 4,
    "Baratheon": 3,
    "Tyrell": 2,
    "Tully": 1,
}

house_member_count = {
    "Stark": 8,
    "Greyjoy": 7,
    "Lannister": 6,
    "Targaryen": 5,
    "Baratheon": 4,
    "Tyrell": 3,
    "Tully": 2,
}

weights = {
    "capture_banner_bonus": 10.0,  # High priority for securing banners
    "row_col_priority": 5.0,       # Moderate priority for row/column moves
    "general_banner_weight": 2.0,   # Low priority for general banner count
    "house_variance": 2.0 
}

house_name_values = {'Stark': 1, 'Greyjoy': 2, 'Lannister': 3, 'Targaryen': 4, 'Baratheon': 5, 'Tyrell': 6, 'Tully': 7}
house_name_keys = {1: 'Stark', 2: 'Greyjoy', 3: 'Lannister', 4: 'Targaryen', 5: 'Baratheon', 6: 'Tyrell', 7: 'Tully'}

def find_varys(cards):
    varys = [card for card in cards if card.get_name() == 'Varys']
    varys_location = varys[0].get_location()
    return varys_location

def get_neighbors(location, row_size=6):
    neighbors = []
    row, col = divmod(location, row_size)

    # Add neighbors in the same column
    for r in range(6):
        if r != row:
            neighbors.append(r * row_size + col)

    # Add neighbors in the same row
    for c in range(row_size):
        if c != col:
            neighbors.append(row * row_size + c)

    return neighbors

def cards_position(cards): # return each cards position, a dictonary containing with key: house, value: cards of that house
    cards_location = {}

    for i in range(len(cards)):
        if cards[i].get_name() == 'Varys':
            continue
        
        x = cards[i].get_location() // 6
        y = cards[i].get_location() % 6
        card_house = house_name_values[cards[i].get_house()]

        if card_house not in cards_location:
            cards_location[card_house] = [(x, y)]
        else:
            cards_location[card_house].append((x, y))

    return cards_location

def cards_variance_based_on_axis(cards_location, axis=0):
    variance_of_cards_location = {}

    for i in range(1, 8):
        if i in cards_location:
            card = cards_location[i]

            axis_values = [pos[axis] for pos in card]
            avg = sum(axis_values) / len(axis_values)
            variance = sum((value - avg) ** 2 for value in axis_values) / len(axis_values)

            variance_of_cards_location[i] = variance
    
    return variance_of_cards_location

def house_weights(cards): # house weights based on axis variance
    cards_location = cards_position(cards)
    cards_axis_0 = cards_variance_based_on_axis(cards_location, 0)
    cards_axis_1 = cards_variance_based_on_axis(cards_location, 1)

    alpha = 10.0

    for i in range(1, 8):
        house = house_name_keys[i]
        if i in cards_axis_0 and i in cards_axis_1 and cards_axis_0[i] != 0 and cards_axis_1[i] != 0:
            house_priority[house] = alpha / cards_axis_0[i] * cards_axis_1[i]
        
        elif (i in cards_axis_0 and cards_axis_0[i] == 0) or (i in cards_axis_1 and cards_axis_1[i] == 0):
            house_priority[house] = 10e2

    return house_priority

def heuristic(player, opponent, cards, varys_location):
    banners = player.get_banners()
    opponent_banners = opponent.get_banners()
    score = 0

    for card in cards:
        if card.get_name() == 'Varys':
            continue

        house = card.get_house()
        location = card.get_location()

        # Check if capturing this card would secure a banner
        if banners.get(house) + 1 >= opponent_banners.get(house):
            count = house_member_count[house]
            if banners.get(house, 0) >= (count // 2 + 1): # this means even if the opponent tries to get all the cards from this house it won't eventually benefit anything
                score += 0
            else:
                score += weights["capture_banner_bonus"]

        # Row and column priority
        neighbors = get_neighbors(location)
        for neighbor_loc in neighbors:
            neighbor_card = next((c for c in cards if c.get_location() == neighbor_loc), None)
            if neighbor_card and neighbor_card.get_house() == house:
                score += weights["row_col_priority"]

        # General banner count
        score += banners.get(house, 0) * weights["general_banner_weight"]

        score += house_priority[house] * weights["house_variance"]

        # we definitely need a heuristic for blocking opponent moves

    return score

def getScore(cards, player1, player2, turn):
    if len(cards) == 0:  # Game over condition
        if calculate_winner(player1, player2) == 1: # in this case i guess player2 should be our agent
            return 10e9
        elif calculate_winner(player1, player2) == 2:
            return -10e9
    else:
        varys_location = find_varys(cards)
        if turn == 1:
            return heuristic(player1, player2, cards, varys_location)
        else:
            return -heuristic(player2, player1, cards, varys_location)

def minimax(player1, player2, cards, depth, alpha, beta, player):
    move = None

    if depth == 0 or len(cards) == 0:  # Either hit depth limit or game over
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
    
    if move == None:
        print("Null move!")

    if player == 1:
        return [move, alpha]
    else:
        return [move, beta]

def get_move(cards, player1, player2):
    '''
    This function gets the move of the player.

    Parameters:
        cards (list): List of Card objects.
        player1 (Player): The player.
        player2 (Player): The opponent.

    Returns:

        move (int): The move of the player.
    '''

    house_priority = house_weights(cards)

    limit = 4 # Depth limit
    
    player1_copy = copy.deepcopy(player1)
    player2_copy = copy.deepcopy(player2)

    result = minimax(player1_copy, player2_copy, cards, limit, -inf, inf, 1)
    print("Best move: ", result[0])
    return result[0]