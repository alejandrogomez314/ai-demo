import chromadb
from chromadb.config import Settings

db_client = chromadb.Client(Settings(
    chroma_db_impl="duckdb+parquet",
    persist_directory="db"
))

db_client.persist()

db_global = db_client.get_collection('job_skills')

DEBUG = True
TESTING = True