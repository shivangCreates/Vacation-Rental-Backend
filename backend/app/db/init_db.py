from app.db.database import Base, engine
from app.models.property_document import PropertyDocument
from app.models.property import Property, PropertyAmenity, PropertyUnavailablePeriod


def create_tables():
   Base.metadata.create_all(bind=engine)
   print("Database tables created successfully!")
   
   
if __name__ == "__main__":
    create_tables()   