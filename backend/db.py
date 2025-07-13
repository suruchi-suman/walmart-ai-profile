import os
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

APP_ENV = os.getenv("APP_ENV", "local")  # default to local if not set

if APP_ENV == "production":
    print("🔗 Using MongoDB Atlas")
    client = MongoClient(os.getenv("MONGO_URI"))
else:
    print("🌐 Using local MongoDB")
    client = MongoClient("mongodb://localhost:27017/")

db = client["walmart_ai"]
customer_collection = db["customers"]

