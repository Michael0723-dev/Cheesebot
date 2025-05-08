import sys
import os
import streamlit as st

st.set_page_config(page_title="Cheese RAG Chatbot", page_icon="��", layout="wide")

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import streamlit as st
from chatbot.rag_chatbot import ChatSession
import json

# --- Load metadata for dropdowns (brands, types, locations, price ranges) ---
@st.cache_data
def load_metadata():
    # Load processed cheese data to extract unique metadata values
    data_path = os.path.join("data", "processed_cheese_products.json")
    with open(data_path, "r", encoding="utf-8") as f:
        products = json.load(f)
    brands = sorted(set(p["metadata"].get("location", "Unknown") for p in products))
    price_min = min(p["metadata"].get("price_value", 0) for p in products)
    price_max = max(p["metadata"].get("price_value", 0) for p in products)
    return brands, price_min, price_max

brands, price_min, price_max = load_metadata()

# --- Session State for Chat ---
if "chat_session" not in st.session_state:
    st.session_state.chat_session = ChatSession()
if "history" not in st.session_state:
    st.session_state.history = []

# --- Sidebar: Metadata Filters ---
st.sidebar.header("Filter Cheeses")
selected_brand = st.sidebar.selectbox("Brand/Location", ["All"] + brands)
price_range = st.sidebar.slider("Price ($)", float(price_min), float(price_max), (float(price_min), float(price_max)))

def get_filter_dict():
    filters = {}
    if selected_brand != "All":
        filters["location"] = selected_brand
    filters["price_value"] = {"$gte": price_range[0], "$lte": price_range[1]}
    return filters

# --- Main Chat UI ---
st.title("🧀 Cheese RAG Chatbot")
st.markdown(
    """
    <style>
    .stChatMessage { font-size: 1.1rem; }
    .stMarkdown img { max-width: 120px; border-radius: 8px; margin: 0.5em 0; }
    .ref-product { background: #f8f9fa; border-radius: 8px; padding: 0.7em; margin-bottom: 0.5em; }
    </style>
    """,
    unsafe_allow_html=True,
)

# --- Chat Input ---
with st.form("chat_form", clear_on_submit=True):
    user_input = st.text_input("Ask a cheese question:", key="user_input", placeholder="e.g., What is a good mozzarella for pizza?")
    submitted = st.form_submit_button("Send")

if submitted and user_input.strip():
    filters = get_filter_dict()
    result = st.session_state.chat_session.ask(user_input, filter_dict=filters)
    st.session_state.history.append({
        "user": user_input,
        "bot": result["answer"],
        "context": result["context"]
    })

# --- Display Chat History ---
for entry in st.session_state.history:
    with st.chat_message("user"):
        st.markdown(entry["user"])
    with st.chat_message("assistant"):
        st.markdown(entry["bot"])
        # Reference context display
        if entry["context"]:
            st.markdown("**Reference Products:**")
            for prod in entry["context"]:
                with st.expander(prod.get("name", "Cheese Product")):
                    cols = st.columns([1, 3])
                    with cols[0]:
                        if prod.get("image_url"):
                            st.image(prod["image_url"], use_container_width=True)
                    with cols[1]:
                        st.markdown(
                            f"""
                            **Description:** {prod.get('description', '')}
                            \n**Price:** ${prod.get('price_value', 0):.2f}
                            \n**Location:** {prod.get('location', '')}
                            \n[View Product]({prod.get('source_url', '')})
                            """
                        )

# --- Nice UX: Scroll to bottom on new message ---
st.markdown(
    """
    <script>
    var chat = window.parent.document.querySelector('.block-container');
    if (chat) { chat.scrollTop = chat.scrollHeight; }
    </script>
    """,
    unsafe_allow_html=True,
)