import random
import os
import copy
from collections import defaultdict
from math import inf
from main import get_possible_moves, calculate_winner, make_move, print_cards_status, set_banners
from utils.classes import Card, Player

# Define the houses variable
houses = ["Stark", "Greyjoy", "Lannister",
          "Targaryen", "Baratheon", "Tyrell", "Tully"]

# Configuration parameters
LEARNING_RATE = 0.8
DISCOUNT_FACTOR = 0.9
Q_TABLE_FILE = "q_table.txt"

# Heuristic weights configuration
weights = {
    "capture_banner_bonus": 20.0,
    "row_col_priority": 3.0,
    "general_banner_weight": 1.0,
    "house_variance_weight": 0.5
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


class ReinforcementLearningAgent:
    def __init__(self):
        self.q_table = self.load_q_table()
        self.state_history = []
        self.move_history = []

    def load_q_table(self):
        q_table = defaultdict(lambda: defaultdict(float))
        if os.path.exists(Q_TABLE_FILE):
            with open(Q_TABLE_FILE, 'r') as f:
                for line in f:
                    state_key, move, value = line.strip().split(',')
                    q_table[state_key][move] = float(value)
        return q_table

    def save_q_table(self):
        with open(Q_TABLE_FILE, 'w') as f:
            for state_key, moves in self.q_table.items():
                for move, value in moves.items():
                    f.write(f"{state_key},{move},{value}\n")

    def get_state_key(self, cards, player1, player2):
        state = []
        for card in cards:
            if card.get_name() != 'Varys':
                state.append((card.get_house(), card.get_location()))
        state.extend([(house, player1.get_banners()[house])
                     for house in houses])
        state.extend([(house, player2.get_banners()[house])
                     for house in houses])
        return str(sorted(state))

    def get_q_value(self, state_key, move):
        return self.q_table[state_key][str(move)]

    def update_q_value(self, state_key, move, reward):
        move_key = str(move)
        current_q = self.q_table[state_key][move_key]
        self.q_table[state_key][move_key] = current_q + \
            LEARNING_RATE * (reward - current_q)

    def calculate_reward(self, player1, player2, last_move, cards):
        reward = 0

        # Capture banner bonus
        if last_move:
            target_card = next(
                (c for c in cards if c.get_location() == last_move), None)
            if target_card and target_card.owner != player1:
                reward += weights["capture_banner_bonus"]

        # Row/column control bonus
        varys_loc = next((c.get_location()
                         for c in cards if c.get_name() == 'Varys'), None)
        if varys_loc:
            row = varys_loc // 6
            col = varys_loc % 6
            reward += len([c for c in cards if c.get_location() //
                          6 == row]) * weights["row_col_priority"]
            reward += len([c for c in cards if c.get_location() %
                          6 == col]) * weights["row_col_priority"]

        # General banner count
        banner_diff = sum(player1.get_banners().values()) - \
            sum(player2.get_banners().values())
        reward += banner_diff * weights["general_banner_weight"]

        # House variance
        banner_counts = list(player1.get_banners().values())
        if banner_counts:
            mean = sum(banner_counts) / len(banner_counts)
            variance = sum(
                (x - mean) ** 2 for x in banner_counts) / len(banner_counts)
            reward += variance * weights["house_variance_weight"]

        return reward

    def heuristic(self, player, opponent, cards, varys_location):
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
            score += banners.get(house, 0) * self.house_weight_change(
                banners.get(house), opponent_banners.get(house), house)

            # House variance
            if house in house_variances:
                score -= house_variances[house] * \
                    weights["house_variance_weight"]

        return score

    def minimax(self, player1, player2, cards, depth, alpha, beta, player):
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

            score = self.minimax(player1, player2, cards,
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

        if player == 1:
            return [move, alpha]
        else:
            return [move, beta]


def house_weight_change(player_banner_count, opponent_banner_count, house):
    """Calculate weight change for a house based on banner counts"""
    if player_banner_count > opponent_banner_count:
        return 1.5
    elif player_banner_count < opponent_banner_count:
        return 0.5
    return 1.0


def find_varys(cards):
    """Find the location of Varys card"""
    for card in cards:
        if card.get_name() == 'Varys':
            return card.get_location()
    return None


def get_neighbors(location, cards):
    neighbors = []
    varys_loc = find_varys(cards)
    row, col = location // 6, location % 6

    # Check the four possible neighbors (up, down, left, right)
    if row > 0:  # Up
        neighbors.append(location - 6)
    if row < 5:  # Down
        neighbors.append(location + 6)
    if col > 0:  # Left
        neighbors.append(location - 1)
    if col < 5:  # Right
        neighbors.append(location + 1)

    return neighbors


def get_valid_moves(cards):
    """Get valid moves based on Varys location"""
    varys_loc = find_varys(cards)
    if varys_loc is None:
        return []

    row, col = varys_loc // 6, varys_loc % 6
    valid_moves = []

    for card in cards:
        if card.get_name() == 'Varys':
            continue
        card_row, card_col = card.get_location() // 6, card.get_location() % 6
        if card_row == row or card_col == col:
            valid_moves.append(card.get_location())

    return valid_moves


def house_variance(cards):
    """Calculate variance in house distribution"""
    house_counts = defaultdict(int)
    for card in cards:
        if card.get_name() != 'Varys':
            house_counts[card.get_house()] += 1

    if not house_counts:
        return {}

    counts = list(house_counts.values())
    mean = sum(counts) / len(counts)
    variances = {
        house: (count - mean) ** 2
        for house, count in house_counts.items()
    }
    return variances


def getScore(cards, player1, player2, player):
    """Calculate game score"""
    p1_banners = sum(player1.get_banners().values())
    p2_banners = sum(player2.get_banners().values())

    if player == 1:
        return p1_banners - p2_banners
    return p2_banners - p1_banners


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


def get_move(cards, player1, player2, companion_cards, choose_companion):
    '''
    This function gets the move of the player.

    Parameters:
        cards (list): list of Card objects
        player1 (Player): the player
        player2 (Player): the opponent
        companion_cards (dict): dictionary of companion cards
        choose_companion (bool): flag to choose a companion card

    Returns:
        move (int/list): the move of the player
    '''
    if not hasattr(get_move, 'rl_agent'):
        get_move.rl_agent = ReinforcementLearningAgent()

    if choose_companion:
        # Companion card selection logic remains the same
        if companion_cards:
            selected_companion = random.choice(list(companion_cards.keys()))
            move = [selected_companion]
            choices = companion_cards[selected_companion]['Choice']

            if choices == 1:  # Jon Snow-style cards
                move.append(random.choice(get_valid_jon_sandor_jaqan(cards)))
            elif choices == 2:  # Ramsay-style cards
                valid_moves = get_valid_ramsay(cards)
                move.extend(random.sample(valid_moves, 2) if len(
                    valid_moves) >= 2 else valid_moves)
            elif choices == 3:  # Jaqen-style cards
                valid_moves = get_valid_jon_sandor_jaqan(cards)
                if valid_moves:
                    move.extend(random.sample(valid_moves, 2) if len(
                        valid_moves) >= 2 else valid_moves)
                    if companion_cards:
                        move.append(random.choice(
                            list(companion_cards.keys())))
            return move
        else:
         return []

    # RL Agent move selection
    try:
        possible_moves = get_possible_moves(cards)
        if not possible_moves:
            return None

        state_key = get_move.rl_agent.get_state_key(cards, player1, player2)

        # Use Q-learning with minimax fallback
        chosen_move = select_move(
            possible_moves, state_key, cards, player1, player2)

        # Update learning state
        if chosen_move:
            get_move.rl_agent.state_history.append(state_key)
            get_move.rl_agent.move_history.append(chosen_move)

        return chosen_move

    except Exception as e:
        print(f"Error in move selection: {e}")
        return random.choice(possible_moves) if possible_moves else None


def select_move(possible_moves, state_key, cards, player1, player2):
    """Select best move using Q-learning and minimax"""
    # Exploration (10% chance)
    if random.random() < 0.1:
        return random.choice(possible_moves)

    # Exploitation using Q-values
    q_values = {move: get_move.rl_agent.get_q_value(state_key, str(move))
                for move in possible_moves}
    max_q = max(q_values.values(), default=-inf)
    best_moves = [move for move, q in q_values.items() if q == max_q]

    # Use minimax if no Q-value found
    if not best_moves:
        result = get_move.rl_agent.minimax(
            copy.deepcopy(player1),
            copy.deepcopy(player2),
            copy.deepcopy(cards),
            depth=3,
            alpha=-inf,
            beta=inf,
            player=1
        )
        return result[0] if result else None

    return random.choice(best_moves)


def record_learning(player1, player2, cards):
    """Record learning after a game"""
    final_state_key = get_move.rl_agent.get_state_key(cards, player1, player2)
    reward = get_move.rl_agent.calculate_reward(player1, player2, None, cards)

    # Update Q-values for all state-action pairs in the history
    for state_key, move in zip(get_move.rl_agent.state_history, get_move.rl_agent.move_history):
        get_move.rl_agent.update_q_value(state_key, move, reward)

    # Save the Q-table to a file
    get_move.rl_agent.save_q_table()

    # Clear history
    get_move.rl_agent.state_history.clear()
    get_move.rl_agent.move_history.clear()

    # Save the final state and reward to a text file
    with open("learning_record.txt", "w") as f:
        f.write(f"Final State: {final_state_key}\n")
        f.write(f"Reward: {reward}\n")
