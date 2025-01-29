import random
import multiprocessing
from random import randrange
from main_sim import main_sim
from config import Config
import json
import os

POPULATION = 1000
ONE_POINT_THRESHOLD = 0.3
TWO_POINT_THRESHOLD = 0.4
ONE_POINT_INDEX = 0.4
TWO_POINT_INDEX_BEGIN = 0.3
TWO_POINT_INDEX_END = 0.7
MUTATION_RATE = 0.4
MUTATION_ALPHA = 40  # Indicates the range of random int generated
GENERATIONS = 50  # Number of generations to run the algorithm
TOURNAMENT_SIZE = 5  # Size of the tournament for selection
NUM_PROCESSES = 1  # Number of processes to run in parallel

class GeneticAlgorithm:
    def __init__(self):
        self.config_array = [Config() for _ in range(POPULATION)]

    def random_populate(self):
        for config in self.config_array:
            config.random_init()

    def random_populate_with_default_configs(self, default_number=10):
        self.random_populate()
        random_indices = random.sample(range(POPULATION), default_number)
        for rand_n in random_indices:
            self.config_array[rand_n] = Config()

    def fitness(self, config):
        # config_file = f'temp_config_{os.getpid()}.json'
        config_file = 'temp_config.json'
        with open(config_file, 'w') as file:
            json.dump(config.__dict__, file)

        results = run_game_with_config(config_file)
        if results is None:
            return -1e4  # Return a low score if the game could not be run
        winner = results['winner']
        current_player_score = results['banners']['player1']
        opponent_player_score = results['banners']['player2']
        
        os.remove(config_file)

        return self.fitness_score(winner, current_player_score, opponent_player_score)

    def fitness_score(self, winner, current_player_score, opponent_player_score):
        if winner == 1:
            return 10e4 + current_player_score - opponent_player_score
        elif winner == 2:
            return -10e4 + opponent_player_score - current_player_score
        else:
            return current_player_score - opponent_player_score

    def crossover(self, parent1, parent2):
        child1, child2 = None, None
        if random.random() <= ONE_POINT_THRESHOLD:
            joint_index = int(ONE_POINT_INDEX * len(parent1))
            child1 = parent1[:joint_index] + parent2[joint_index:]
            child2 = parent2[:joint_index] + parent1[joint_index:]

        elif random.random() > ONE_POINT_THRESHOLD and random.random() <= TWO_POINT_THRESHOLD:
            joint_index_begin = int(TWO_POINT_INDEX_BEGIN * len(parent1))
            joint_index_end = int(TWO_POINT_INDEX_END * len(parent1))
            child1 = parent1[:joint_index_begin] + parent2[joint_index_begin:joint_index_end] + parent1[joint_index_end:]
            child2 = parent1[:joint_index_begin] + parent2[joint_index_begin:joint_index_end] + parent1[joint_index_end:]
        
        if child1 and child2:
            return Config(weights=child1), Config(weights=child2)
        return None, None

    def mutation(self, gene):
        if random.random() < MUTATION_RATE:
            index = randrange(0, len(gene))
            mutate_amount = randrange(-MUTATION_ALPHA, MUTATION_ALPHA)
            gene[index] += mutate_amount
        return gene

    def select_parents(self):
        selected = random.sample(self.config_array, TOURNAMENT_SIZE)
        selected.sort(key=lambda x: x.fitness_score, reverse=True)
        return selected[0], selected[1]

    def generate_children(self, _):
        parent1, parent2 = self.select_parents()
        child1, child2 = self.crossover(parent1.weights, parent2.weights)
        if child1 and child2:
            child1.weights = self.mutation(child1.weights)
            child2.weights = self.mutation(child2.weights)
            return [child1, child2]
        return []

    def run(self):
        for generation in range(GENERATIONS):
            new_population = []
            with multiprocessing.Pool(processes=NUM_PROCESSES) as pool:
                results = pool.map(self.generate_children, range(POPULATION // 2))
                for result in results:
                    new_population.extend(result)

            self.config_array = new_population
            self.evaluate_fitness()
            best_fitness = max(config.fitness_score for config in self.config_array)
            print(f"Generation {generation}: Best Fitness = {best_fitness}")

    def evaluate_fitness(self):
        with multiprocessing.Pool(processes=NUM_PROCESSES) as pool:
            self.config_array = pool.map(self.calculate_fitness, self.config_array)

    def calculate_fitness(self, config):
        config.fitness_score = self.fitness(config)
        return config

def run_game_with_config(config_file):
    results = main_sim(
        player1='simulate',
        player2='random_agent'
    )
    return results

if __name__ == "__main__":
    import time
    start_time = time.time()  # Start timing
    ga = GeneticAlgorithm()
    ga.random_populate_with_default_configs()
    ga.run()
    end_time = time.time()  # End timing
    print(f"Execution Time: {end_time - start_time:.2f} seconds")