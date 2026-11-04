
from langchain_ollama import OllamaEmbeddings

# Embedding model configuration
EMBEDDING_MODEL = "nomic-embed-text"
EMBEDDING_DIMENSIONS = 768

# Initialize embedding model
embedding_model = OllamaEmbeddings(
    model=EMBEDDING_MODEL
)


def generate_embedding(text: str) -> list[float]:
    """
    Convert a text string into a numerical vector.
    """

    if not text or not text.strip():
        raise ValueError("Text cannot be empty")

    embedding = embedding_model.embed_query(text)

    if len(embedding) != EMBEDDING_DIMENSIONS:
        raise ValueError(
            f"Expected {EMBEDDING_DIMENSIONS} dimensions, "
            f"got {len(embedding)}"
        )

    return embedding


def generate_embeddings(texts: list[str]) -> list[list[float]]:
    """
    Generate embeddings for multiple text documents.
    """

    if not texts or any(not text.strip() for text in texts):
        raise ValueError("Texts cannot be empty")

    embeddings = embedding_model.embed_documents(texts)

    for embedding in embeddings:
        if len(embedding) != EMBEDDING_DIMENSIONS:
            raise ValueError("Unexpected embedding dimensions")

    return embeddings
