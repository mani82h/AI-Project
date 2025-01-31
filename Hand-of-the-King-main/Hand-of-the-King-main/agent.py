from math import inf
import copy
import random
from main import load_board, make_move, get_possible_moves, print_cards_status, save_board, set_banners

houses = ["Stark", "Greyjoy", "Lannister",
          "Targaryen", "Baratheon", "Tyrell", "Tully"]

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

        variance = sum((value - avg) **
                       2 for value in axis_values) / len(axis_values)
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
            neighbor_card = next(
                (c for c in cards if c.get_location() == neighbor_loc), None)
            if neighbor_card and neighbor_card.get_house() == house:
                score += weights["row_col_priority"]

        # General banner count
        score += banners.get(house, 0) * house_weight_change(
            banners.get(house), opponent_banners.get(house), house)

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


def calculate_winner(player1, player2):
    player1_banners = player1.get_banners()
    player2_banners = player2.get_banners()
    player1_score = sum(player1_banners.values())
    player2_score = sum(player2_banners.values())

    if player1_score > player2_score:
        return 1
    elif player2_score > player1_score:
        return 2
    else:
        return 0


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


def minimax(player1, player2, cards, depth, alpha, beta, player, transposition_table=None):
    if transposition_table is None:
        transposition_table = {}

    # Generate state hash
    cards_state = tuple(sorted(
        (card.get_house(), card.get_name(), card.get_location()) for card in cards))

    # Corrected: Iterate over houses and their card lists for player1
    p1_cards = tuple(sorted(
        (card.get_house(), card.get_name(), card.get_location())
        for house in player1.get_cards()  # Iterate over houses
        # Then iterate over cards in each house
        for card in player1.get_cards()[house]
    ))

    # Similarly for player2
    p2_cards = tuple(sorted(
        (card.get_house(), card.get_name(), card.get_location())
        for house in player2.get_cards()
        for card in player2.get_cards()[house]
    ))

    p1_banners = tuple(sorted(player1.get_banners().items()))
    p2_banners = tuple(sorted(player2.get_banners().items()))

    state_hash = (cards_state, (p1_banners, p1_cards), (p2_banners, p2_cards))
    key = (state_hash, player)

    if key in transposition_table:
        return transposition_table[key]

    move = None

    # Terminal condition: return heuristic score
    if depth == 0 or len(cards) == 0:
        score = getScore(cards, player1, player2, player)
        transposition_table[key] = (move, score)
        return (move, score)

    # Evaluate moves recursively
    for possible_move in get_possible_moves(cards):
        # Deep copy the game state to simulate the move
        copied_cards = copy.deepcopy(cards)
        copied_p1 = copy.deepcopy(player1)
        copied_p2 = copy.deepcopy(player2)

        # Apply the move
        if player == 1:
            make_move(copied_cards, possible_move, copied_p1)
        else:
            make_move(copied_cards, possible_move, copied_p2)

        # Recursive Minimax call
        _, score = minimax(copied_p1, copied_p2, copied_cards,
                           depth - 1, alpha, beta, -player, transposition_table)

        # Update alpha/beta
        if player == 1:
            if score > alpha:
                alpha = score
                move = possible_move
            if alpha >= beta:
                break  # Alpha-beta pruning
        else:
            if score < beta:
                beta = score
                move = possible_move
            if beta <= alpha:
                break  # Alpha-beta pruning

    # Store result in transposition table
    result = (move, alpha) if player == 1 else (move, beta)
    transposition_table[key] = result
    return result


def get_valid_ramsay(cards):
    '''
    This function gets the possible moves for Ramsay.

    Parameters:
        cards (list): list of Card objects

    Returns:
        moves (list): list of possible moves
    '''

    moves = []

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

    moves = []

    for card in cards:
        if card.get_name() != 'Varys':
            moves.append(card.get_location())

    return moves

