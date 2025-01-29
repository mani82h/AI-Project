from house_utils import house_member_count, houses

def find_varys(cards):
    varys = [card for card in cards if card.get_name() == 'Varys']
    varys_location = varys[0].get_location()
    return varys_location

def get_neighbors(location, row_size=6):
    neighbors = []
    row, col = divmod(location, row_size)

    for r in range(6):
        if r != row:
            neighbors.append(r * row_size + col)
    for c in range(row_size):
        if c != col:
            neighbors.append(row * row_size + c)

    return neighbors

def house_weight_change(player, opponent, house):
    alpha = 1.0
    
    if player + 1 > house_member_count[house] // 2:
        return 0.0
    
    elif player - opponent < 0:
        alpha = -1.0

    return alpha * (player - opponent) ** 2 / (house_member_count[house]) ** 2 

def cards_position(cards):
    cards_location = {}

    for card in cards:
        if card.get_name() == 'Varys':
            continue

        x = card.get_location() // 6
        y = card.get_location() % 6
        card_house = card.get_house()

        if card_house not in cards_location:
            cards_location[card_house] = [(x, y)]
        else:
            cards_location[card_house].append((x, y))

    return cards_location

def cards_variance_based_on_axis(cards_location, axis=0):
    variance_of_cards_location = {}

    for house, positions in cards_location.items():
        axis_values = [pos[axis] for pos in positions]
        avg = sum(axis_values) / len(axis_values)

        variance = sum((value - avg) ** 2 for value in axis_values) / len(axis_values)
        variance_of_cards_location[house] = variance

    return variance_of_cards_location

def house_variance(cards):
    cards_location = cards_position(cards)
    
    variance_x = cards_variance_based_on_axis(cards_location, 0)
    variance_y = cards_variance_based_on_axis(cards_location, 1)

    total_variance = {}

    for house in houses:
        if house in variance_x and house in variance_y:
            total_variance[house] = variance_x[house] + variance_y[house]
            
    return total_variance