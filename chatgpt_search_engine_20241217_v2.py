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
        openai.models.list()  # Simple call to validate the key
        return True
    except openai.AuthenticationError:
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
    models = ["gpt-4o-mini", "gpt-4o", "gpt-3.5-turbo"]
    selected_model = st.sidebar.selectbox("Select OpenAI Model", models)

    # Multi-session management
    if "chat_sessions" not in db:
        db["chat_sessions"] = {}
    session_names = list(db["chat_sessions"].keys())
    selected_session = st.sidebar.selectbox(
        "Select Chat Session",
        session_names + ["New Chat"],
        index=len(session_names) if session_names else 0
    )
    if selected_session == "New Chat":
        new_session_name = st.sidebar.text_input("Enter a name for the new session")
        if st.sidebar.button("Create Session"):
            if new_session_name:
                db["chat_sessions"][new_session_name] = [{"role": "system", "content": DEFAULT_PROMPT}]
                with open(DB_FILE, 'w') as file:
                    json.dump(db, file)
                st.rerun()
            else:
                st.sidebar.error("Session name cannot be empty.")
    elif st.sidebar.button("Clear Chat"):
        db["chat_sessions"][selected_session] = [{"role": "system", "content": DEFAULT_PROMPT}]
        with open(DB_FILE, 'w') as file:
            json.dump(db, file)
        st.rerun()

    # Load chat history for selected session
    chat_history = db["chat_sessions"].get(selected_session, [])

    # Display chat messages
    for message in chat_history:
        if message["role"] != "system":
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

    # Accept user input
    user_input = st.chat_input("Type your message:")
    if user_input:
        with st.chat_message("user"):
            st.markdown(user_input)
        chat_history.append({"role": "user", "content": user_input})
        
        # Check for "search" keyword
        if "search" in user_input.lower():
            search_results = live_web_search(
                user_input,
                st.session_state.google_api_key,
                st.session_state.google_cse_id,
                excluded_domains=["reddit.com"]
            )
            snippets = [result["snippet"] for result in search_results]
            response_content = "\n\n".join(snippets) if snippets else "No results found."
        else:
            # Generate OpenAI response
            response_stream = openai.chat.completions.create(
                model=selected_model,
                messages=chat_history,
                stream=True
            )
            response_content = ""
            with st.chat_message("assistant"):
                for chunk in response_stream:
                    chunk_content = chunk.choices[0].delta.get("content", "")
                    response_content += chunk_content
                    st.write(chunk_content)

        chat_history.append({"role": "assistant", "content": response_content})
        db["chat_sessions"][selected_session] = chat_history
        with open(DB_FILE, 'w') as file:
            json.dump(db, file)

if __name__ == "__main__":
    main()
