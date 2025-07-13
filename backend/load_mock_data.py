import json
from pymongo import MongoClient

client = MongoClient("mongodb://localhost:27017/")
db = client["walmart"]
collection = db["customers"]

# Load mock data from JSON file
with open("customers.json", "r") as f:
    data = json.load(f)

# Insert into MongoDB
result = collection.insert_many(data)
print(f"✅ Inserted {len(result.inserted_ids)} records!")
