class TriageEngine:

    def __init__(self, heuristics, embedder, llm, repository):
        self.heuristics = heuristics
        self.embedder = embedder
        self.llm = llm
        self.repo = repository

    def classify(self, email):

        cached = self.repo.find_by_subject(email.subject)
        if cached:
            return cached

        scores = self.heuristics.score(email)

        similar = self.repo.find_similar(email.subject)

        if similar:
            scores = similar.apply(scores)

        category, confidence = scores.best()

        if confidence > 0.9:
            return category

        return self.llm.classify(email)
