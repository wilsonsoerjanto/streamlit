import streamlit as st
import pandas as pd
import openai
import ssl
# ssl._create_default_https_context = ssl._create_unverified_context
# App Title
st.title("Excel File Analyzer with OpenAI")
# Input OpenAI API Key
st.sidebar.subheader("OpenAI API Key")
api_key = st.sidebar.text_input("Enter your OpenAI API key", type="password")
@st.cache_data
def validate_api_key(key):
    """
    Validate the OpenAI API key by making a simple test request.
    """
    try:
        openai.api_key = key
        # Test request: fetch OpenAI models list
        openai.models.list()
        return True, "API key is valid."
    except openai.AuthenticationError:
        return False, "Invalid API key. Please check and try again."
    except Exception as e:
        return False, f"Error validating API key: {e}"
if api_key:
    with st.spinner("Validating API key..."):
        is_valid, message = validate_api_key(api_key)
    if is_valid:
        st.sidebar.success(message)
    else:
        st.sidebar.error(message)
# File Upload
uploaded_file = st.file_uploader("Upload your Excel file", type=["xlsx", "xls"])
@st.cache_data
def load_excel(file, sheet_name):
    return pd.read_excel(file, sheet_name=sheet_name)
if uploaded_file:
    # Read the Excel file into a DataFrame
    try:
        excel_data = pd.ExcelFile(uploaded_file)
        sheet_names = excel_data.sheet_names
        # Let the user pick a sheet
        sheet_name = st.selectbox("Select a sheet to read", sheet_names)
        # Load the selected sheet
        if sheet_name:
            df = load_excel(uploaded_file, sheet_name=sheet_name)
            st.success(f"Sheet '{sheet_name}' loaded successfully!")
        
            # Display the first few rows of the DataFrame
            st.subheader("Data Preview")
            st.write(df.head())
        
            # Option to download uploaded content as CSV
            csv = df.to_csv(index=False)
            st.download_button(
                label="Download as CSV",
                data=csv,
                file_name='uploaded_file.csv',
                mime='text/csv',
            )
            # User input question for OpenAI
            if api_key:
                st.subheader("Feel free to ask a question about the data")
                user_question = st.text_input("Your Question")
                if user_question:
                    # Convert DataFrame to JSON
                    table_json = df.to_dict(orient="records")
                    # OpenAI query
                    with st.spinner("Analyzing your question..."):
                        try:
                            response = openai.ChatCompletion.create(
                                model="gpt-3.5-turbo",  # Or use "gpt-4" if available
                                messages=[
                                    {"role": "system", "content": "You are a data analysis assistant."},
                                    {"role": "user", "content": f"Here is a table in JSON format:\n{table_json}\n\nQuestion: {user_question}"}
                                ]
                            )
                            # Display the response
                            st.subheader("OpenAI Response")
                            st.write(response['choices'][0]['message']['content'])
                        except Exception as e:
                            st.error(f"Error communicating with OpenAI: {e}")
            elif not is_valid:
                st.warning("Please enter a valid OpenAI API key to enable question analysis.")    
    except Exception as e:
        st.error(f"Error reading file: {e}")
else:
    st.info("Awaiting file upload.")