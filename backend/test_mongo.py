 
# test_mongo.py
from db import customer_collection

for doc in customer_collection.find():
    print(doc)
