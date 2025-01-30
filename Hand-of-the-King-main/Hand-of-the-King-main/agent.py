import random
import json
import os
import copy
from collections import defaultdict
from math import inf
from main import get_possible_moves, calculate_winner, make_move, print_cards_status, set_banners
from utils.classes import Card, Player

# Define the houses variable
houses = ["Stark", "Greyjoy", "Lannister", "Targaryen", "Baratheon", "Tyrell", "Tully"]

# Configuration parameters
LEARNING_RATE = 0.8
DISCOUNT_FACTOR = 0.9
Q_TABLE_FILE = "q_table.json"

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

def get_neighbors(location):
    row = location // 6
    col = location % 6
    neighbors = []
    if row > 0:
        neighbors.append(location - 6)
    if row < 5:
        neighbors.append(location + 6)
    if col > 0:
        neighbors.append(location - 1)
    if col < 5:
        neighbors.append(location + 1)
    return neighbors

def house_weight_change(player_count, opponent_count, house):
    total_needed = (house_member_count[house] // 2) + 1
    if player_count >= total_needed:
        return 0.5  # Already secured, lower weight
    elif opponent_count >= total_needed:
        return 0.0  # Opponent secured, no benefit
    else:
        return 1.0 / (total_needed - player_count + 1)

def getScore(cards, player, opponent, turn):
    varys_location = next((c.get_location() for c in cards if c.get_name() == 'Varys'), None)
    agent = get_move.rl_agent
    player_score = agent.heuristic(player, opponent, cards, varys_location)
    opponent_score = agent.heuristic(opponent, player, cards, varys_location)
    return player_score - opponent_score

class ReinforcementLearningAgent:
    def __init__(self):
        self.q_table = self.load_q_table()
        self.state_history = []
        self.move_history = []

    def load_q_table(self):
        if os.path.exists(Q_TABLE_FILE):
            with open(Q_TABLE_FILE, 'r') as f:
                data = json.load(f)
                return defaultdict(lambda: defaultdict(float), 
                                  {k: defaultdict(float, v) for k, v in data.items()})
        return defaultdict(lambda: defaultdict(float))

    def save_q_table(self):
        save_data = {k: dict(v) for k, v in self.q_table.items()}
        with open(Q_TABLE_FILE, 'w') as f:
            json.dump(save_data, f)

    def get_state_key(self, cards, player1, player2):
        state = []
        for card in cards:
            if card.get_name() != 'Varys':
                state.append((card.get_house(), card.get_location()))
        state.extend([(house, player1.get_banners()[house]) for house in houses])
        state.extend([(house, player2.get_banners()[house]) for house in houses])
        return str(sorted(state))

    def get_q_value(self, state_key, move):
        return self.q_table[state_key][str(move)]

    def update_q_value(self, state_key, move, reward):
        move_key = str(move)
        current_q = self.q_table[state_key][move_key]
        self.q_table[state_key][move_key] = current_q + LEARNING_RATE * (reward - current_q)

    def calculate_reward(self, player1, player2, last_move, cards):
        reward = 0
        
        if last_move:
            target_card = next((c for c in cards if c.get_location() == last_move), None)
            if target_card and target_card.get_owner() != player1:
                reward += weights["capture_banner_bonus"]

        varys_loc = next((c.get_location() for c in cards if c.get_name() == 'Varys'), None)
        if varys_loc:
            row = varys_loc // 6
            col = varys_loc % 6
            reward += len([c for c in cards if c.get_location() // 6 == row]) * weights["row_col_priority"]
            reward += len([c for c in cards if c.get_location() % 6 == col]) * weights["row_col_priority"]

        banner_diff = sum(player1.get_banners().values()) - sum(player2.get_banners().values())
        reward += banner_diff * weights["general_banner_weight"]

        banner_counts = list(player1.get_banners().values())
        if banner_counts:
            mean = sum(banner_counts) / len(banner_counts)
            variance = sum((x - mean) ** 2 for x in banner_counts) / len(banner_counts)
            reward += variance * weights["house_variance_weight"]

        return reward

    def heuristic(self, player, opponent, cards, varys_location):
        banners = player.get_banners()
        opponent_banners = opponent.get_banners()
        score = 0

        for card in cards:
            if card.get_name() == 'Varys':
                continue

            house = card.get_house()
            location = card.get_location()
            current_banners = banners.get(house, 0)
            opponent_current = opponent_banners.get(house, 0)
            total_needed = (house_member_count[house] // 2) + 1

            if current_banners + 1 >= total_needed and current_banners < total_needed:
                score += weights["capture_banner_bonus"]

            if varys_location is not None:
                card_row = location // 6
                card_col = location % 6
                varys_row = varys_location // 6
                varys_col = varys_location % 6

                if card_row == varys_row or card_col == varys_col:
                    score += weights["row_col_priority"]

            weight = house_weight_change(current_banners, opponent_current, house)
            score += current_banners * weight

        banner_counts = list(banners.values())
        if len(banner_counts) >= 2:
            mean = sum(banner_counts) / len(banner_counts)
            variance = sum((x - mean) ** 2 for x in banner_counts) / len(banner_counts)
            score -= variance * weights["house_variance_weight"]

        return score

    def minimax(self, player1, player2, cards, depth, alpha, beta, player):
        if depth == 0 or not cards:
            return [None, getScore(cards, player1, player2, player)]

        best_move = None
        possible_moves = get_possible_moves(cards)

        if player == 1:
            max_score = -inf
            for move in possible_moves:
                new_cards = copy.deepcopy(cards)
                new_p1 = copy.deepcopy(player1)
                new_p2 = copy.deepcopy(player2)
                make_move(new_cards, move, new_p1)
                _, current_score = self.minimax(new_p1, new_p2, new_cards, depth-1, alpha, beta, -player)
                if current_score > max_score:
                    max_score = current_score
                    best_move = move
                    alpha = max(alpha, max_score)
                if alpha >= beta:
                    break
            return [best_move, max_score]
        else:
            min_score = inf
            for move in possible_moves:
                new_cards = copy.deepcopy(cards)
                new_p1 = copy.deepcopy(player1)
                new_p2 = copy.deepcopy(player2)
                make_move(new_cards, move, new_p2)
                _, current_score = self.minimax(new_p1, new_p2, new_cards, depth-1, alpha, beta, -player)
                if current_score < min_score:
                    min_score = current_score
                    best_move = move
                    beta = min(beta, min_score)
                if alpha >= beta:
                    break
            return [best_move, min_score]
def get_valid_ramsay(cards):
    return [card.get_location() for card in cards]

def get_valid_jon_sandor_jaqan(cards):
    return [card.get_location() for card in cards if card.get_name() != 'Varys']

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

def train_agent(episodes, player1, player2, cards):
    for episode in range(episodes):
        current_cards = copy.deepcopy(cards)
        current_player1 = copy.deepcopy(player1)
        current_player2 = copy.deepcopy(player2)
        
        while current_cards:
            move = get_move(current_cards, current_player1, current_player2)
            if move is None:
                break
            make_move(current_cards, move, current_player1)
            reward = get_move.rl_agent.calculate_reward(current_player1, current_player2, move, current_cards)
            state_key = get_move.rl_agent.get_state_key(current_cards, current_player1, current_player2)
            get_move.rl_agent.update_q_value(state_key, move, reward)
        
        winner = calculate_winner(current_player1, current_player2)
        final_reward = 100 if winner == 1 else -100
        for i in range(len(get_move.rl_agent.state_history)):
            state = get_move.rl_agent.state_history[i]
            move = get_move.rl_agent.move_history[i]
            get_move.rl_agent.update_q_value(state, str(move), final_reward)
        
        get_move.rl_agent.save_q_table()
        get_move.rl_agent.state_history = []
        get_move.rl_agent.move_history = []