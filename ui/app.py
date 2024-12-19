import streamlit as st
import asyncio
import websockets
import html
import uuid
import json

# Initialize session state
if "session_id" not in st.session_state:
    st.session_state["session_id"] = str(uuid.uuid4())
if "messages" not in st.session_state:
    st.session_state["messages"] = [{"role": "assistant", "content": "Hello! I am MetuBOT, here to assist you with information about courses at METU Informatics Institute. Feel free to ask me about course details, prerequisites, and more!"}]
if "stop" not in st.session_state:
    st.session_state["stop"] = False

# Title and logo section
col1, col2 = st.columns([0.8, 0.2])
with col1:
    st.title("💬 MetuBOT")
with col2:
    st.image("logo.png", width=100)
st.caption("🚀 A METU course support chatbot powered by KIZIR-AI")
# Sidebar with Stop and Clear Conversation buttons
with st.sidebar:
    st.title("Options")
    
    # Stop Button
    if st.button("Stop"):
        st.session_state["stop"] = True  # Signal to stop streaming
    # Clear Conversation Button
    if st.button("Clear Conversation", help="Warning: This will remove all chat history and reset the conversation."):
        st.session_state["messages"] = [{"role": "assistant", "content": "Hello! I am MetuBOT, here to assist you with information about courses at METU Informatics Institute. Feel free to ask me about course details, prerequisites, and more!"}]
        st.session_state["stop"] = False  # Reset the stop state
        st.session_state["session_id"] = str(uuid.uuid4())
        st.rerun()  # Refresh the interface to clear the chat

# Display chat history
for msg in st.session_state.messages:
    if msg["role"] == "assistant":
        st.markdown(
            f"""
            <div style='background-color: #f1f0f0; padding: 10px; border-radius: 10px; margin-bottom: 10px; color: black;
                        border: 1px solid #d1d1d1; max-width: 80%; float: left; clear: both; word-wrap: break-word; white-space: pre-wrap;'>
                <strong>Assistant:</strong> {msg['content']}
            </div>
            """,
            unsafe_allow_html=True
        )
    else:
        st.markdown(
            f"""
            <div style='background-color: #dcf8c6; padding: 10px; border-radius: 10px; margin-bottom: 10px; color: black;
                        border: 1px solid #b8e994; max-width: 80%; float: right; clear: both; word-wrap: break-word; white-space: pre-wrap;'>
                <strong>You:</strong> {msg['content']}
            </div>
            """,
            unsafe_allow_html=True
        )

# Chat input
user_input = st.chat_input("Your message")

# Asynchronous function to fetch response from WebSocket
async def fetch_response_stream(user_message):
    uri = "ws://localhost:9090/llm"
    try:
        print(st.session_state["session_id"])
        async with websockets.connect(uri) as websocket:
            package = {"session_id": st.session_state["session_id"], "message": user_message}
            await websocket.send(json.dumps(package))

            response = ""
            async for word in websocket:
                if st.session_state["stop"]:
                    break
                if word == "<end-of-response>":
                    break

                # Print the raw WebSocket message for debugging
                print(f"Raw WebSocket message: {word}")
                response += word
                
                # Yield the incremental response
                yield response

    except websockets.exceptions.ConnectionClosedError:
        yield "Connection was closed unexpectedly."

# Handle user input and streaming response
if user_input:
    # Append user's message to the chat immediately
    st.session_state["messages"].append({"role": "user", "content": user_input})
    
    # Display user message immediately
    st.markdown(
        f"""
        <div style='background-color: #dcf8c6; padding: 10px; border-radius: 10px; margin-bottom: 10px; color: black;
                    border: 1px solid #b8e994; max-width: 80%; float: right; clear: both; word-wrap: break-word; white-space: pre-wrap;'>
            <strong>You:</strong> {user_input}
        </div>
        """,
        unsafe_allow_html=True
    )

    # Placeholder for assistant's streamed response
    assistant_placeholder = st.empty()
    partial_response = ""

    async def display_streamed_response():
        async for chunk in fetch_response_stream(user_input):
            partial_response = html.escape(chunk.rstrip())
            assistant_placeholder.markdown(
                f"""
                <div style='background-color: #f1f0f0; padding: 10px; border-radius: 10px; margin-bottom: 10px; color: black;
                            border: 1px solid #d1d1d1; max-width: 80%; float: left; clear: both; word-wrap: break-word; white-space: pre-wrap;'>
                    <strong>Assistant:</strong> {partial_response}
                </div>
                """,
                unsafe_allow_html=True
            )
        st.session_state["messages"].append({"role": "assistant", "content": partial_response})

    asyncio.run(display_streamed_response())
