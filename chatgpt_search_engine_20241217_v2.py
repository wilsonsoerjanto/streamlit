import streamlit as st
import openai
import requests
import json
import os

DB_FILE = 'db.json'

DEFAULT_PROMPT = (
    "You are an investment analyzer, and after giving out an answer, you should always offer the user options for next action items "
    "(for example, 'Would you like me to ...?') to encourage deeper analysis based on the user's responses. "
    "Your goal is to guide the user through the investment evaluation process, providing insights and asking for more information where necessary. "
    "Always cite your sources and do not make up information."
)

# Sidebar key validation functions
def validate_openai_api_key(api_key):
    try:
        openai.api_key = api_key
        openai.Model.list()  # Simple call to validate the key
        return True
    except openai.error.AuthenticationError:
        return False

def validate_google_api_key(api_key, cse_id):
    try:
        response = requests.get(
            'https://www.googleapis.com/customsearch/v1',
            params={'q': 'test', 'key': api_key, 'cx': cse_id}
        )
        return response.status_code == 200
    except Exception:
        return False

# Live Web Search Function
def live_web_search(query, google_api_key, cse_id, excluded_domains=None):
    search_url = 'https://www.googleapis.com/customsearch/v1'
    params = {
        'q': query,
        'key': google_api_key,
        'cx': cse_id,
    }
    response = requests.get(search_url, params=params)
    response.raise_for_status()
    results = response.json()
    
    # Filter results from excluded domains
    if excluded_domains:
        results['items'] = [
            result for result in results.get('items', [])
            if not any(domain in result['link'] for domain in excluded_domains)
        ]
    return results.get('items', [])

# Main Function
def main():
    # Load or initialize database
    if not os.path.exists(DB_FILE):
        with open(DB_FILE, 'w') as file:
            json.dump({'openai_api_keys': [], 'chat_sessions': {}}, file)

    with open(DB_FILE, 'r') as file:
        db = json.load(file)

    st.sidebar.title("Chat Settings")
    
    # Input API keys
    openai_api_key = st.sidebar.text_input("Enter OpenAI API Key", type="password")
    google_api_key = st.sidebar.text_input("Enter Google API Key", type="password")
    google_cse_id = st.sidebar.text_input("Enter Google Search Engine ID")
    validate_keys = st.sidebar.button("Validate Keys")

    if validate_keys:
        if validate_openai_api_key(openai_api_key) and validate_google_api_key(google_api_key, google_cse_id):
            st.success("API Keys Validated!")
            st.session_state.openai_api_key = openai_api_key
            st.session_state.google_api_key = google_api_key
            st.session_state.google_cse_id = google_cse_id
        else:
            st.error("Invalid API Keys! Please check your entries.")
            return

    if 'openai_api_key' not in st.session_state:
        st.warning("Please enter valid API keys to proceed.")
        return

    openai.api_key = st.session_state.openai_api_key

    # Sidebar: Model Selection
    models = ["gpt-4-turbo", "gpt-4", "gpt-3.5-turbo"]
    selected_model = st.sidebar.selectbox("Select OpenAI Model", models)

    # Multi-session management
    if "chat_sessions" not in db:
        db["chat_sessions"] = {}
    session_names = list(db["chat_sessions"].keys())
    selected_session = st.sidebar.selectbox(
        "Select Chat Session",
        session_names + ["New Chat"],
        index=0 if session_names else -1
    )
    if selected_session == "New Chat":
        new_session_name = st.sidebar.text_input("Enter a name for the new session")
        if st.sidebar.button("Create Session"):
            db["chat_sessions"][new_session_name] = [{"role": "system", "content": DEFAULT_PROMPT}]
            with open(DB_FILE, 'w') as file:
                json.dump(db, file)
            st.experimental_rerun()
    elif st.sidebar.button("Clear Chat"):
        db["chat_sessions"][selected_sessi
