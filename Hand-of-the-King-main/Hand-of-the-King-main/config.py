import random

WEIGHTS_SIZE = 7
PRECISION = 2

class Config():
    def __init__(self, weights=None):
        self.weight_names = [
            "capture_banner_bonus",
            "row_col_priority",
            "general_banner_weight",
            "house_variance_weight",
            "who_has_more",
            "banner_difference_score",
            "heuristic"
        ]
        
        if weights is None:
            self.weights = [
                40.0,  # "capture_banner_bonus"
                3.0,   # "row_col_priority"
                2.0,   # "general_banner_weight"
                1.5,   # "house_variance_weight"
                50.0,  # "who_has_more"
                15.0,  # "banner_difference_score"
                1.0    # "heuristic"
            ]
        else:
            self.weights = weights
        
        self.fitness_score = 0  # Initialize fitness_score
    
    def random_init(self):
        self.weights = [round(random.random(), PRECISION) for _ in range(WEIGHTS_SIZE)]
    
    def default_init(self, weights):
        self.weights = weights
    
    def get_weights_dict(self):
        return {name: self.weights[idx] for idx, name in enumerate(self.weight_names)}