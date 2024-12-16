import streamlit as st
from openai import OpenAI
import json
import os

DB_FILE = 'db.json'

def generate_session_name(messages):
    # Generate a session name based on the first user message or summary of the discussion
    # Here, we use the first user message as the basis for naming the session
    first_user_message = next((m['content'] for m in messages if m['role'] == 'user'), 'General Discussion')
    return f"Chat about: {first_user_message[:30]}..."  # truncate to the first 30 characters

def main():
    client = OpenAI(api_key=st.session_state.openai_api_key)

    # List of models
    models = ["gpt-4o-mini", "gpt-4o", "gpt-4-turbo", "gpt-4", "gpt-3.5-turbo"]

    # Create a select box for the models
    st.session_state["openai_model"] = st.sidebar.selectbox("Select OpenAI model", models, index=0)

    # Load chat history from db.json
    with open(DB_FILE, 'r') as file:
        db = json.load(file)

    # Initialize chat_sessions if not present
    if 'chat_sessions' not in db:
        db['chat_sessions'] = {}

    # If 'active_session' not in session_state, set it to 0 (first session)
    if 'active_session' not in st.session_state:
        st.session_state['active_session'] = 0

    # Display existing chat sessions
    session_names = list(db['chat_sessions'].keys())
    selected_session = st.sidebar.selectbox(
        "Select Chat Session", 
        options=session_names + ["New Chat"], 
        index=st.session_state['active_session']
    )

    # Handle selecting a new session or creating a new one
    if selected_session != "New Chat" and selected_session != session_names[st.session_state['active_session']]:
        st.session_state['active_session'] = session_names.index(selected_session)

    # If "New Chat" is selected, create a new session with a generated name
    if selected_session == "New Chat":
        new_session_id = generate_session_name([])  # Start with an empty message list
        st.session_state['active_session'] = len(db['chat_sessions'])
        db['chat_sessions'][new_session_id] = []  # New chat history for the session
        with open(DB_FILE, 'w') as file:
            json.dump(db, file)
        st.rerun()

    # Get the active session's chat history
    chat_history = db['chat_sessions'][session_names[st.session_state['active_session']]]

    # Display chat messages from the selected session
    for message in chat_history:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Accept user input
    if prompt := st.chat_input("What is up?"):
        # Add user message to chat history
        chat_history.append({"role": "user", "content": prompt})
        # Display user message in chat message container
        with st.chat_message("user"):
            st.markdown(prompt)

        # Display assistant response in chat message container
        with st.chat_message("assistant"):
            stream = client.chat.completions.create(
                model=st.session_state["openai_model"],
                messages=[{"role": m["role"], "content": m["content"]} for m in chat_history],
                stream=True,
            )
            response = st.write_stream(stream)
        chat_history.append({"role": "assistant", "content": response})

        # Update session name based on the first user message or summary of the chat
        new_session_name = generate_session_name(chat_history)
        if new_session_name != selected_session:
            # Update session name in db if conversation content has changed
            db['chat_sessions'][new_session_name] = db['chat_sessions'].pop(session_names[st.session_state['active_session']])

        # Store updated chat history in db.json
        db['chat_sessions'][new_session_name] = chat_history
        with open(DB_FILE, 'w') as file:
            json.dump(db, file)

        # Update active session index
        session_names = list(db['chat_sessions'].keys())
        st.session_state['active_session'] = session_names.index(new_session_name)

    # Add a "Clear Chat" button to the sidebar for the current session
    if st.sidebar.button('Clear Chat'):
        db['chat_sessions'][session_names[st.session_state['active_session']]] = []
        with open(DB_FILE, 'w') as file:
            json.dump(db, file)
        st.rerun()

if __name__ == '__main__':
    if 'openai_api_key' in st.session_state and st.session_state.openai_api_key:
        main()
    else:
        # if the DB_FILE not exists, create it
        if not os.path.exists(DB_FILE):
            with open(DB_FILE, 'w') as file:
                db = {
                    'openai_api_keys': [],
                    'chat_sessions': {}
                }
                json.dump(db, file)

        # load the database
        else:
            with open(DB_FILE, 'r') as file:
                db = json.load(file)

        # display the selectbox from db['openai_api_keys']
        selected_key = st.selectbox(
            label="Existing OpenAI API Keys", 
            options=db['openai_api_keys']
        )

        # a text input box for entering a new key
        new_key = st.text_input(
            label="New OpenAI API Key", 
            type="password"
        )

        login = st.button("Login")

        # if new_key is given, add it to db['openai_api_keys']
        # if new_key is not given, use the selected_key
        if login:
            if new_key:
                db['openai_api_keys'].append(new_key)
                with open(DB_FILE, 'w') as file:
                    json.dump(db, file)
                st.success("Key saved successfully.")
                st.session_state['openai_api_key'] = new_key
                st.rerun()
            else:
                if selected_key:
                    st.success(f"Logged in with key '{selected_key}'")
                    st.session_state['openai_api_key'] = selected_key
                    st.rerun()
                else:
                    st.error("API Key is required to login")
