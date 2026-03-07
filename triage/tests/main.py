from sentence_transformers import SentenceTransformer


sentences = ["This is an example sentence", "Each sentence is converted"]

model = SentenceTransformer(
  'sentence-transformers/all-MiniLM-L6-v2',
  backend="onnx",
  model_kwargs={"file_name": "onnx/model_quint8_avx2.onnx"}
  )
embeddings = model.encode(sentences)
print(embeddings)
