class LLMClassifier:

    def __init__(self, client):
        self.client = client

    def classify(self, email):

        prompt = build_prompt(email)

        result = self.client.chat(prompt)

        return parse_result(result)
