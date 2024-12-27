from math import inf
import copy
from main import make_move, get_possible_moves, print_cards_status, set_banners

house_priority = {  # This should be adjusted dynamically by how accessible
    "Stark": 7,
    "Greyjoy": 6,
    "Lannister": 5,
    "Targaryen": 4,
    "Baratheon": 3,
    "Tyrell": 2,
    "Tully": 1,
}

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
    "capture_banner_bonus": 30.0,  # High priority for securing banners
    "row_col_priority": 2.0,       # Moderate priority for row/column moves
    "general_banner_weight": 2.0   # Low priority for general banner count
}


def find_varys(cards):
    varys = [card for card in cards if card.get_name() == 'Varys']
    varys_location = varys[0].get_location()
    return varys_location


def get_neighbors(location, row_size=6):
    neighbors = set()
    row, col = divmod(location, row_size)

    # Add neighbors in the same column
    for r in range(6):
        if r != row:
            neighbors.add(r * row_size + col)

    # Add neighbors in the same row
    for c in range(row_size):
        if c != col:
            neighbors.add(row * row_size + c)

    return frozenset(neighbors)  # Return an immutable, hashable set


def house_weight_change(player, opponent, house):
    alpha = 1.0

    if player + 1 > house_member_count[house] // 2:
        return 0.0
    elif player - opponent < 0:
        alpha = -1.0

    return alpha * (player - opponent) ** 2 / (house_member_count[house]) ** 2


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
            # even if count is even we're good to go
            count = house_member_count[house]
            # this means even if the opponent tries to get all the cards from this house it won't eventually benefit anything
            if banners.get(house) + 1 >= (count // 2 + 1):
                score -= 15.0
            else:
                score += weights["capture_banner_bonus"]

        # Row and column priority, this shit is wrong
        neighbors = get_neighbors(location)
        for neighbor_loc in neighbors:
            neighbor_card = next(
                (c for c in cards if c.get_location() == neighbor_loc), None)
            if neighbor_card and neighbor_card.get_house() == house:
                score += weights["row_col_priority"]

        # General banner count
        # score += banners.get(house, 0) * weights["general_banner_weight"]
        score += banners.get(house, 0) * house_weight_change(
            banners.get(house), opponent_banners.get(house), house)

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
        if banners[house] > opponent_banners[house]:
            results += 1

    return results


def getScore(cards, player1, player2, turn):
    if len(cards) == 0:  # Game over condition
        # In this case, I guess player2 should be our agent
        if calculate_winner(player1, player2) == 1:
            return 10e9
        elif calculate_winner(player1, player2) == 2:
            return -10e9
    else:
        varys_location = find_varys(cards)
        if turn == 1:
            # The len part should be in a function to be multiplied by weights as well
            return 5 * who_has_more(player1, player2) + 1.5 * bannerDifferenceScore(player1, player2) + heuristic(player1, player2, cards, varys_location)
        else:
            return -5 * who_has_more(player1, player2) + -1.5 * bannerDifferenceScore(player1, player2) - heuristic(player2, player1, cards, varys_location)


transposition_table = {}
def hash_board(cards):
    """Generate a unique hash for the current board state (using card locations or other attributes)."""
    # You can adapt this to create a hash based on the state of your game board.
    # Assuming locations are sufficient for hashing
    return tuple(card.get_location() for card in cards)
def minimax(player1, player2, cards, depth, alpha, beta, player):
    move = None
    # Check Transposition Table (memoization)
    board_hash = hash_board(cards)
    if board_hash in transposition_table:
        return [move, transposition_table[board_hash]]

    if depth == 0 or len(cards) == 0:  # Either hit depth limit or game over
        score = getScore(cards, player1, player2, player)
        # Store result in Transposition Table
        transposition_table[board_hash] = score
        return [move, score]

    for moves in get_possible_moves(cards):
        current_cards = copy.deepcopy(cards)
        current_player1_status = copy.deepcopy(player1)
        current_player2_status = copy.deepcopy(player2)

        if player == 1:
            make_move(cards, moves, player1)
        else:
            make_move(cards, moves, player2)

        score = minimax(player1, player2, cards,
                        depth - 1, alpha, beta, -player)

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

    # Store the score for this position in Transposition Table
    if player == 1:
        transposition_table[board_hash] = alpha
        return [move, alpha]
    else:
        transposition_table[board_hash] = beta
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

    limit = 1  # Depth limit

    player1_copy = copy.deepcopy(player1)
    player2_copy = copy.deepcopy(player2)

    result = minimax(player1_copy, player2_copy, cards, limit, -inf, inf, 1)
    # print("Best move: ", result[0])
    return result[0]
