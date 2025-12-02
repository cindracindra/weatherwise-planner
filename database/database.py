import os
from sqlalchemy import create_engine
from sqlalchemy.engine import URL
from dotenv import load_dotenv

# Load environment variables (only for local testing)
load_dotenv(override=True)

# Create database engine
url = URL.create(
    drivername="postgresql+psycopg2",
    username=os.getenv("PGUSER"),
    password=os.getenv("PGPASSWORD"),
    host=os.getenv("PGHOST"),
    port=int(os.getenv("PGPORT", "5432")),
    database=os.getenv("PGDATABASE"),
    query={"client_encoding": "utf8"},
)

engine = create_engine(url)
