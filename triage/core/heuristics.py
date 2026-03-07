from .scoring import init_scores


class HeuristicClassifier:

    def __init__(self, rules):
        self.rules = rules

    def score(self, email):

        scores = init_scores()

        subject = email.subject.lower()

        for keyword, category, weight in self.rules:

            if keyword in subject:
                scores[category] += weight

        return scores
