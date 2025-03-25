import streamlit as st
import requests
import time
import datetime
import base64
import json
from streamlit_ace import st_ace

# Initialize session state if not exists
if "messages" not in st.session_state:
    st.session_state.messages = []
    
if "conversation_history" not in st.session_state:
    st.session_state.conversation_history = []

def save_message(role, content=None, code=None, language=None):
    """Save message to conversation history"""
    message = {
        "role": role,
        "timestamp": datetime.datetime.utcnow().isoformat(),
    }
    
    if content:
        message["content"] = content
    if code:
        message["code"] = code
        message["language"] = language
        
    st.session_state.conversation_history.append(message)
    st.session_state.messages.append(message)

def query_ai(message):
    """Send user input to Azure OpenAI model and return response."""
    API_URL = "https://bbazuresc-openai.openai.azure.com/openai/deployments/GPT3_5/chat/completions?api-version=2023-09-15-preview"
    API_KEY = ""
    
    # Include conversation history in the prompt
    conversation = [
        {"role": msg["role"], "content": msg.get("content", "")} 
        for msg in st.session_state.conversation_history
    ]
    conversation.append({"role": "user", "content": message})
    
    payload = {
        "messages": conversation,
        "max_tokens": 500,
        "temperature": 0.9,
        "frequency_penalty": 0,
        "presence_penalty": 0,
        "top_p": 0.95,
        "stop": None
    }

    headers = {
        "Content-Type": "application/json",
        "api-key": API_KEY,
        "bb-decoded-vid": "1234",
        "X-Channel": "BB-Android",
        "X-Tracker": "listingGptCall",
        "X-Entry-Context": "bb-b2c",
        "X-Entry-Context-Id": "100",
        "X-Timestamp": datetime.datetime.utcnow().isoformat() + "Z",
        "X-Caller": "listing-svc",
        "x-project": "mm-canary",
        "bb-decoded-mid": "32517608"
    }

    try:
        response = requests.post(API_URL, json=payload, headers=headers)
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"].strip()
    except Exception as e:
        return f"⚠️ Error: {str(e)}"

def extract_code_blocks(text):
    """Extract code blocks from text"""
    if "```" not in text:
        return [{"type": "text", "content": text}]
        
    blocks = []
    parts = text.split("```")
    
    for i, part in enumerate(parts):
        if i % 2 == 0:
            if part.strip():
                blocks.append({"type": "text", "content": part.strip()})
        else:
            lines = part.strip().split('\n', 1)
            if len(lines) > 1:
                language = lines[0].strip().lower()
                code = lines[1].strip()
                blocks.append({
                    "type": "code",
                    "language": language,
                    "content": code
                })
    
    return blocks

def format_code(code, language):
    """Format code based on language"""
    if language == "json":
        try:
            return json.dumps(json.loads(code), indent=2)
        except:
            pass
    return code

# Page config
st.set_page_config(page_title="BB-GPT", page_icon="bb.svg", layout="wide")

# Header
try:
    with open("bb.png", "rb") as img_file:
        image_base64 = base64.b64encode(img_file.read()).decode()
        st.markdown(
            f"""
            <div style="display: flex; align-items: center;">
                <img src="data:image/png;base64,{image_base64}" width="200" style="margin-right: 10px;">
                <h1 style="margin: 0;">BB-GPT</h1>
            </div>
            """,
            unsafe_allow_html=True
        )
except:
    st.title("BB-GPT")

# Display chat history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        if "content" in msg:
            if "```" in msg["content"]:
                blocks = extract_code_blocks(msg["content"])
                for block in blocks:
                    if block["type"] == "text":
                        st.markdown(block["content"])
                    else:
                        formatted_code = format_code(block["content"], block["language"])
                        st_ace(
                            value=formatted_code,
                            language=block["language"],
                            theme="monokai",
                            height=300,
                            font_size=14,
                            show_gutter=True,
                            show_print_margin=True,
                            wrap=True,
                            key=f"code_{time.time()}"
                        )
            else:
                st.markdown(msg["content"])
        if "code" in msg:
            st_ace(
                value=msg["code"],
                language=msg["language"],
                theme="monokai",
                height=300,
                font_size=14,
                show_gutter=True,
                show_print_margin=True,
                wrap=True,
                key=f"code_{time.time()}"
            )

# Chat input
user_input = st.chat_input("Type your message...")
if user_input:
    # Save and display user message
    save_message("user", content=user_input)
    with st.chat_message("user"):
        st.markdown(user_input)

    # Get AI response
    with st.chat_message("assistant"):
        response = query_ai(user_input)
        
        if "```" in response:
            blocks = extract_code_blocks(response)
            for block in blocks:
                if block["type"] == "text":
                    message_placeholder = st.empty()
                    full_response = ""
                    for word in block["content"].split():
                        full_response += word + " "
                        message_placeholder.markdown(full_response + "▌")
                        time.sleep(0.02)
                    message_placeholder.markdown(full_response)
                else:
                    formatted_code = format_code(block["content"], block["language"])
                    st_ace(
                        value=formatted_code,
                        language=block["language"],
                        theme="monokai",
                        height=300,
                        font_size=14,
                        show_gutter=True,
                        show_print_margin=True,
                        wrap=True,
                        key=f"code_{time.time()}"
                    )
        else:
            message_placeholder = st.empty()
            full_response = ""
            for word in response.split():
                full_response += word + " "
                message_placeholder.markdown(full_response + "▌")
                time.sleep(0.02)
            message_placeholder.markdown(full_response)
        
        save_message("assistant", content=response)
