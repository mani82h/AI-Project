import os
import json
import random
import multiprocessing
from time import sleep
from config import Config
from random import randrange
from datetime import datetime
from main_sim_no_gui import main_sim

POPULATION = 25
ELITE_PORTION = 0.3
BEST_SETUP_COLD_START_PORTION = 0.2
ONE_POINT_THRESHOLD = 0.2
TWO_POINT_THRESHOLD = 0.4
ONE_POINT_INDEX = 0.4
TWO_POINT_INDEX_BEGIN = 0.2
TWO_POINT_INDEX_END = 0.5
MUTATION_RATE = 0.3
MUTATION_ALPHA = 20  # Indicates the range of random int generated
GENERATIONS = 1  # Number of generations to run the algorithm
TOURNAMENT_PORTION = 0.4  # portion of the tournament for selection
NUM_PROCESSES = 1 # whoever thought GIL was a good idea, i want to talk to them

# oh god we messed up somewhere, we're adding like a whole double precision thingy probably and that's really bad
# honestly the performance sucks
# or there could be sth wrong with the code, dunno
# it's unreasonable to have that many bad runs

# mate in the simulate itself make sure after each run we're using different config, cause if that's not it, we're in big troubles, we can assign a number to it and after it changed in the json file, we're good to changing or sth, right????

