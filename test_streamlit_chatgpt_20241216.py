import streamlit as st
from openai import OpenAI
import json
import os

DB_FILE = 'db.json'

# Default prompt that cannot be adjusted by the user
DEFAULT_PROMPT = (
    "You are an investment analyzer. Always provide insightful analyses for investments, "
    "ask relevant follow-up questions, and summarize information concisely."
    "Your goal is to guide the user through the investment evaluation process, providing insights and asking for more information where necessary to provide a thorough analysis."
    "For example, if the user asks about a potential investment, you should ask questions about the investment type, location, market trends, or other relevant factors."
    "Always provide strong reasoning to your answers (for example, support your answers with SWOT analysis using the most recent data. This is only an example, do not limit yourself to only SWOT analysis. Use strong reasonings)."
)

def summarize_chat(client, chat_history):
    """Summarize the chat history using the OpenAI API."""
    summary_prompt = (
        "Summarize the following conversation in a concise and clear format, "
        "retaining the key points discussed and any actionable insights:\n\n"
    )
    full_conversation = "\n".join([f"{m['role'].capitalize()}: {m['content']}" for m in chat_history])
    messages = [{"role": "system", "content": "You are a helpful chat summarizer."},
                {"role": "user", "content": summary_prompt + full_conversation}]

    response = client.chat.completions.create(
        model="gpt-3.5-turbo",  # Use a smaller model for summaries
        messages=messages,
        temperature=0.3
    )
    return response.choices[0].message.content.strip()

def main():
    client = OpenAI(api_key=st.session_state.openai_api_key)

    # List of models
    models = ["gpt-4o-mini", "gpt-4o", "gpt-4-turbo", "gpt-4", "gpt-3.5-turbo"]

    # Sidebar: Select model
    st.session_state["openai_model"] = st.sidebar.selectbox("Select OpenAI model", models, index=0)

    # Load or initialize db.json
    if not os.path.exists(DB_FILE):
        with open(DB_FILE, 'w') as file:
            json.dump({"chat_sessions": {}}, file)
    with open(DB_FILE, 'r') as file:
        db = json.load(file)

    # Initialize sessions
    if 'chat_sessions' not in db:
        db['chat_sessions'] = {}
    if 'active_session' not in st.session_state:
        st.session_state['active_session'] = 0

    # Sidebar: Select or create a new session
    session_names = list(db['chat_sessions'].keys())
    selected_session = st.sidebar.selectbox("Select Chat Session", session_names + ["New Chat"],
                                            index=st.session_state['active_session'])

    # Handle creating a new chat session
    if selected_session == "New Chat":
        new_session_id = f"Session {len(db['chat_sessions']) + 1}"
        db['chat_sessions'][new_session_id] = {"messages": [], "summary": ""}
        st.session_state['active_session'] = len(db['chat_sessions'])
        selected_session = new_session_id
        with open(DB_FILE, 'w') as file:
            json.dump(db, file)
        st.rerun()

    # Rename session
    if selected_session != "New Chat":
        new_session_name = st.text_input("Rename Chat Session", value=selected_session, max_chars=50)
        if new_session_name and new_session_name != selected_session:
            # Ensure the new name doesn't already exist
            if new_session_name not in db['chat_sessions']:
                db['chat_sessions'][new_session_name] = db['chat_sessions'].pop(selected_session)
                selected_session = new_session_name
                st.session_state['active_session'] = session_names.index(selected_session)
                with open(DB_FILE, 'w') as file:
                    json.dump(db, file)
                st.success("Session renamed successfully.")
                st.rerun()
            else:
                st.error("A session with this name already exists. Please choose a different name.")

    # Safely fetch the active session, validate its structure
    active_session = db['chat_sessions'].get(selected_session, {"messages": [], "summary": ""})
    if not isinstance(active_session, dict):
        db['chat_sessions'][selected_session] = {"messages": [], "summary": ""}
        active_session = db['chat_sessions'][selected_session]

    chat_history = active_session["messages"]
    summary = active_session["summary"]

    # Display chat (excluding the system prompt)
    for message in chat_history:
        if message["role"] != "system":
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

    # Input box
    if prompt := st.chat_input("Please ask a question:"):
        # Add user message
        chat_history.append({"role": "user", "content": prompt})

        # Create API context: System prompt, Summary, Recent input
        api_messages = [{"role": "system", "content": DEFAULT_PROMPT}]
        if summary:
            api_messages.append({"role": "system", "content": f"Summary of previous conversation: {summary}"})
        api_messages += [{"role": m["role"], "content": m["content"]} for m in chat_history[-2:]]

        # Generate assistant response
        with st.chat_message("assistant"):
            stream = client.chat.completions.create(
                model=st.session_state["openai_model"],
                messages=api_messages,
                stream=True,
            )
            response = ""
            for chunk in stream:
                st.markdown(chunk["choices"][0]["delta"]["content"], unsafe_allow_html=True)
                response += chunk["choices"][0]["delta"]["content"]

        # Add assistant message
        chat_history.append({"role": "assistant", "content": response})

        # Summarize chat if it exceeds a certain length
        if len(chat_history) > 5:  # Adjust threshold as needed
            summary = summarize_chat(client, chat_history)
            active_session["summary"] = summary
            st.sidebar.info("Chat summarized to optimize input tokens.")

        # Save to db
        active_session["messages"] = chat_history
        db['chat_sessions'][selected_session] = active_session
        with open(DB_FILE, 'w') as file:
            json.dump(db, file)

        st.rerun()

    # Clear Chat Button
    if st.sidebar.button("Clear Chat"):
        active_session["messages"] = []
        active_session["summary"] = ""
        with open(DB_FILE, 'w') as file:
            json.dump(db, file)
        st.rerun()

if __name__ == '__main__':
    if 'openai_api_key' in st.session_state and st.session_state.openai_api_key:
        main()
    else:
        st.error("API key not found. Please reload and enter your OpenAI API key.")
