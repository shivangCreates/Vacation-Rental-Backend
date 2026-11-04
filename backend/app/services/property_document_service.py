
from sqlalchemy.orm import Session

from app.models.property import Property
from app.models.property_document import PropertyDocument
from app.ai.embedding_service import generate_embedding


def build_property_content(property: Property) -> str:
    """
    Convert a property record into searchable text.
    """

    amenities = ", ".join(property.amenities or [])

    content = f"""
    Property Name: {property.name}
    Destination: {property.destination}
    Property Type: {property.property_type}
    Swimming Pool: {"Yes" if property.has_pool else "No"}
    Amenities: {amenities or "Not specified"}
    Description: {property.description or "Not specified"}
    """

    return content.strip()


def ingest_property(db: Session, property: Property):
    """
    Generate an embedding and store the property document.
    """

    content = build_property_content(property)

    # Generate vector before changing existing records
    embedding = generate_embedding(content)

    # Remove the previous document for this property
    db.query(PropertyDocument).filter(
        PropertyDocument.property_id == property.id
    ).delete(synchronize_session=False)

    # Create the new document
    document = PropertyDocument(
        property_id=property.id,
        content=content,
        embedding=embedding,
        chunk_index=0,
    )

    db.add(document)
    return document


def ingest_all_properties(db: Session) -> int:
    """
    Generate and store embeddings for all properties.
    """

    try:
        properties = db.query(Property).all()

        for property in properties:
            ingest_property(db, property)

        db.commit()

        return len(properties)

    except Exception:
        db.rollback()
        raise

