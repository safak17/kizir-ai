import streamlit as st
import asyncio
import websockets

# Title with image on the right
col1, col2 = st.columns([3, 1])  # Adjust the proportions as needed

with col1:
    st.title("KIZIR AI MetuBOT")

with col2:
    # Replace 'metubot_logo.png' with your actual image file path
    st.image("logo.png", use_column_width=True)

# Initialize chat history and stop flag in session state
if "chat_history" not in st.session_state:
    st.session_state["chat_history"] = []
if "stop" not in st.session_state:
    st.session_state["stop"] = False

# Add an initial message from the bot when the app starts
if not st.session_state["chat_history"]:
    st.session_state["chat_history"].append(
        "Hello! I am MetuBOT, here to assist you with information about courses at METU Informatics Institute. "
        "Feel free to ask me about course details, prerequisites, and more!"
    )

async def chat_with_bot(user_message):
    uri = "ws://localhost:8000/ws"
    try:
        async with websockets.connect(uri) as websocket:
            await websocket.send(user_message)
            response = await websocket.recv()
            return response
    except websockets.exceptions.ConnectionClosedError:
        return "Connection was closed unexpectedly. Please try again."

def display_chat():
    st.write("## Chat History")
    for i, chat in enumerate(st.session_state["chat_history"]):
        # Define user and bot message colors
        user_bg_color = "#D1E7FD"
        bot_bg_color = "#F1F1F1"
        text_color = "black"  # Set text color to black for better readability
        
        # Differentiate styles for user and bot messages
        if i % 2 == 0:  # Bot message (initial message is always from the bot)
            st.markdown(f"""
                <div style='background-color: {bot_bg_color}; padding: 10px; border-radius: 10px; margin-bottom: 10px; color: {text_color};
                            white-space: pre-wrap; word-wrap: break-word; overflow-wrap: break-word; display: flex; flex-direction: column;'>
                    <strong>MetuBOT:</strong> <span style="margin-top: 5px;">{chat}</span>
                </div>
                """, unsafe_allow_html=True)
        else:  # User message
            st.markdown(f"""
                <div style='background-color: {user_bg_color}; padding: 10px; border-radius: 10px; margin-bottom: 10px; color: {text_color};
                            white-space: pre-wrap; word-wrap: break-word; overflow-wrap: break-word; display: flex; flex-direction: column;'>
                    <strong>You:</strong> <span style="margin-top: 5px;">{chat}</span>
                </div>
                """, unsafe_allow_html=True)

def main():
    st.sidebar.write("Enter your message:")
    
    # Message input box
    user_message = st.sidebar.text_area("Message", key="user_message", height=50, max_chars=500, placeholder="Type your message here...").strip()

    # Send button
    if st.sidebar.button("Send"):
        if user_message:
            # Reset stop flag before sending a new message
            st.session_state["stop"] = False

            # Retrieve response from the bot
            response = asyncio.run(chat_with_bot(user_message))

            # Check stop flag before updating the chat history
            if not st.session_state["stop"]:
                # Add both user message and bot response to chat history if not stopped
                st.session_state["chat_history"].append(user_message)
                st.session_state["chat_history"].append(response)
            st.sidebar.empty()  # Clear input

    # Stop button
    if st.sidebar.button("Stop"):
        st.session_state["stop"] = True  # Set stop flag to True
    
    display_chat()

if __name__ == "__main__":
    main()
