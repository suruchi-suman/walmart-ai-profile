from fastapi import FastAPI, Request
from pymongo import MongoClient
from db import customer_collection
from bson import ObjectId
from fastapi.middleware.cors import CORSMiddleware
from ai.sentiment import analyze_sentiment
from collections import Counter
from datetime import datetime
from uuid import uuid4   # to generate unique customer_id


product_catalog = {
    "Apparel": [
        {"name": "T-Shirt", "price": 299},
        {"name": "Jeans", "price": 899},
        {"name": "Jacket", "price": 1499}
    ],
    "Electronics": [
        {"name": "Wireless Mouse", "price": 599},
        {"name": "USB-C Charger", "price": 899},
        {"name": "Power Bank", "price": 999}
    ],
    "Books": [
        {"name": "Atomic Habits", "price": 450},
        {"name": "The Alchemist", "price": 350}
    ],
    "Accessories": [
        {"name": "Backpack", "price": 799},
        {"name": "Wallet", "price": 499}
    ],
    "Footwear": [
        {"name": "Running Shoes", "price": 1200},
        {"name": "Flip-Flops", "price": 250}
    ]
}


default_products = [
    {"name": "Toothpaste", "category": "Personal Care", "price": 59},
    {"name": "Shampoo", "category": "Personal Care", "price": 139},
    {"name": "Rice Bag (5kg)", "category": "Grocery", "price": 299},
    {"name": "Cooking Oil", "category": "Grocery", "price": 149},
    {"name": "Notebook", "category": "Stationery", "price": 40},
    {"name": "Pen (Pack of 5)", "category": "Stationery", "price": 50},
    {"name": "Instant Noodles", "category": "Food", "price": 30}
]


app = FastAPI()

# CORS for local frontend dev
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def home():
    return {"message": "Hello from FastAPI!"}

# ------------------ Signup ------------------
@app.post("/signup")
def signup(data: dict):
    name = data.get("name")
    email = data.get("email")

    if not name or not email:
        return {"error": "Name and email are required"}

    # Check if user already exists
    existing = customer_collection.find_one({"email": email})
    if existing:
        return {"error": "User already exists"}

    new_customer = {
        "customer_id": str(uuid4())[:12],
        "name": name,
        "email": email,
        "satisfaction_score": 5,
        "order_history": [],
        "churned": False,
        "app_usage": {
            "last_login": None,
            "total_visits": 0
        },
        "purchases": []
    }

    customer_collection.insert_one(new_customer)
    new_customer.pop("_id")  # remove ObjectId before returning
    return new_customer


# ------------------ Login ------------------
@app.post("/login")
def login(data: dict):
    email = data.get("email")
    if not email:
        return {"error": "Email is required"}

    customer = customer_collection.find_one({"email": email}, {"_id": 0})
    if not customer:
        return {"error": "User not found"}

    customer_collection.update_one({"email": email}, {"$set": {"app_usage.last_login": "2025-07-05"}})
    return customer

def serialize_customer(customer):
    return {
        "customer_id": customer.get("customer_id"),
        "name": customer.get("name"),
        "email": customer.get("email","N/A"),
        "satisfaction_score": customer.get("satisfaction_score", 5),
        "order_history": customer.get("order_history", []),
        "feedback_history": customer.get("feedback_history", [])
    }


# ------------------ Get All Customers ------------------
@app.get("/customers")
def get_customers():
    try:
        customers = list(customer_collection.find())
        return [serialize_customer(c) for c in customers]
    except Exception as e:
        return {"error": "Internal Server Error"}

# ------------------ Get by ID ------------------
@app.get("/customers/{customer_id}")
def get_customer(customer_id: str):
    user = customer_collection.find_one({"customer_id": customer_id})
    return serialize_customer(user) if user else {"error": "User not found"}

# ------------------ Flags & Sentiment ------------------
@app.get("/flagged-customers")
def flagged_customers():
    flagged = customer_collection.find({
        "$or": [
            {"satisfaction_score": {"$lt": 3}},
            {"app_usage.last_login": {"$lt": "2025-06-15"}}
        ]
    }, {"_id": 0})
    return list(flagged)

@app.post("/analyze-sentiment")
def get_sentiment(data: dict):
    text = data.get("text")
    customer_id = data.get("customer_id")

    if not text or not customer_id:
        return {"error": "Missing text or customer_id"}

    sentiment = analyze_sentiment(text)

    # Save feedback to MongoDB
    customer_collection.update_one(
        {"customer_id": customer_id},
        {"$push": {
            "feedback_history": {
                "text": text,
                "mood": sentiment,
                "timestamp": datetime.now().isoformat()
            }
        }}
    )

    return {"sentiment": sentiment}


@app.get("/churned-customers")
def churned_customers():
    churned = customer_collection.find({"churned": True}, {"_id": 0})
    return list(churned)

@app.get("/products-in-demand")
def products_in_demand():
    customers = customer_collection.find({}, {"purchases": 1})
    all_products = [item for doc in customers for item in doc.get("purchases", [])]
    counter = Counter(all_products)
    return counter.most_common(10)

@app.get("/recommendations/{category}")
def get_recommendations(category: str):
    return product_catalog.get(category, [])

# @app.get("/legacy-dummy-recommendations/{category}")
def legacy_get_recommendations(category: str):
    dummy_products = {
        "Electronics": ["Smartwatch", "Bluetooth Speaker", "USB Hub"],
        "Clothing": ["T-Shirt", "Jeans", "Jacket"],
        "Groceries": ["Almonds", "Green Tea", "Dark Chocolate"]
    }
    return [{"name": item, "price": 299 + i * 100} for i, item in enumerate(dummy_products.get(category, []))]

@app.post("/purchase")
def purchase_product(data: dict):
    customer_id = data.get("customer_id")
    product_name = data.get("product_name")
    category = data.get("category")
    if not category or category.lower() == "unknown":
         return {"error": "Invalid category"}
    price = data.get("price")

    if not all([customer_id, product_name, category, price]):
        return {"error": "Missing fields"}

    product = {
        "product_name": product_name,
        "category": category,
        "price": price,
        "rating": None
    }

    result = customer_collection.update_one(
        {"customer_id": customer_id},
        {"$push": {"order_history": product}}
    )

    if result.modified_count == 1:
        return {"message": "Purchase added"}
    else:
        return {"error": "Customer not found"}



@app.post("/rate-order")
def rate_order(data: dict):
    customer_id = data.get("customer_id")
    product_name = data.get("product_name")
    rating = data.get("rating")

    result = customer_collection.update_one(
        {
            "customer_id": customer_id,
            "order_history.product_name": product_name
        },
        {
            "$set": {"order_history.$.rating": rating}
        }
    )

    if result.modified_count == 1:
        return {"message": "Rating updated"}
    else:
        return {"error": "Could not update rating"}

@app.get("/default-products")
def get_default_products():
    return default_products