class GeneticAlgorithm:
    def __init__(self):
        self.config_array = [Config() for _ in range(POPULATION)]
        self.current_run_set = False

    def random_populate(self):
        for config in self.config_array:
            config.random_init()
        
        # print(f'config_array length after random_populate: {len(self.config_array)}')
        # sleep(3)

    def random_populate_with_default_configs(self, default_number=BEST_SETUP_COLD_START_PORTION):
        self.random_populate()
        random_indices = random.sample(range(1, POPULATION), int(default_number * POPULATION)) # here using population itself wont' cause issues, but later since config_array will change, len of config_array should be used
        # make sure at least 1 or 2 guys get selected in the random_indices

        # print(f'random_indices: {random_indices}')
        # sleep(0.5)

        for rand_n in random_indices:
            self.config_array[rand_n] = Config() # you know why this thing can go wrong, it's cause it can still lose in this point, so maybe cold start with some fixed scores right
        
        # print(f'config_array length after random_populate_with_default_configs: {len(self.config_array)}')
        # sleep(3)

    def fitness(self, config):
        config_file = 'temp_config.json'
        with open(config_file, 'w') as file:
            json.dump(config.__dict__, file)

        results = run_game_with_config()
        if results is None:
            return -1e4 # in case the game couldn't run properly

        winner = results['winner']
        current_player_score = results['player1_banners'] # make sure this actually works alright, idk rn but make sure aight :))))
        opponent_player_score = results['player2_banners']
        
        os.remove(config_file) # remove config_file after each simulation

        return self.fitness_score(winner, current_player_score, opponent_player_score)

    def fitness_score(self, winner, current_player_score, opponent_player_score):
        # the problem with this shit is that you can't just subtract two dictionaries

        # basically -> current_player = player1 and opponent = player2

        current_player_score = sum(current_player_score.values())
        opponent_player_score = sum(opponent_player_score.values())

        # print(f'score difference: {current_player_score - opponent_player_score}')
        # sleep(1)
        # this shit ain't even working, not sure why tho man
        # think we should cold start the self.fitness_score of some of the configs, saying that cause it might lose even tho it's our best setup

        # print(f'winner: {winner}')
        # sleep(0.5)

        if winner == 1:
            return 1e4 + current_player_score - opponent_player_score
        elif winner == 2:
            return -1e4 + current_player_score - opponent_player_score
        
        # else: bruh this shouldn't even be happening, i don't think there's any sort of tie in this game sooooooo
        #     return current_player_score - opponent_player_score

    def crossover(self, parent1, parent2):
        child1, child2 = None, None
        if random.random() <= ONE_POINT_THRESHOLD:
            joint_index = int(ONE_POINT_INDEX * randrange(0, len(parent1)))
            child1 = parent1[:joint_index] + parent2[joint_index:]
            child2 = parent2[:joint_index] + parent1[joint_index:]

        else:
            # joint_index_begin = int(TWO_POINT_INDEX_BEGIN * randrange(1, len(parent1)))
            # joint_index_end = int(TWO_POINT_INDEX_END * randrange(joint_index_begin, len(parent1)))

            # not sure which one of these are better implemenations
            # we should test that's all I know

            joint_index_begin = int(TWO_POINT_INDEX_BEGIN * len(parent1))
            joint_index_end = int(TWO_POINT_INDEX_END * len(parent1))
            child1 = parent1[:joint_index_begin] + parent2[joint_index_begin:joint_index_end] + parent1[joint_index_end:]
            child2 = parent1[:joint_index_begin] + parent2[joint_index_begin:joint_index_end] + parent1[joint_index_end:]
        
        return Config(weights=child1), Config(weights=child2)

    def mutate(self, gene):
        if random.random() < MUTATION_RATE:
            index = randrange(0, len(gene))
            mutate_amount = randrange(1, MUTATION_ALPHA) # like this part can be dynamically decreased after some iterations has been gone, or maybe even increased if fitness score was too low
        else:
            index = randrange(0, len(gene))
            mutate_amount = randrange(-MUTATION_ALPHA, -1)
        
        gene[index] += mutate_amount
        return Config(weights=gene)
    
    def run(self):
        best_config = None
        best_fitness = 0

        # multi processing can be added to this but first gotta make sure the vanilla implementation works quite alright
        for generation in range(GENERATIONS):
            population_fitness = []

            for config in self.config_array:
                config_fitness = self.fitness(config)
                config.set_fitness_score(config_fitness)
                population_fitness.append((config, config_fitness)) # config ain't just a weight, so take care of it yourself, make sure not that many unfinished games are added to this thingy, ah also one thing else mate, since we're just using a global boolean for the setting config in simulate.py there could be the point that it doesn't just get set off again, yk i'm saying maybe only it's getting set on;y once and not much happening after that
            
            population_fitness.sort(key=lambda x: x[1], reverse=True) # sort based on fitness

            if population_fitness[0][1] > best_fitness:
                best_fitness = population_fitness[0][1]
                best_config = population_fitness[0][0] # not sure if i should use paranthesis with __dict__

            elite_population = []

            # rn this implementation is elite based, we should try tournament one as well
            for x in population_fitness[: int(len(self.config_array) * ELITE_PORTION)]: # good idea to check if this joint position is greater than zero
                elite_population.append(x[0])

            # print(f'joint index: {int(len(self.config_array) * ELITE_PORTION)}')
            # print(f'config_array length: {len(self.config_array)}') # why the fuck this is 3 when it should be 10 instead
            # print(f'population_fitness length: {len(population_fitness)}')
            # print(f'population_fitness: {population_fitness}')
            # print(f'elite_population: {elite_population}')
            # sleep(5)
            
            new_population = elite_population[:]
            
            while len(new_population) < POPULATION: # this let us to add new thing to our stuff, also having the elite population all together
                parent1, parent2 = random.sample(elite_population, 2)
                offspring = self.crossover(parent1.weights, parent2.weights)
                new_population.append(offspring[0]) # not sure if this work alright since crossover will return to things
                new_population.append(offspring[1])
                # make sure that thing is actually working alright

            new_population = [self.mutate(config.weights) for config in new_population]
            
            self.config_array = new_population
            self.save_best_configs(best_config)
        
        # figure out saving best_config as it should to json, it's fucked rn
        print(f'best_confg: {best_config}')
        # sleep(1)

        return best_config
    
    def save_best_configs(self, best_config):
        with open("best_configs.json", "a") as file:
            if self.current_run_set == False:
                self.current_run_set = True
                now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                file.write(now + "\n")
        
            json.dump(best_config.__dict__, file)
            file.write("\n")

# In Python, the expression -1e4 represents the scientific notation for the number -1 * 10^4, which is -10000.0

def run_game_with_config(): # oh god not sure why the config_file was passed here, guess we don't really need it
    results = main_sim(
        player1='simulate',
        player2='random_agent'
    )

    # this point is actually a critical one as it might not return anything good from the main_sim so take care
    # print(f'results: {results}')
    # sleep(0.5)

    return results

# dude ima fucking crash out like tf is this: "weights": [0.84, 0.28, 0.07, 0.24, -3.0300000000000002, 0.18, 0.79], "fitness_score": 10003.0}
# just look at that precision, how tf did that happen

if __name__ == "__main__":
    import time
    start_time = time.time()  # Start timing
    ga = GeneticAlgorithm()
    ga.random_populate_with_default_configs()
    # print(f'config_array length before running: {len(ga.config_array)}')
    # sleep(3)
    ga.run()
    end_time = time.time()  # End timing
    print(f"Execution Time: {end_time - start_time:.2f} seconds")