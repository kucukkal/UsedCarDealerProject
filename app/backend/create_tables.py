# create_tables.py
from app.database import Base, engine
import app.models  # <-- IMPORTANT: this registers the models with Base

def main():
    print("Using DB URL:", engine.url)
    Base.metadata.create_all(bind=engine)
    print("Tables created (or already existed).")

if __name__ == "__main__":
    main()
