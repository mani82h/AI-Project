from math import inf
import random
import copy
from main import make_move, get_possible_moves, print_cards_status, set_banners

# Constants and configurations
houses = ["Stark", "Greyjoy", "Lannister",
          "Targaryen", "Baratheon", "Tyrell", "Tully"]
house_member_count = {
    "Stark": 8, "Greyjoy": 7, "Lannister": 6, "Targaryen": 5,
    "Baratheon": 4, "Tyrell": 3, "Tully": 2,
}
weight_ranges = {
    "capture_banner_bonus": (10.0, 30.0),
    "row_col_priority": (1.0, 5.0),
    "general_banner_weight": (0.1, 2.0),
    "house_variance_weight": (0.1, 1.0),
}

# Initial weights
weights = {
    "capture_banner_bonus": 20.0,
    "row_col_priority": 3.0,
    "general_banner_weight": 1.0,
    "house_variance_weight": 0.5
}

def evolve_weights(population_size=10, generations=20, mutation_rate=0.1):
    population = [
        {key: random.uniform(*weight_ranges[key]) for key in weights}
        for _ in range(population_size)
    ]

    for generation in range(generations):
        fitness_scores = [simulate_games(weights) for weights in population]
        top_indices = sorted(range(len(fitness_scores)),
                             key=lambda i: -fitness_scores[i])
        top_individuals = [population[i] for i in top_indices[:population_size // 2]]

        new_population = []
        for _ in range(population_size):
            parent1, parent2 = random.sample(top_individuals, 2)
            child = {key: random.choice([parent1[key], parent2[key]]) for key in weights}

            if random.random() < mutation_rate:
                key_to_mutate = random.choice(list(weights.keys()))
                child[key_to_mutate] = random.uniform(*weight_ranges[key_to_mutate])

            new_population.append(child)

        population = new_population

    fitness_scores = [simulate_games(weights) for weights in population]
    best_index = max(range(len(fitness_scores)), key=lambda i: fitness_scores[i])
    return population[best_index]

def simulate_games(weights, num_games=5):
    score = 0
    for _ in range(num_games):
        score += run_game_simulation(weights)
    return score

def run_game_simulation(weights):
    return random.randint(0, 100)

def update_weights_rl(current_weights, gradients, learning_rate=0.01):
    for key in current_weights:
        current_weights[key] += learning_rate * gradients[key]
    return current_weights

def find_varys(cards):
    for i, card in enumerate(cards):
        if card.get_name() == 'Varys':
            return i
    return None

def compute_gradients(player1, player2, cards):
    gradients = {key: 0.0 for key in weights}
    varys_location = find_varys(cards)
    for card in cards:
        if card.get_name() == 'Varys':
            continue
        house = card.get_house()
        gradients["capture_banner_bonus"] += (player1.get_banners()[house] - player2.get_banners()[house])
    return gradients

def getScore(cards, player1, player2, player):
    p1_banners = sum(player1.get_banners().values())
    p2_banners = sum(player2.get_banners().values())
    return (p1_banners - p2_banners) if player == 1 else (p2_banners - p1_banners)

def minimax(player1, player2, cards, depth, alpha, beta, player):
    move = None

    if depth == 0 or not cards:
        return [move, getScore(cards, player1, player2, player)]

    for moves in get_possible_moves(cards):
        current_cards = copy.deepcopy(cards)
        current_player1 = copy.deepcopy(player1)
        current_player2 = copy.deepcopy(player2)

        if player == 1:
            make_move(current_cards, moves, current_player1)
        else:
            make_move(current_cards, moves, current_player2)

        score = minimax(current_player1, current_player2, current_cards, depth - 1, alpha, beta, -player)
        
        if player == 1:
            if score[1] > alpha:
                alpha = score[1]
                move = moves
        else:
            if score[1] < beta:
                beta = score[1]
                move = moves

        if alpha >= beta:
            break

    return [move, alpha] if player == 1 else [move, beta]

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
    global weights
    limit = 5

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

    result = minimax(player1, player2, cards, limit, -inf, inf, 1)
    return result[0]

def game_over(cards):
    return len(cards) == 0

def is_player1_turn(turn_counter):
    return turn_counter % 2 == 0

def play_game(player1, player2, cards):
    global weights
    weights = evolve_weights()
    turn_counter = 0

    while not game_over(cards):
        current_turn = 1 if is_player1_turn(turn_counter) else 2
        move = get_move(cards, player1, player2)
        make_move(cards, move, player1 if current_turn == 1 else player2)
        gradients = compute_gradients(player1, player2, cards)
        weights = update_weights_rl(weights, gradients)
        turn_counter += 1