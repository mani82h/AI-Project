from math import inf
import random
import copy
from main import make_move, get_possible_moves, print_cards_status, set_banners

# Constants
houses = ["Stark", "Greyjoy", "Lannister",
          "Targaryen", "Baratheon", "Tyrell", "Tully"]
house_member_count = {
    "Stark": 8, "Greyjoy": 7, "Lannister": 6, "Targaryen": 5,
    "Baratheon": 4, "Tyrell": 3, "Tully": 2,
}

def find_varys(cards):
    for i, card in enumerate(cards):
        if card.get_name() == 'Varys':
            return i
    return None

def getScore(cards, player1, player2, player):
    """Returns 1/-1 for win/loss, 0 for tie/during gameplay"""
    if not game_over(cards):
        return 0  # No heuristic evaluation for non-terminal states
        
    p1_banners = sum(player1.get_banners().values())
    p2_banners = sum(player2.get_banners().values())
    
    if p1_banners > p2_banners:
        return 1 if player == 1 else -1
    elif p2_banners > p1_banners:
        return -1 if player == 1 else 1
    return 0

def minimax(player1, player2, cards, depth, alpha, beta, player):
    move = None

    if depth == 0 or game_over(cards):
        return [move, getScore(cards, player1, player2, player)]

    for moves in get_possible_moves(cards):
        current_cards = copy.deepcopy(cards)
        current_p1 = copy.deepcopy(player1)
        current_p2 = copy.deepcopy(player2)

        if player == 1:
            make_move(current_cards, moves, current_p1)
        else:
            make_move(current_cards, moves, current_p2)

        score = minimax(current_p1, current_p2, current_cards, depth-1, alpha, beta, -player)
        
        if player == 1:
            if score[1] > alpha:
                alpha = score[1]
                move = moves
                if alpha >= beta:
                    break
        else:
            if score[1] < beta:
                beta = score[1]
                move = moves
                if alpha >= beta:
                    break

    return [move, alpha] if player == 1 else [move, beta]

def get_valid_ramsay(cards):
    return [card.get_location() for card in cards]

def get_valid_jon_sandor_jaqan(cards):
    return [card.get_location() for card in cards if card.get_name() != 'Varys']

def get_move(cards, player1, player2, companion_cards=None, choose_companion=True):
    """Hybrid strategy: Random companion selection + minimax for regular moves"""
    if choose_companion and companion_cards:
        selected_companion = random.choice(list(companion_cards.keys()))
        move = [selected_companion]
        choice_type = companion_cards[selected_companion]['Choice']

        valid_moves = []
        if choice_type == 1:  # Jon Snow-style
            valid_moves = get_valid_jon_sandor_jaqan(cards)
        elif choice_type == 2:  # Ramsay-style
            valid_moves = get_valid_ramsay(cards)
        elif choice_type == 3:  # Jaqen-style
            valid_moves = get_valid_jon_sandor_jaqan(cards)

        if valid_moves:
            if choice_type in [2, 3] and len(valid_moves) >= 2:
                move.extend(random.sample(valid_moves, 2))
            else:
                move.append(random.choice(valid_moves))
            
            if choice_type == 3:
                move.append(random.choice(list(companion_cards.keys())))

        return move

    # Use depth-limited minimax for regular moves
    depth = 3  # Reduced depth for performance
    result = minimax(player1, player2, cards, depth, -inf, inf, 1)
    return result[0]

def game_over(cards):
    return len(cards) == 0

def calculate_winner(player1, player2):
    p1_score = sum(player1.get_banners().values())
    p2_score = sum(player2.get_banners().values())
    
    if p1_score > p2_score:
        return "Player 1"
    elif p2_score > p1_score:
        return "Player 2"
    return "Tie"

def play_game(player1, player2, cards):
    turn_counter = 0
    while not game_over(cards):
        current_player = player1 if turn_counter % 2 == 0 else player2
        move = get_move(cards, player1, player2)
        
        if not move:
            break
            
        make_move(cards, move, current_player)
        turn_counter += 1

    winner = calculate_winner(player1, player2)
    print(f"Final banners - P1: {sum(player1.get_banners().values())}, P2: {sum(player2.get_banners().values())}")
    print(f"Game result: {winner}")
    return winner

# Example usage
if __name__ == "__main__":
    from main import initialize_game  # Assuming this exists
    player1, player2, cards = initialize_game()
    winner = play_game(player1, player2, cards)