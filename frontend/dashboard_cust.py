import streamlit as st
import requests

st.set_page_config(page_title="Walmart Customer Dashboard", layout="centered")
st.title("🛍️ Walmart Customer Dashboard")

# ------------------ Auth Toggle ------------------
auth_mode = st.radio("Choose mode", ["Login", "Signup"])

# ------------------ Signup ------------------
if auth_mode == "Signup":
    st.subheader("📝 Sign up")
    name = st.text_input("Your Name")
    email = st.text_input("Email")

    if st.button("Register"):
        resp = requests.post("http://localhost:8000/signup", json={"name": name, "email": email})
        data = resp.json()

        if "error" in data:
            st.error(data["error"])
        else:
            st.success("✅ Account created successfully! Please switch to Login and sign in.")
            st.session_state["signup_email"] = email  # optionally prefill login
            st.stop()  # stop further rendering (important!)

# ------------------ Login ------------------
elif auth_mode == "Login":
    st.subheader("🔐 Login")
    default_email = st.session_state.get("signup_email", "")
    email = st.text_input("Email", value=default_email)

    if st.button("Login"):
        resp = requests.post("http://localhost:8000/login", json={"email": email})
        data = resp.json()

        if "error" in data:
            st.error(data["error"])
        else:
            st.success("✅ Logged in successfully!")
            st.session_state["customer_id"] = data["customer_id"]
            st.session_state["logged_in"] = True
            st.session_state["profile"] = data

# ------------------ Show Dashboard ------------------
if st.session_state.get("logged_in"):
    profile = st.session_state["profile"]
    customer_id = profile["customer_id"]

    st.header(f"👤 Welcome, {profile['name']}")
    st.write(f"📧 Email: {profile.get('email', 'N/A')}")
    st.write(f"🎯 Satisfaction Score: {profile.get('satisfaction_score', 'N/A')}")

    # ------------------ Purchase History ------------------
    st.subheader("🧾 Purchase History")
    order_history = profile.get("order_history", [])
    for order in order_history:
        if isinstance(order, dict) and "product_name" in order:
            product = order["product_name"]
            category = order.get("category", "N/A")
            rating = order.get("rating", "N/A")
            st.write(f"- {product} ({category}) – ⭐ {rating}")
        else:
            st.warning("⚠️ Invalid order format")

    # ------------------ Recommendations ------------------
    last_order = order_history[-1] if order_history else None
    if last_order:
        category = last_order["category"]
        st.subheader("🛒 Recommended for You")
        if category.lower() != "unknown":
            st.write(f"Because you bought a {category} product recently:")
        else:
            st.write("Based on your recent purchase history:")

        recommended = requests.get(f"http://localhost:8000/recommendations/{category}")
        for product in recommended.json():
            st.markdown(f"**{product['name']}** – ₹{product['price']}")
            if st.button(f"🛍️ Shop Now: {product['name']}"):
                payload = {
                    "customer_id": customer_id,
                    "product_name": product["name"],
                    "category": category,
                    "price": product["price"]
                }
                res = requests.post("http://localhost:8000/purchase", json=payload)
                if res.status_code == 200:
                    st.success("✅ Order placed successfully!")
                else:
                    st.error("❌ Failed to place order.")

    # ------------------ Default Products ------------------
    st.subheader("🛒 Explore Products")
    default_products = requests.get("http://localhost:8000/default-products").json()

    for product in default_products:
        st.markdown(f"**{product['name']}** – ₹{product['price']}")
        if st.button(f"🛒 Shop: {product['name']}", key=f"default_{product['name']}"):
            payload = {
                "customer_id": customer_id,
                "product_name": product["name"],
                "category": product["category"],
                "price": product["price"]
            }
            res = requests.post("http://localhost:8000/purchase", json=payload)
            if res.status_code == 200:
                st.success("✅ Added to your purchases!")
            else:
                st.error("❌ Failed to add.")

    # ------------------ Feedback & Sentiment ------------------
    st.subheader("💬 Share your Feedback")
    feedback = st.text_area("How was your recent experience?")

    if st.button("Analyze Mood"):
        sentiment_resp = requests.post("http://localhost:8000/analyze-sentiment", json={
            "text": feedback,
            "customer_id": customer_id
        })

        if sentiment_resp.status_code == 200:
            mood_data = sentiment_resp.json()["sentiment"]

            # If sentiment is a dict, extract the label
            if isinstance(mood_data, dict) and "label" in mood_data:
                mood_label = mood_data["label"]
                st.write(f"🧠 Detected Mood: **{mood_label.upper()}**")
            else:
                # If sentiment is just a string
                st.write(f"🧠 Detected Mood: **{mood_data.upper()}**")
        else:
            st.error("❌ Could not analyze mood.")

    # ------------------ Rating Last Order ------------------
    if last_order:
        st.subheader("⭐ Rate Your Last Purchase")
        rating_input = st.slider("How would you rate it?", 1, 5)

        if st.button("Submit Rating"):
            res = requests.post("http://localhost:8000/rate-order", json={
                "customer_id": customer_id,
                "product_name": last_order.get("product_name"),
                "rating": rating_input
            })
            if res.status_code == 200:
                st.success("✅ Rating submitted!")
                last_order["rating"] = rating_input  # update locally to reflect immediately
            else:
                st.error("❌ Failed to submit rating.")

        # ------------------ Alerts ------------------
        last_rating = last_order.get("rating")
        if isinstance(last_rating, (int, float)) and last_rating <= 2:
            st.warning("⚠️ Your last order had a low rating. We're working on it!")

        category = last_order.get("category", "various categories")
        if category.lower() != "unknown":
            st.info(f"✨ Based on your activity, you might love more from **{category}**!")
        else:
            st.info("✨ Based on your activity, we've selected some items you might like.")

    # ------------------ Logout ------------------
    if st.button("Logout"):
        st.session_state.clear()
        st.success("Logged out!")
