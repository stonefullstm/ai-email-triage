from sentence_transformers import SentenceTransformer


class Embedder:

    def __init__(self):
        self.model = SentenceTransformer(
            "sentence-transformers/all-MiniLM-L6-v2",
            backend="onnx",
            model_kwargs={"file_name": "onnx/model_quint8_avx2.onnx"},
        )

    def embed(self, text):
        return self.model.encode(text)
