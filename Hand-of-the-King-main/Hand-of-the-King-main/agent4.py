import random
import json
import os
import copy
from collections import defaultdict
from main import get_possible_moves, calculate_winner, make_move
from utils.classes import Card, Player

# Configuration
Q_TABLE_FILE = "q_table.json"
LEARNING_RATE = 0.7
DISCOUNT_FACTOR = 0.95
EXPLORATION_RATE = 0.2

class RLAgent:
    def __init__(self):
        self.q_table = self.load_q_table()
        self.state_history = []

    def load_q_table(self):
        if os.path.exists(Q_TABLE_FILE):
            with open(Q_TABLE_FILE, 'r') as f:
                return defaultdict(lambda: defaultdict(float), json.load(f))
        return defaultdict(lambda: defaultdict(float))

    def save_q_table(self):
        with open(Q_TABLE_FILE, 'w') as f:
            json.dump(dict(self.q_table), f)

    def get_state_key(self, cards, player, opponent):
        state = [
            (card.get_house(), card.get_location())
            for card in cards
        ]
        state += [(house, player.get_banners()[house]) for house in player.get_banners()]
        return str(sorted(state))

    def choose_action(self, state_key, possible_moves):
        if random.random() < EXPLORATION_RATE:
            return random.choice(possible_moves)
        
        q_values = {move: self.q_table[state_key][str(move)] for move in possible_moves}
        return max(q_values, key=q_values.get, default=random.choice(possible_moves))

    def update_q_values(self, reward):
        for state, action in reversed(self.state_history):
            old_value = self.q_table[state][action]
            self.q_table[state][action] = old_value + LEARNING_RATE * (reward - old_value)
            reward *= DISCOUNT_FACTOR

def get_move(cards, player, opponent, companion_cards=None, choose_companion=False):
    if not hasattr(get_move, 'agent'):
        get_move.agent = RLAgent()

    # Companion card handling (game mechanic)
    if choose_companion and companion_cards:
        companion = random.choice(list(companion_cards.keys()))
        move = [companion]
        
        choice_type = companion_cards[companion]['Choice']
        valid_locations = [c.get_location() for c in cards if c.get_name() != 'Varys']
        
        if choice_type == 1:  # Single location
            move.append(random.choice(valid_locations))
        elif choice_type == 2:  # Two locations
            move.extend(random.sample(valid_locations, 2))
        elif choice_type == 3:  # Two locations + companion
            move.extend(random.sample(valid_locations, 2))
            move.append(random.choice(list(companion_cards.keys())))
            
        return move

    # RL-based move selection
    possible_moves = get_possible_moves(cards)
    if not possible_moves:
        return None

    state_key = get_move.agent.get_state_key(cards, player, opponent)
    chosen_move = get_move.agent.choose_action(state_key, possible_moves)
    get_move.agent.state_history.append((state_key, str(chosen_move)))
    
    return chosen_move

def train_rl_agent(episodes=1000):
    agent = RLAgent()
    
    for episode in range(episodes):
        # Initialize game state - implement your game initialization
        player = Player()
        opponent = Player()
        cards = []  # Implement your card initialization
        
        while cards:
            # Agent's turn
            state_key = agent.get_state_key(cards, player, opponent)
            possible_moves = get_possible_moves(cards)
            action = agent.choose_action(state_key, possible_moves)
            
            if action:
                make_move(cards, action, player)
                agent.state_history.append((state_key, str(action)))
            
            # Check game termination
            if not cards:
                break

        # Calculate final reward
        p1_score = sum(player.get_banners().values())
        p2_score = sum(opponent.get_banners().values())
        reward = 1 if p1_score > p2_score else -1 if p1_score < p2_score else 0
        
        # Update Q-values
        agent.update_q_values(reward)
        agent.save_q_table()
        agent.state_history = []

        print(f"Episode {episode+1}: Result {'Win' if reward > 0 else 'Loss' if reward < 0 else 'Draw'}")

# Example usage
if __name__ == "__main__":
    train_rl_agent(episodes=1000)