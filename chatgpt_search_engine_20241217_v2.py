import openai
import requests
import streamlit as st

# Function to validate OpenAI API key
def validate_openai_api_key(api_key):
    try:
        openai.api_key = api_key
        # Perform a simple API call to validate the key
        openai.models.list()
        return True
    except openai.AuthenticationError:
        return False

# Function to validate Google API key
def validate_google_api_key(api_key, cse_id):
    search_url = 'https://www.googleapis.com/customsearch/v1'
    params = {
        'q': 'test',
        'key': api_key,
        'cx': cse_id,
    }
    response = requests.get(search_url, params=params)
    return response.status_code == 200

# Function to perform web search using Google Custom Search API
def web_search(query, google_api_key, cse_id, excluded_domains=None):
    search_url = 'https://www.googleapis.com/customsearch/v1'
    params = {
        'q': query,
        'key': google_api_key,
        'cx': cse_id,
    }
    response = requests.get(search_url, params=params)
    response.raise_for_status()
    search_results = response.json()

    # Ensure 'items' exists in the response
    if 'items' not in search_results:
        return []  # Return an empty list if no results found
    
    # Extract and filter results
    filtered_results = []
    for result in search_results['items']:
        if 'link' in result:
            if excluded_domains and any(domain in result['link'] for domain in excluded_domains):
                continue
            filtered_results.append(result)
    
    return filtered_results

# Function to generate response using OpenAI API
def generate_response_with_sources(messages, google_api_key, cse_id):
    excluded_domains = ["reddit.com"]
    user_query = messages[-1]["content"]
    search_results = web_search(user_query, google_api_key, cse_id, excluded_domains)
    sources = [result['link'] for result in search_results]
    search_snippets = [result['snippet'] for result in search_results]
    context = '\n'.join(search_snippets)

    # Add search context to the conversation
    messages.append(
        {"role": "system", "content": f"Web Search Results:\n{context}"}
    )
    response = openai.chat.completions.create(
        model='gpt-4o-mini',  # Update to 'gpt-3.5-turbo' or another model you're using
        messages=messages,
        max_tokens=4000,
        temperature=0.2
    )
    answer = response.choices[0].message.content
    messages.append({"role": "assistant", "content": answer})
    return answer, sources

# Streamlit UI
st.set_page_config(page_title="ChatGPT with Live Web Search", layout="wide")
st.title('ChatGPT with Live Web Search')

# Input fields for API keys
openai_api_key = st.text_input('Enter your OpenAI API Key:', type='password')
google_api_key = st.text_input('Enter your Google API Key:', type='password')
cse_id = st.text_input('Enter your Google Custom Search Engine ID:')

# Initialize session state for conversation history
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "system", "content": "You are an investment analyzer, and after giving out answer, you should always offer the user options for next action items (for example, 'Would you like me to ...?') to encourage deeper analysis based on the user's responses."
                                         "Your goal is to guide the user through the investment evaluation process, providing insights and asking for more information where necessary to provide a thorough analysis."
                                         "For example, if the user asks about a potential investment, you should ask questions about the investment type, location, market trends, or other relevant factors."
                                         "Always consider the most recent information when conducting your analysis, as we would like your information and reasonings to be as relevant as possible."
                                         "DO NOT MAKE UP INFORMATION"
        },
    ]

# Validate API keys
if openai_api_key and google_api_key and cse_id:
    if validate_openai_api_key(openai_api_key) and validate_google_api_key(google_api_key, cse_id):
        st.success('API keys are valid. You can now use the application.')

        # Chat history display
        st.markdown("### Chat")
        chat_placeholder = st.container()
        with chat_placeholder:
            for message in st.session_state.messages:
                if message["role"] == "user":
                    st.markdown(
                        f'<div style="text-align: right; background-color: #DCF8C6; border-radius: 10px; padding: 10px; margin: 5px;">'
                        f"{message['content']}</div>",
                        unsafe_allow_html=True,
                    )
                elif message["role"] == "assistant":
                    st.markdown(
                        f'<div style="text-align: left; background-color: #E8E8E8; border-radius: 10px; padding: 10px; margin: 5px;">'
                        f"{message['content']}</div>",
                        unsafe_allow_html=True,
                    )

        # Input box and send button
        user_query = st.text_input("Your message:", key="user_input")
        if st.button("Send"):
            if user_query:
                # Add user message to conversation
                st.session_state.messages.append({"role": "user", "content": user_query})
                # Generate response
                answer, sources = generate_response_with_sources(
                    st.session_state.messages, google_api_key, cse_id
                )
                # Display sources
                with chat_placeholder:
                    for source in sources:
                        st.markdown(f"- [Source]({source})")
    else:
        st.error('Invalid API keys. Please check your keys and try again.')
else:
    st.warning('Please enter all API keys to proceed.')
