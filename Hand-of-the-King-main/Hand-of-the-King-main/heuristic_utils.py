from house_utils import house_member_count, houses

def banner_difference_score(player1, player2):
    banners = player1.get_banners()
    opponent_banners = player2.get_banners()
    results = 0
    for house in houses:
        results += (banners[house] - opponent_banners[house])
    return results

def who_has_more(player1, player2):
    banners = player1.get_banners()
    opponent_banners = player2.get_banners()
    results = 0
    for house in houses:
        if banners[house] > house_member_count[house] // 2:
            results += -2
        elif banners[house] > opponent_banners[house]:
            results += 1
    return results