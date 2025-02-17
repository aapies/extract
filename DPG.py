import os
import time
import streamlit as st
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup

# ✅ Manually Install & Set Up Chromium & ChromeDriver in Streamlit Cloud
@st.cache_resource
def setup_chrome():
    chrome_bin = "/usr/bin/chromium-browser"
    chromedriver_bin = "/usr/bin/chromedriver"

    # ✅ Ensure ChromeDriver is correctly installed
    if not os.path.exists(chromedriver_bin):
        os.system("wget -q https://chromedriver.storage.googleapis.com/114.0.5735.90/chromedriver_linux64.zip")
        os.system("unzip chromedriver_linux64.zip")
        os.system("chmod +x chromedriver")
        os.system("mv chromedriver /usr/bin/chromedriver")
        os.system("rm chromedriver_linux64.zip")

    return chrome_bin, chromedriver_bin

# 🚀 Ensure Chrome & ChromeDriver are set up
chrome_path, chromedriver_path = setup_chrome()

# ✅ Function to extract title & introduction using Headless Chromium
def extract_title_and_introduction_selenium(url):
    try:
        # ✅ Set up Selenium with Chromium in headless mode
        chrome_options = Options()
        chrome_options.add_argument("--headless")  # Run in headless mode
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--window-size=1920x1080")
        chrome_options.binary_location = chrome_path  # ✅ Set Chrome binary location

        # ✅ Initialize WebDriver
        service = Service(chromedriver_path)
        driver = webdriver.Chrome(service=service, options=chrome_options)

        # ✅ Open the website
        driver.get(url)
        time.sleep(3)  # Allow page load

        # ✅ Extract title & introduction using BeautifulSoup
        soup = BeautifulSoup(driver.page_source, "html.parser")
        driver.quit()  # Close browser

        # Extract Title
        title = soup.title.text.strip() if soup.title else "Title not found"

        # Extract Introduction
        meta_description = soup.find("meta", attrs={"name": "description"})
        introduction = meta_description["content"] if meta_description else "Introduction not found."

        return title, introduction

    except Exception as e:
        return "Error", f"Error: {str(e)}"

# ✅ Streamlit UI
st.title("🔍 Web Scraper with Selenium (Headless)")

# ✅ Input field for multiple URLs (newline-separated)
urls_input = st.text_area("Enter URLs (one per line):")

# ✅ Process the URLs when user clicks "Scrape"
if st.button("🚀 Scrape"):
    urls = urls_input.strip().split("\n")  # Split input into a list of URLs
    results = []

    for url in urls:
        if url.strip():  # Ensure URL is not empty
            title, introduction = extract_title_and_introduction_selenium(url)
            results.append({"URL": url, "Title": title, "Introduction": introduction})

    # ✅ Display results in a DataFrame
    if results:
        import pandas as pd
        df_results = pd.DataFrame(results)
        st.write("### 🔹 Scraping Results:")
        st.dataframe(df_results)
    else:
        st.warning("⚠️ Please enter at least one valid URL")
