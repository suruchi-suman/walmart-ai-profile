from pymongo import MongoClient
import certifi

uri = "mongodb+srv://sumansuruchi2023:Odbk1k12RU2pDA3t@walmart-cluster.lk4jv0a.mongodb.net/?retryWrites=true&w=majority&tls=true"

client = MongoClient(uri, tlsCAFile=certifi.where())

try:
    print("Databases:", client.list_database_names())
except Exception as e:
    print("❌ Connection error:", e)

