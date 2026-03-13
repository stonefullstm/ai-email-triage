from sentence_transformers import SentenceTransformer


class Embedder:
    def __init__(
            self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        self.model = SentenceTransformer(
            model_name,
            backend="onnx",
            model_kwargs={"file_name": "onnx/model_quint8_avx2.onnx"},
        )

    def encode(self, text: str):
        return self.model.encode(text)
