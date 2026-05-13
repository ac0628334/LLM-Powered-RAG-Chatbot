import sys
from pathlib import Path

# Add project root to sys.path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from src.database import engine
from src.models import Base

print("Creating tables in MySQL...")
Base.metadata.create_all(bind=engine)
print("Tables created successfully!")
