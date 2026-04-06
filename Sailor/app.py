import streamlit as st
import datetime
import math

# --- STEP 1: UI CONFIG ---
st.set_page_config(page_title="The Snail's Pace", page_icon="🐌", layout="centered")

# --- STEP 2: STYLED CSS (For that 'Classical' feel) ---
st.markdown("""
    <style>
    .main { background-color: #fdfaf5; }
    .stTextArea textarea { font-family: 'Georgia', serif; background-color: #fffdfa; }
    </style>
    """, unsafe_allow_name_with_html=True)

# --- STEP 3: THE "RELIABILITY" ENGINE (Core Logic) ---
def get_delivery_info(city_from, city_to):
    # Mock distance logic to prevent "Black Screen" hangs
    # In Phase 2, we will reconnect this to a real Map API
    distances = {
        ("Ludhiana", "London"): 6700,
        ("Ludhiana", "New York"): 11000,
        ("Ludhiana", "Tokyo"): 6000,
        ("London", "New York"): 5500
    }
    # Default distance if not in mock list
    dist = distances.get((city_from, city_to), 1500) 
    
    # Snail Logic: 1 hour per 500km
    hours = dist / 500
    arrival = datetime.datetime.now() + datetime.timedelta(hours=hours)
    return dist, hours, arrival

# --- STEP 4: APP INTERFACE ---
st.title("🐌 The Snail's Pace")
st.write("A global penpal network built on **Trust** and **Patience**.")

# Sidebar for User Stats
with st.sidebar:
    st.header("📜 Your Profile")
    my_city = st.selectbox("Your Location", ["Ludhiana", "London", "New York", "Tokyo"])
    
    # Data Science Metric: Reliability Score
    # We use st.session_state to keep track of "Sent" letters during this session
    if 'sent_count' not in st.session_state:
        st.session_state.sent_count = 0
        
    reliability = 85 + (st.session_state.sent_count * 2)
    st.metric("Reliability Score", f"{min(reliability, 100)}%", delta=f"{st.session_state.sent_count} letters")
    st.info("High scores unlock faster 'Air Mail' stamps.")

# Main Letter Area
target_city = st.selectbox("Write to a Penpal in:", ["London", "New York", "Tokyo", "Ludhiana"])

if my_city == target_city:
    st.warning("Try writing to someone in a different city to experience the 'Snail' delay!")

letter_body = st.text_area("Your Message:", placeholder="Dear Friend, I hope this letter finds you well...", height