import streamlit as st
import pandas as pd
import concurrent.futures  # Import concurrent.futures for parallel processing
from selenium import webdriver
from bs4 import BeautifulSoup
import base64

# Function to get seller names and availability for a single ASIN
def get_seller_name_and_availability(asin):
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    driver = webdriver.Chrome(options=options)

    product_url = f"https://www.amazon.it/dp/{asin}"
    driver.get(product_url)

    html = driver.page_source
    soup = BeautifulSoup(html, 'html.parser')

    seller_element = soup.find('a', {'id': 'sellerProfileTriggerId'})
    availability_div = soup.find('div', {'id': 'availability'})

    if availability_div is not None:
        if "Non in stock" in availability_div.get_text():
            availability_status = "Not Available"
            seller_name = "none"
        else:
            availability_status = "Available"
            if seller_element is not None:
                seller_name = seller_element.get_text(strip=True)
            else:
                seller_name = "Amazon"
    else:
        availability_status = "Product page not found"
        seller_name = "none"

    driver.quit()

    return [asin, seller_name, availability_status]

st.title("Amazon Scraper")

# File Upload
st.sidebar.header("Upload Input CSV")
uploaded_file = st.sidebar.file_uploader("Upload your input CSV file", type=["csv"])

# Check if a file has been uploaded
if uploaded_file is not None:
    # Display the uploaded file
    st.sidebar.write("Uploaded CSV File")
    #st.sidebar.write(uploaded_file)

    # Run the scraping process when the user clicks the button
    if st.sidebar.button("Run Scraper"):
        # Read ASINs from the uploaded CSV
        df = pd.read_csv(uploaded_file)
        asins = df['ASIN'].tolist()

        # Run your scraping script with parallel processing
        seller_data = []
        with concurrent.futures.ThreadPoolExecutor() as executor:
            results = executor.map(get_seller_name_and_availability, asins)
            seller_data.extend(results)

        # Create a DataFrame from the scraped data
        result_df = pd.DataFrame(seller_data, columns=['ASIN', 'Seller Name', 'Availability'])

        # Display the result DataFrame
        st.write("Scraped Data:")
        st.write(result_df)

       
        # Provide a download link for the result CSV
        csv_data = result_df.to_csv(index=False).encode()
        b64 = base64.b64encode(csv_data).decode('utf-8')
        href = f'<a href="data:file/csv;base64,{b64}" download="processed_data.csv">Download Processed CSV</a>'
        st.markdown(href, unsafe_allow_html=True)
        