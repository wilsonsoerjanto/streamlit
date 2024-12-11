import streamlit as st
import pandas as pd
import ssl

ssl._create_default_https_context = ssl._create_unverified_context

# App Title
st.title("Excel File Uploader")

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
    except Exception as e:
        st.error(f"Error reading file: {e}")
else:
    st.info("Awaiting file upload.")