 
import streamlit as st
import requests

st.set_page_config(page_title="Walmart AI Dashboard",layout="wide")
st.title("🛍️ Walmart AI Customer Insights") 

try:
   res = requests.get("http://127.0.0.1:8000/customers")
   res.raise_for_status()
   customers = res.json()
   st.success(f"Loaded {len(customers)} customers!")
except requests.exceptions.RequestException as e:
   st.error("Failed to load customer data.")
   st.exception(e)
   st.stop()

selected_id = st.sidebar.selectbox("Select a Customer ID",options=[c["customer_id"] for c in customers],)

customer = next((c for c in customers if c["customer_id"] == selected_id),None)

if customer:
   st.subheader(f"{customer['name']}(ID:{customer['customer_id']})")
   st.write("📊 Customer Details",customer)
   if customer.get("satisfaction_score",5)<3:
         st.warning("⚠️ Low satisfaction score detected!")
   if customer.get("flagged"):
         st.error("🚨 This customer is flagged for review.")