from .categories import CATEGORIES


def init_scores():
    return {category: 0.0 for category in CATEGORIES}


def choose_best(scores):
    best = max(scores, key=scores.get)
    confidence = scores[best]
    return best, confidence
