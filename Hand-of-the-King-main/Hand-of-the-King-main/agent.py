from math import inf
import copy
from main import make_move, get_possible_moves, print_cards_status, set_banners

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

def get_neighbors(location, row_size=6):
    '''
    Get the neighboring card locations in the same row and column.

    Parameters:
        location (int): The location of the card on the board.
        row_size (int): The number of columns in the board (default 6).

    Returns:
        neighbors (list): List of neighboring locations.
    '''
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

def heuristic(player, opponent, cards, varys_location, weights):
    '''
    Compute a score for the current board state with a focus on capturing banners.

    Parameters:
        player (Player): The current player.
        opponent (Player): The opponent player.
        cards (list): List of Card objects.
        varys_location (int): Location of Varys.
        weights (dict): Weights for scoring factors.

    Returns:
        score (float): Calculated score for the current player.
    '''
    house_priority = {
    "Stark": 7,
    "Greyjoy": 6,
    "Lannister": 5,
    "Targaryen": 4,
    "Baratheon": 3,
    "Tyrell": 2,
    "Tully": 1,
}
    banners = player.get_banners()
    opponent_banners = opponent.get_banners()
    score = 0

    for card in cards:
        house = card.get_house()
        location = card.get_location()

        # Check if capturing this card would secure a banner
        if banners.get(house, 0) <  house_priority.get(house, 3) :
            score += weights["capture_banner_bonus"]

        # Row and column priority
        neighbors = get_neighbors(location)
        for neighbor_loc in neighbors:
            neighbor_card = next((c for c in cards if c.get_location() == neighbor_loc), None)
            if neighbor_card and neighbor_card.get_house() == house:
                score += weights["row_col_priority"]

        # General banner count
        score += banners.get(house, 0) * weights["general_banner_weight"]

    return score

def getScore(cards, player1, player2, turn, weights):
    '''
    Evaluate the score of the game state.

    Parameters:
        cards (list): List of Card objects.
        player1 (Player): Player 1.
        player2 (Player): Player 2.
        turn (int): Current player's turn.
        weights (dict): Weights for scoring factors.

    Returns:
        score (float): Calculated score.
    '''
    if len(cards) == 0:  # Game over condition
        if calculate_winner(player1, player2) == 1:
            return 10e9
        elif calculate_winner(player1, player2) == 2:
            return -10e9
    else:
        varys_location = find_varys(cards)
        if turn == 1:
            return heuristic(player1, player2, cards, varys_location, weights)
        else:
            return -heuristic(player2, player1, cards, varys_location, weights)

def minimax(player1, player2, cards, depth, alpha, beta, player, weights):
    '''
    Perform the minimax algorithm with alpha-beta pruning.

    Parameters:
        player1 (Player): Player 1.
        player2 (Player): Player 2.
        cards (list): List of Card objects.
        depth (int): Maximum depth to explore.
        alpha (float): Alpha value for pruning.
        beta (float): Beta value for pruning.
        player (int): Current player's turn.
        weights (dict): Weights for scoring factors.

    Returns:
        list: Best move and its score.
    '''
    move = None

    if depth == 0 or len(cards) == 0:  # Either hit depth limit or game over
        return [move, getScore(cards, player1, player2, player, weights)]

    for moves in get_possible_moves(cards):
        current_cards = copy.deepcopy(cards)
        current_player1_status = copy.deepcopy(player1)
        current_player2_status = copy.deepcopy(player2)

        if player == 1:
            make_move(cards, moves, player1)
        else:
            make_move(cards, moves, player2)

        score = minimax(player1, player2, cards, depth - 1, alpha, beta, -player, weights)
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
    limit = 3  # Depth limit
    weights = {
        "capture_banner_bonus": 10.0,  # High priority for securing banners
        "row_col_priority": 5.0,       # Moderate priority for row/column moves
        "general_banner_weight": 2.0   # Low priority for general banner count
    }

    player1_copy = copy.deepcopy(player1)
    player2_copy = copy.deepcopy(player2)

    result = minimax(player1_copy, player2_copy, cards, limit, -inf, inf, 1, weights)
    print("Best move: ", result[0])
    return result[0]
