import streamlit as st
from openai import OpenAI
import json
import os
import pandas as pd

DB_FILE = 'db.json'

# Function to load and display file content
def load_file(file):
    if file.name.endswith('.csv'):
        return pd.read_csv(file)
    elif file.name.endswith(('.xls', '.xlsx')):
        return pd.read_excel(file)
    else:
        st.error("Unsupported file format. Please upload a CSV or Excel file.")
        return None

def main():
    client = OpenAI(api_key=st.session_state.openai_api_key)

    # List of models
    models = ["gpt-4o-mini", "gpt-4o", "gpt-4-turbo", "gpt-4", "gpt-3.5-turbo"]

    # Sidebar
    st.session_state["openai_model"] = st.sidebar.selectbox("Select OpenAI model", models, index=0)
    if st.sidebar.button('Clear Chat'):
        db['chat_history'] = []
        with open(DB_FILE, 'w') as file:
            json.dump(db, file)
        st.session_state.messages = []
        st.rerun()

    # Load chat history from db.json
    with open(DB_FILE, 'r') as file:
        db = json.load(file)
    st.session_state.messages = db.get('chat_history', [])

    # Display chat messages from history on app rerun
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # File upload section
    uploaded_file = st.file_uploader("Upload your CSV or Excel file for analysis", type=["csv", "xls", "xlsx"])
    if uploaded_file:
        data = load_file(uploaded_file)
        if data is not None:
            st.write("**Preview of the uploaded file:**")
            st.dataframe(data)

            # Ask user for columns to analyze
            selected_columns = st.multiselect("Select columns to analyze", options=data.columns.tolist())
            if selected_columns:
                st.write("**Selected data for analysis:**")
                filtered_data = data[selected_columns]
                st.dataframe(filtered_data)

                # User prompt for specific questions about the data
                data_prompt = st.text_area("Ask a question or describe the analysis you want:")
                if st.button("Analyze Data"):
                    st.session_state.messages.append({"role": "user", "content": f"Analyze the following data: {filtered_data.to_dict()}\n{data_prompt}"})
                    with st.chat_message("user"):
                        st.markdown(f"Analyze the following data: {filtered_data.to_dict()}\n{data_prompt}")

                    with st.chat_message("assistant"):
                        stream = client.chat.completions.create(
                            model=st.session_state["openai_model"],
                            messages=[
                                {"role": m["role"], "content": m["content"]}
                                for m in st.session_state.messages
                            ],
                            stream=True,
                        )
                        response = st.write_stream(stream)
                    st.session_state.messages.append({"role": "assistant", "content": response})

                    # Store chat history to db.json
                    db['chat_history'] = st.session_state.messages
                    with open(DB_FILE, 'w') as file:
                        json.dump(db, file)

    # Chat interface
    if prompt := st.chat_input("What is up?"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            stream = client.chat.completions.create(
                model=st.session_state["openai_model"],
                messages=[
                    {"role": m["role"], "content": m["content"]}
                    for m in st.session_state.messages
                ],
                stream=True,
            )
            response = st.write_stream(stream)
        st.session_state.messages.append({"role": "assistant", "content": response})

        # Store chat history to db.json
        db['chat_history'] = st.session_state.messages
        with open(DB_FILE, 'w') as file:
            json.dump(db, file)

if __name__ == '__main__':
    if 'openai_api_key' in st.session_state and st.session_state.openai_api_key:
        main()
    else:
        if not os.path.exists(DB_FILE):
            with open(DB_FILE, 'w') as file:
                db = {
                    'openai_api_keys': [],
                    'chat_history': []
                }
                json.dump(db, file)
        else:
            with open(DB_FILE, 'r') as file:
                db = json.load(file)

        selected_key = st.selectbox("Existing OpenAI API Keys", options=db['openai_api_keys'])
        new_key = st.text_input("New OpenAI API Key", type="password")

        if st.button("Login"):
            if new_key:
                db['openai_api_keys'].append(new_key)
                with open(DB_FILE, 'w') as file:
                    json.dump(db, file)
                st.success("Key saved successfully.")
                st.session_state['openai_api_key'] = new_key
                st.rerun()
            elif selected_key:
                st.success(f"Logged in with key '{selected_key}'")
                st.session_state['openai_api_key'] = selected_key
                st.rerun()
            else:
                st.error("API Key is required to login.")
