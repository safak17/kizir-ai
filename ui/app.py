import streamlit as st
import asyncio
import websockets
import html
import uuid 
import json
if "session_id" not in st.session_state:
    st.session_state["session_id"] = str(uuid.uuid4())

# Title and logo section
col1, col2 = st.columns([0.8, 0.2])
with col1:
    st.title("💬 MetuBOT")
with col2:
    st.image("logo.png", width = 100)
st.caption("🚀 A METU course support chatbot powered by KIZIR-AI")

# Initialize chat history and stop state if not already in session state
if "messages" not in st.session_state:
    st.session_state["messages"] = [{"role": "assistant", "content": "Hello! I am MetuBOT, here to assist you with information about courses at METU Informatics Institute. Feel free to ask me about course details, prerequisites, and more!"}]
if "stop" not in st.session_state:
    st.session_state["stop"] = False

# Display chat history and maintain placeholders for message styling
# Display chat history and maintain placeholders for message styling
placeholders = []
for msg in st.session_state.messages:
    placeholder = st.empty()
    if msg["role"] == "assistant":
        placeholder.markdown(
            f"""
            <div style='background-color: #f1f0f0; padding: 10px; border-radius: 10px; margin-bottom: 10px; color: black;
                        border: 1px solid #d1d1d1; max-width: 80%; float: left; clear: both; word-wrap: break-word; white-space: pre-wrap;'>
                <strong>Assistant:</strong> {msg['content']}
            </div>
            """,
            unsafe_allow_html=True
        )
    else:
        placeholder.markdown(
            f"""
            <div style='background-color: #dcf8c6; padding: 10px; border-radius: 10px; margin-bottom: 10px; color: black;
                        border: 1px solid #b8e994; max-width: 80%; float: right; clear: both; word-wrap: break-word; white-space: pre-wrap;'>
                <strong>You:</strong> {msg['content']}
            </div>
            """,
            unsafe_allow_html=True
        )
    placeholders.append(placeholder)


# Chat input field in the main area
user_input = st.chat_input("Your message")

# Sidebar with title, Stop button, and Clear Conversation button
with st.sidebar:
    st.title("Options")
    if st.button("Stop"):
        st.session_state["stop"] = True  # Set stop signal
    if st.button("Clear Conversation"):
        st.session_state["messages"] = [{"role": "assistant", "content": "Hello! I am MetuBOT, here to assist you with information about courses at METU Informatics Institute.\n\nFeel free to ask me about course details, prerequisites, and more!"}]
        st.session_state["stop"] = False
        st.rerun()  # Refresh the app to show the cleared conversation

# Asynchronous function to fetch response from WebSocket
async def fetch_response_stream(user_message):
    uri = "ws://localhost:9090/llm"
    try:
        async with websockets.connect(uri) as websocket:
            # Send message with session ID
            is_message = False
            is_continue = False
            package = {st.session_state["session_id"] +"SessionGuid"+ user_message}
            await websocket.send(package)

            response = ""
            async for word in websocket:
                if st.session_state["stop"]:
                    break
                if word == "<end-of-response>":
                    break

                # Parse the JSON response and extract the message
                try:
                    word_content = json.loads(word)
                except json.JSONDecodeError:
                    word_content = word  # Fallback to raw word if JSON parsing fails
                if 'SessionGuid' in word_content:
                    is_message = True
                    is_continue = True
                if(is_message):
                    word_content = word_content.split('SessionGuid', 1)[1]
                    is_message = False

                if is_continue:
                        
                    print(word_content)
                    response += word_content
                    yield response


    except websockets.exceptions.ConnectionClosedError:
        yield "Connection was closed unexpectedly."

# Handle user message submission
if user_input:
    st.session_state["stop"] = False
    st.session_state["messages"].append({"role": "user", "content": user_input})

    # Display user message immediately
    user_placeholder = st.empty()
    user_placeholder.markdown(
        f"""
        <div style='background-color: #dcf8c6; padding: 10px; border-radius: 10px; margin-bottom: 10px; color: black;
                    border: 1px solid #b8e994; max-width: 80%; float: right; clear: both;'>
            <strong>You:</strong> {user_input}
        </div>
        """,
        unsafe_allow_html=True
    )
    placeholders.append(user_placeholder)

    # Placeholder for the assistant's streamed response
    assistant_placeholder = st.empty()
    partial_response = ""  # Store incremental assistant response here
    placeholders.append(assistant_placeholder)

    # Stream and display the assistant's response
    async def display_streamed_response():
        async for chunk in fetch_response_stream(user_input):
            partial_response = html.escape(chunk.rstrip())  # Update partial response with each chunk
            # Update the displayed response incrementally
            assistant_placeholder.markdown(
                f"""
                <div style='background-color: #f1f0f0; padding: 10px; border-radius: 10px; margin-bottom: 10px; color: black;
                            border: 1px solid #d1d1d1; max-width: 80%; float: left; clear: both;'>
                    <strong>Assistant:</strong> {partial_response}</div> 
                """,
                unsafe_allow_html=True
            )
            if st.session_state["stop"]:
                break
        # Save the full or partial response when streaming is complete or stopped
        st.session_state["messages"].append({"role": "assistant", "content": partial_response})
        st.rerun()


    asyncio.run(display_streamed_response())
