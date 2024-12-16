import streamlit as st
from openai import OpenAI
import json
import os

DB_FILE = 'db.json'

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

    # Handle creating a new chat session
    if selected_session == "New Chat":
        new_session_id = str(len(db['chat_sessions']))
        st.session_state['active_session'] = len(db['chat_sessions'])
        db['chat_sessions'][new_session_id] = []  # New chat history for the session
        with open(DB_FILE, 'w') as file:
            json.dump(db, file)
        st.rerun()

    # Get the active session's chat history
    chat_history = db['chat_sessions'][session_names[st.session_state['active_session']]]

    # Add a text input for the user to give instructions (e.g., "You are an investment analyzer")
    instructions = st.text_input("Provide instructions for the assistant:", value="You are an investment analyzer, and you should always ask relevant follow-up questions to encourage deeper analysis based on the user's responses. Your goal is to guide the user through the investment evaluation process, providing insights and asking for more information where necessary to provide a thorough analysis. For example, if the user asks about a potential investment, you should ask questions about the investment type, location, market trends, or other relevant factors.")

    # If instructions are provided, add them to the chat history
    if instructions and not any(m["role"] == "system" for m in chat_history):  # Avoid adding multiple system instructions
        chat_history.insert(0, {"role": "system", "content": instructions})
        with open(DB_FILE, 'w') as file:
            json.dump(db, file)
        st.experimental_rerun()

    # Display chat messages from the selected session
    for message in chat_history:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Accept user input
    if prompt := st.chat_input("Please ask a question:"):
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

        # Store updated chat history in db.json
        db['chat_sessions'][session_names[st.session_state['active_session']]] = chat_history
        with open(DB_FILE, 'w') as file:
            json.dump(db, file)

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
