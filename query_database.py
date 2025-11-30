import os
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL
from dotenv import load_dotenv

# Set up environment variables according to .env-template

# This file is useful to test that 
# your connection to the database is working

# Load environment variables
load_dotenv(override=True)

url = URL.create(
    drivername="postgresql+psycopg2",
    username=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
    host=os.getenv("DB_HOST"),
    port=os.getenv("DB_PORT"),
    database=os.getenv("DB_NAME"),
    query={"client_encoding": "utf8"},
)

engine = create_engine(url)

query = "SELECT * FROM event;"

with engine.connect() as connection:
    result = connection.execute(text(query))
    for row in result:
        print(row)