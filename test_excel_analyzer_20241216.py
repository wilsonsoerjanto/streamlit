import streamlit as st
import pandas as pd
import openai

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

def summarize_data(df):
    """Generate a summary of the uploaded data."""
    summary = {
        "Shape": df.shape,
        "Columns": df.columns.tolist(),
        "Data Types": df.dtypes.to_dict(),
        "Missing Values": df.isnull().sum().to_dict(),
    }
    return summary

def get_openai_insight(prompt):
    """Send a prompt to OpenAI and return the response."""
    try:
        response = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a data analysis assistant."},
                {"role": "user", "content": prompt},
            ],
            max_tokens=1000,
        )
        return response.choices[0].message
    except Exception as e:
        return f"Error: {e}"

# Streamlit UI
st.title("Excel Data Analyzer with OpenAI")

uploaded_file = st.file_uploader("Upload an Excel file", type=["xlsx", "xls"])

if uploaded_file:
    try:
        # Read the Excel file into a DataFrame
        df = pd.read_excel(uploaded_file)

        st.write("### Dataset Preview")
        st.dataframe(df.head(10))

        st.write("### Dataset Summary")
        summary = summarize_data(df)
        st.json(summary)

        # Allow the user to request OpenAI insights
        st.write("### OpenAI Analysis")

        prompt_type = st.selectbox(
            "Choose the type of insight you'd like:",
            ["Summary of dataset", "Find trends or patterns", "Anomaly detection", "Custom prompt"],
        )

        if prompt_type != "Custom prompt":
            prompt = (
                f"Please analyze the following dataset and provide {prompt_type.lower()} insights:\n"
                f"Columns: {', '.join(df.columns)}\n"
                f"Data Preview: {df.head(5).to_string(index=False)}\n"
            )
        else:
            custom_prompt = st.text_area(
                "Enter your custom analysis request:", placeholder="e.g., Find correlation between columns A and B."
            )
            if custom_prompt:
                prompt = (
                    f"Dataset Columns: {', '.join(df.columns)}\n"
                    f"Data Preview: {df.head(5).to_string(index=False)}\n"
                    f"Custom Request: {custom_prompt}"
                )

        if st.button("Get Insights from OpenAI"):
            st.write("### OpenAI Response")
            with st.spinner("Generating insights..."):
                insight = get_openai_insight(prompt)
                st.text(insight)

    except Exception as e:
        st.error(f"Error processing the file: {e}")
else:
    st.info("Please upload an Excel file to proceed.")
