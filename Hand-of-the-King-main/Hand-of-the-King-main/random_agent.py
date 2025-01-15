import random

def find_varys(cards):
    '''
    This function finds the location of Varys on the board.

    Parameters:
        cards (list): list of Card objects

    Returns:
        varys_location (int): location of Varys
    '''
    varys = [card for card in cards if card.get_name() == 'Varys']
    if varys:  # Check if Varys exists in the list
        return varys[0].get_location()
    return None  # If Varys is not found


def get_valid_moves(cards):
    '''
    This function gets the possible moves for the player.

    Parameters:
        cards (list): list of Card objects

    Returns:
        moves (list): list of possible moves
    '''
    varys_location = find_varys(cards)

    if varys_location is None:
        return []  # No moves are possible if Varys is not found

    # Get the row and column of Varys
    varys_row, varys_col = varys_location // 6, varys_location % 6

    moves = []

    # Get the cards in the same row or column as Varys
    for card in cards:
        if card.get_name() == 'Varys':
            continue

        row, col = card.get_location() // 6, card.get_location() % 6

        if row == varys_row or col == varys_col:
            moves.append(card.get_location())

    return moves


def get_move(cards, player1, player2, companion_cards=None, choose_companion=False):
    '''
    This function gets the move of the random agent.

    Parameters:
        cards (list): list of Card objects
        player1 (Player): the player
        player2 (Player): the opponent
        companion_cards (dict): dictionary of companion cards (optional)
        choose_companion (bool): flag to choose a companion card (optional)
    
    Returns:
        move (list): The move of the player as a list.
    '''
    if choose_companion and companion_cards:
        # Randomly select a companion card if choosing companion
        companion_card_name = random.choice(list(companion_cards.keys()))
        return [companion_card_name]  # Return as a list for consistency

    # Get valid moves for Varys
    valid_moves = get_valid_moves(cards)

    if not valid_moves:
        return None  # No valid moves available

    # Randomly select a move from the valid moves
    selected_move = random.choice(valid_moves)
    return [selected_move]  # Wrap the move in a list for consistency
