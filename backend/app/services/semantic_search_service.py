
from sqlalchemy.orm import Session

from app.ai.embedding_service import generate_embedding
from app.models.property_document import PropertyDocument


def search_similar_documents(
    db: Session,
    query: str,
    top_k: int = 5,
    property_ids: list[int] | None = None,
) -> list[PropertyDocument]:
    """
    Retrieve the most semantically relevant property documents.
    """

    if not query or not query.strip():
        raise ValueError("Query cannot be empty")

    if top_k < 1:
        raise ValueError("top_k must be greater than 0")

    # Convert guest query into an embedding
    query_embedding = generate_embedding(query)

    # Calculate cosine distance between query and stored vectors
    distance = PropertyDocument.embedding.cosine_distance(
        query_embedding
    )

    # Build database query
    db_query = db.query(PropertyDocument)

    # Optional: restrict search to selected properties
    if property_ids is not None:
        if not property_ids:
            return []

        db_query = db_query.filter(
            PropertyDocument.property_id.in_(property_ids)
        )

    # Return the closest matching documents
    documents = (
        db_query
        .order_by(distance)
        .limit(top_k)
        .all()
    )

    return documents