def get_move(cards, player1, player2, companion_cards=None, choose_companion=True):
    # Depth limit for minimax
    limit = 3

    if choose_companion:
        if companion_cards:
            current_banners = player2.get_banners()
            opponent_banners = player1.get_banners()

            # Calculate row/column control
            your_rows = [sum(1 for card in cards if (card.get_location() // 6) == r and card.get_house() == house)
                         for r in range(6) for house in current_banners]
            your_cols = [sum(1 for card in cards if (card.get_location() % 6) == c and card.get_house() == house)
                         for c in range(6) for house in current_banners]

            needed_to_secure = 4  # Majority in 6-row/col
            nearly_secured_rows = sum(
                1 for count in your_rows if count == needed_to_secure - 1)
            nearly_secured_cols = sum(
                1 for count in your_cols if count == needed_to_secure - 1)

            # Initialize weights for ALL possible companions using correct keys
            companion_weights = {
                companion: 1.0  # Base weight
                for companion in companion_cards.keys()
            }

            if nearly_secured_rows + nearly_secured_cols > 0:
              if 'Melisandre' in companion_weights: 
                companion_weights['Melisandre'] += 50 * \
                    (nearly_secured_rows + nearly_secured_cols)

            for house in current_banners:
                needed = (house_member_count[house] // 2) + 1
                if (current_banners.get(house, 0) + 1) >= needed and 'Sandor' in companion_weights:
                    companion_weights['Sandor'] += 40  

            if "Baratheon" in current_banners and "Baratheon" in opponent_banners:
                if current_banners["Baratheon"] == 2 and opponent_banners["Baratheon"] == 2:
                    companion_weights['Gendry'] += 1000  
            jaqen_weight_boost = 0
            if 'Gendry' in companion_weights:
                if current_banners.get("Baratheon", 0) == 2 and opponent_banners.get("Baratheon", 0) == 2:
                    companion_weights['Gendry'] += 1000
            target_houses = []
            for house in current_banners:
                needed = (house_member_count[house] // 2) + 1
                if (current_banners.get(house, 0) + 1) >= needed:
                    target_houses.append(house)
                    if 'Jon' in companion_weights: 
                        companion_weights['Jon'] += 50
            save_board(cards, 'current_strategy_board')

        # Load fresh board state to ensure accuracy
            current_board, _ = load_board('current_strategy_board')
            location_house_map = {card.get_location(): card.get_house() for card in current_board}            # Select companion with highest weight
            selected_companion = max(
                companion_weights, key=companion_weights.get, default=None)

            move = [selected_companion]
            choices = companion_cards[selected_companion]['Choice']

            # Handle choices based on companion type
            if choices == 1:  # Jon-style
                valid_moves = get_valid_jon_sandor_jaqan(cards)
                if valid_moves:
                    current_houses = {card.get_location(): card.get_house() for card in cards}
                    # Prioritize locations that complete house majorities
                    priority_moves = [
                        loc for loc in valid_moves
                        if current_houses.get(loc) in target_houses
                    ]
                    if not priority_moves:
                        priority_moves = sorted(
                            valid_moves,
                            key=lambda loc: (needed_to_secure - your_rows[loc//6], 
                                           needed_to_secure - your_cols[loc%6])
                        )
                    move.append(priority_moves[0] if priority_moves else valid_moves[0])

            elif choices == 2:  # Ramsay-style
                valid_moves = get_valid_ramsay(cards)
                if valid_moves:
                    # Strategic swap logic
                    current_banners = player2.get_banners()
                    opponent_banners = player1.get_banners()
                    
                    # 1. Find overcrowded rows/columns with 3+ same house cards but no banner control
                    overcrowded = []
                    for i in range(6):
                        # Check rows
                        row = [card for card in cards if card.get_location() // 6 == i]
                        houses = {}
                        for card in row:
                            if card.get_house() in houses:
                                houses[card.get_house()] += 1
                            else:
                                houses[card.get_house()] = 1
                        for house, count in houses.items():
                            if count >= 3 and current_banners.get(house, 0) < (house_member_count[house] // 2) + 1:
                                overcrowded.extend([card.get_location() for card in row if card.get_house() == house])
                        
                        # Check columns
                        col = [card for card in cards if card.get_location() % 6 == i]
                        houses = {}
                        for card in col:
                            if card.get_house() in houses:
                                houses[card.get_house()] += 1
                            else:
                                houses[card.get_house()] = 1
                        for house, count in houses.items():
                            if count >= 3 and current_banners.get(house, 0) < (house_member_count[house] // 2) + 1:
                                overcrowded.extend([card.get_location() for card in col if card.get_house() == house])

                    # 2. Find contested houses (tie or ±1 banner difference)
                    contested_houses = [
                        house for house in houses 
                        if abs(current_banners.get(house, 0) - opponent_banners.get(house, 0)) <= 1
                    ]
                    final_moves = []
                    # Select top 2 prioritized moves
                    if len(final_moves) >= 2:
                        move.extend(final_moves[:2])
                    elif valid_moves:
                        # Fallback to first two valid moves (non-random)
                        move.extend(valid_moves[:2])
            elif choices == 3:  # Jaqen-style
                if 'Jaqen' in companion_weights:
                    enemy_strongholds = [
                        card.get_location() for card in cards
                        if (your_rows[card.get_location() // 6] >= needed_to_secure - 1 or
                            your_cols[card.get_location() % 6] >= needed_to_secure - 1)
                    ]
                    jaqen_weight_boost = 30 * len(enemy_strongholds)

                    if len(companion_cards) >= 2:
                        jaqen_weight_boost += 40

                    companion_weights['Jaqen'] += jaqen_weight_boost

                valid_moves = get_valid_jon_sandor_jaqan(cards)
                if valid_moves:
                    prioritized_moves = [
                        loc for loc in valid_moves
                        if any(card.get_location() == loc for card in cards 
                               if card.get_house() in opponent_banners)
                    ]
                    
                    if len(prioritized_moves) >= 2:
                        move.extend(prioritized_moves[:2])
                    else:
                        move.extend(random.sample(
                            valid_moves, min(2, len(valid_moves)))
                        )
            return move
        else:
            return []

    player1_copy = copy.copy(player1)
    player2_copy = copy.copy(player2)
    result = minimax(player1_copy, player2_copy, cards,
                     limit, -inf, inf, -1, transposition_table={})
    return result[0]
