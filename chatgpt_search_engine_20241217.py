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
def web_search(query, google_api_key, cse_id):
    search_url = 'https://www.googleapis.com/customsearch/v1'
    params = {
        'q': query,
        'key': google_api_key,
        'cx': cse_id,
    }
    response = requests.get(search_url, params=params)
    response.raise_for_status()
    search_results = response.json()
    return search_results.get('items', [])

# Function to generate response using OpenAI API
def generate_response_with_sources(user_query, google_api_key, cse_id):
    search_results = web_search(user_query, google_api_key, cse_id)
    sources = [result['link'] for result in search_results]
    search_snippets = [result['snippet'] for result in search_results]
    context = '\n'.join(search_snippets)
    prompt = f"User Query: {user_query}\n\nWeb Search Results:\n{context}\n\nAnswer:"
    response = openai.chat.completions.create(
        model='text-davinci-003',
        prompt=prompt,
        max_tokens=2000,
        temperature=0.5
    )
    answer = response.choices[0].text.strip()
    return answer, sources

# Streamlit UI
st.title('ChatGPT with Live Web Search')

# Input fields for API keys
openai_api_key = st.text_input('Enter your OpenAI API Key:', type='password')
google_api_key = st.text_input('Enter your Google API Key:', type='password')
cse_id = st.text_input('Enter your Google Custom Search Engine ID:')

# Validate API keys
if openai_api_key and google_api_key and cse_id:
    if validate_openai_api_key(openai_api_key) and validate_google_api_key(google_api_key, cse_id):
        st.success('API keys are valid. You can now use the application.')
        user_query = st.text_input('Ask a question:')
        if user_query:
            answer, sources = generate_response_with_sources(user_query, google_api_key, cse_id)
            st.write('**Answer:**')
            st.write(answer)
            st.write('**Sources:**')
            for source in sources:
                st.write(f'- {source}')
    else:
        st.error('Invalid API keys. Please check your keys and try again.')
else:
    st.warning('Please enter all API keys to proceed.')
