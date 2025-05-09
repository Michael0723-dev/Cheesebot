import streamlit as st
import sys
import os
from pathlib import Path
import requests
from PIL import Image
from io import BytesIO
import time

# Add project root to Python path
project_root = str(Path(__file__).parent.parent)
sys.path.append(project_root)

from chatbot.bot import ChatSession

# Initialize session state for chat history
if 'chat_session' not in st.session_state:
    st.session_state.chat_session = ChatSession()
if 'messages' not in st.session_state:
    st.session_state.messages = []

def clear_chat_history():
    """Clear the chat history and reset the chat session"""
    st.session_state.messages = []
    st.session_state.chat_session = ChatSession()
    st.rerun()

# Page config
st.set_page_config(
    page_title="Cheese Expert Assistant",
    page_icon="🧀",
    layout="wide"
)

# Header with clear button

st.title("🧀 Cheese Expert Assistant")
with st.sidebar:
    if st.button("Clear Chat History", type="secondary"):
        clear_chat_history()

st.markdown("Ask me anything about cheese products!")

# Chat container
chat_container = st.container()

def display_product_details(product):
    """Display product details in a structured format"""
    col1, col2 = st.columns([0.4, 0.6])
    
    with col1:
        if "image_url" in product and product["image_url"] != "N/A":
            try:
                img_response = requests.get(product["image_url"])
                if img_response.status_code == 200:
                    image = Image.open(BytesIO(img_response.content))
                    st.image(image, use_container_width=True)
            except Exception as e:
                st.error(f"Error loading image: {str(e)}")
    
    with col2:
        # Product details
        st.markdown(f"### {product.get('name', 'Cheese product')}")
        st.markdown(f"**Type:** {product.get('cheese_type', 'N/A')}")
        st.markdown(f"**Brand:** {product.get('brand', 'N/A')}")
        st.markdown(f"**Form:** {product.get('cheese_form', 'N/A')}")
        
        # Price and weight information
        price_each = product.get('price_each', 0)
        price_per_lb = product.get('price_per_lb', 0)
        lb_per_each = product.get('lb_per_each', 0)
        
        st.markdown(f"**Price:** {price_each:.2f}$")
        # if price_per_lb:
        #     st.markdown(f"**Price per lb:** ${price_per_lb:.2f}")
        if lb_per_each:
            st.markdown(f"**Weight:** {lb_per_each:.2f}lb")
        # Source URL button
        if "source_url" in product and product["source_url"] != "N/A":
            st.link_button("View Product Source", product["source_url"])        
        # Description in expander
        if "description" in product and product["description"]:
            with st.expander("Product Description"):
                st.write(product["description"])
        


# Display chat history
with chat_container:
    for message in st.session_state.messages:
        if message["role"] == "user":
            st.chat_message("user").write(message["content"])
        else:
            with st.chat_message("assistant"):
                st.write(message["content"])
                # Display product details if available
                if "context" in message and message["context"]:
                    st.markdown("---")
                    st.markdown("### Suggested Products")
                    for product in message["context"]:
                        display_product_details(product)
                        st.markdown("---")

# Input area
st.markdown("---")  # Add a separator
user_input = st.chat_input("Ask about cheese...")


if user_input:
    # Add user message to chat
    st.session_state.messages.append({"role": "user", "content": user_input})
    st.chat_message("user").write(user_input)

    # Create a placeholder for the assistant's response
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""
        
        # Get bot response with streaming
        response = st.session_state.chat_session.ask(user_input)
        
        # Stream the response
        if isinstance(response, dict) and "answer" in response:
            answer = response["answer"]
            for chunk in answer.split():
                full_response += chunk + " "
                message_placeholder.write(full_response + "▌")
                time.sleep(0.05)  # Add a small delay for visual effect
            
            # Display the final response
            message_placeholder.write(full_response)
            
            # Display product details if available
            if "context" in response and response["context"]:
                st.markdown("---")
                st.markdown("### Suggested Products")
                for product in response["context"]:
                    display_product_details(product)
                    st.markdown("---")

            # Add bot response to chat history
            st.session_state.messages.append({
                "role": "assistant",
                "content": full_response,
                "context": response.get("context", [])
            })
        else:
            st.error("Error: Unexpected response format from chatbot")