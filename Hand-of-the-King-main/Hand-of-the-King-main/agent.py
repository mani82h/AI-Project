from math import inf
import copy
from main import make_move, get_possible_moves, print_cards_status, set_banners

houses = ["Stark", "Greyjoy", "Lannister", "Targaryen", "Baratheon", "Tyrell", "Tully"]

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
    "capture_banner_bonus": 20.0,  # High priority for securing banners
    "row_col_priority": 3.0,       # Moderate priority for row/column moves
    "general_banner_weight": 1.0,  # Low priority for general banner count
    "house_variance_weight": 0.5   # Weight for house variance
}

def find_varys(cards):
    varys = [card for card in cards if card.get_name() == 'Varys']
    varys_location = varys[0].get_location()
    return varys_location

def get_neighbors(location, row_size=6):
    neighbors = []
    row, col = divmod(location, row_size)

    for r in range(6):
        if r != row:
            neighbors.append(r * row_size + col)
    for c in range(row_size):
        if c != col:
            neighbors.append(row * row_size + c)

    return neighbors

def house_weight_change(player, opponent, house):
    alpha = 1.0
    
    if player + 1 > house_member_count[house] // 2:
        return 0.0
    
    elif player - opponent < 0:
        alpha = -1.0

    return alpha * (player - opponent) ** 2 / (house_member_count[house]) ** 2 

def cards_position(cards):
    cards_location = {}

    for card in cards:
        if card.get_name() == 'Varys':
            continue

        x = card.get_location() // 6
        y = card.get_location() % 6
        card_house = card.get_house()

        if card_house not in cards_location:
            cards_location[card_house] = [(x, y)]
        else:
            cards_location[card_house].append((x, y))

    return cards_location

def cards_variance_based_on_axis(cards_location, axis=0):
    variance_of_cards_location = {}

    for house, positions in cards_location.items():
        axis_values = [pos[axis] for pos in positions]
        avg = sum(axis_values) / len(axis_values)

        variance = sum((value - avg) ** 2 for value in axis_values) / len(axis_values)
        variance_of_cards_location[house] = variance

    return variance_of_cards_location

def house_variance(cards):
    cards_location = cards_position(cards)
    
    variance_x = cards_variance_based_on_axis(cards_location, 0)
    variance_y = cards_variance_based_on_axis(cards_location, 1)

    total_variance = {}

    for house in houses:
        if house in variance_x and house in variance_y:
            total_variance[house] = variance_x[house] + variance_y[house]
            
    return total_variance

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

def bannerDifferenceScore(player1, player2):
    banners = player1.get_banners()
    opponent_banners = player2.get_banners()
    results = 0
    for house in houses:
        results += (banners[house] - opponent_banners[house])
    return results

def who_has_more(player1, player2):
    banners = player1.get_banners()
    opponent_banners = player2.get_banners()
    results = 0
    for house in houses:
        if banners[house] > house_member_count[house] // 2:
            results += -2
        elif banners[house] > opponent_banners[house]:
            results += 1
    return results

def getScore(cards, player1, player2, turn):
    if len(cards) == 0:
        if calculate_winner(player1, player2) == 1:
            return 10e9
        elif calculate_winner(player1, player2) == 2:
            return -10e9
    else:
        varys_location = find_varys(cards)
        if turn == 1:
            return 50.0 * who_has_more(player1, player2) + 15.0 * bannerDifferenceScore(player1, player2) + heuristic(player1, player2, cards, varys_location)
        else:
            return -50.0 * who_has_more(player2, player1) + -15.0 * bannerDifferenceScore(player2, player1) - heuristic(player2, player1, cards, varys_location)

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

    limit = 5 # Depth limit
    
    player1_copy = copy.copy(player1)
    player2_copy = copy.copy(player2)

    result = minimax(player1_copy, player2_copy, cards, limit, -inf, inf, 1)
    return result[0]