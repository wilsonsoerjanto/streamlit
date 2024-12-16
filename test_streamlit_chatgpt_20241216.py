import streamlit as st
from openai import OpenAI
import json
import os


DB_FILE = 'db.json'

def summarize_conversation(messages, max_messages=5):
    """Summarize the older conversation if the message history is too long."""
    if len(messages) > max_messages:
        # Summarize past conversations if the message count exceeds the max
        summary_prompt = "Summarize the following conversation briefly:\n"
        summary = client.chat.completions.create(
            model=st.session_state["openai_model"],
            messages=[{"role": "user", "content": summary_prompt + "\n".join(m['content'] for m in messages)}]
        )
        return summary['choices'][0]['message']['content']
    return messages

def main():
    client = OpenAI(api_key=st.session_state.openai_api_key)

    # List of models
    models = ["gpt-4o-mini", "gpt-4o", "gpt-4-turbo", "gpt-4", "gpt-3.5-turbo"]

    # Create a select box for the models
    st.session_state["openai_model"] = st.sidebar.selectbox("Select OpenAI model", models, index=0)

    # Load chat history from db.json
    with open(DB_FILE, 'r') as file:
        db = json.load(file)
    st.session_state.messages = db.get('chat_history', [])

    # Display chat messages from history on app rerun
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Accept user input
    if prompt := st.chat_input("Please ask a question:"):
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})
        # Display user message in chat message container
        with st.chat_message("user"):
            st.markdown(prompt)

        # Summarize the older messages if there are too many
        summarized_messages = summarize_conversation(st.session_state.messages)

        # Prepare messages for the GPT API with follow-up instructions
        system_instruction = (
            "You are an investment analyzer, and you should always ask relevant follow-up questions "
            "to encourage deeper analysis based on the user's responses. "
            "Your goal is to guide the user through the investment evaluation process, providing insights and "
            "asking for more information where necessary to provide a thorough analysis. "
            "For example, if the user asks about a potential investment, you should ask questions about the "
            "investment type, location, market trends, or other relevant factors."
        )
        
        # Prepare messages to send to GPT, including system instruction for follow-up questions
        if isinstance(summarized_messages, list):
            # If messages are not summarized yet, send the recent ones
            conversation_to_send = [{"role": "system", "content": system_instruction}] + summarized_messages + [{"role": "user", "content": prompt}]
        else:
            # If messages are summarized, send the summarized version and the latest prompt
            conversation_to_send = [{"role": "system", "content": system_instruction}] + [{"role": "user", "content": summarized_messages}] + [{"role": "user", "content": prompt}]

        # Get the assistant's response (Investment Analyzer)
        response = client.chat.completions.create(
            model=st.session_state["openai_model"],
            messages=conversation_to_send
        )

        # Display assistant response in chat message container
        with st.chat_message("assistant"):
            st.markdown(response['choices'][0]['message']['content'])

        # Add assistant response to chat history
        st.session_state.messages.append({"role": "assistant", "content": response['choices'][0]['message']['content']})

        # Store chat history to db.json
        db['chat_history'] = st.session_state.messages
        with open(DB_FILE, 'w') as file:
            json.dump(db, file)

    # Add a "New Chat" button to the sidebar
    if st.sidebar.button('New Chat'):
        # Clear chat history and create a new session
        db['chat_history'] = []
        with open(DB_FILE, 'w') as file:
            json.dump(db, file)
        st.session_state.messages = []
        st.session_state["openai_model"] = models[0]  # Reset to default model
        st.session_state["openai_api_key"] = None  # Reset the API key if needed
        st.rerun()

    # Add a "Clear Chat" button to the sidebar
    if st.sidebar.button('Clear Chat'):
        # Clear chat history in db.json
        db['chat_history'] = []
        with open(DB_FILE, 'w') as file:
            json.dump(db, file)
        # Clear chat messages in session state
        st.session_state.messages = []
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
                    'chat_history': []
                }
                json.dump(db, file)
        # load the database
        else:
            with open(DB_FILE, 'r') as file:
                db = json.load(file)

        # display the selectbox from db['openai_api_keys']
        selected_key = st.selectbox(
            label = "Existing OpenAI API Keys", 
            options = db['openai_api_keys']
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
