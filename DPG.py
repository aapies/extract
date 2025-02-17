import os
import time
import streamlit as st
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup

# ✅ Manually install Chrome & ChromeDriver
@st.cache_resource
def setup_chrome():
    chrome_bin = "/usr/bin/chromium-browser"
    chromedriver_bin = "/usr/bin/chromedriver"

    # ✅ Download ChromeDriver if missing
    if not os.path.exists(chromedriver_bin):
        os.system("wget -q https://chromedriver.storage.googleapis.com/114.0.5735.90/chromedriver_linux64.zip")
        os.system("unzip chromedriver_linux64.zip")
        os.system("chmod +x chromedriver")
        os.system("mv chromedriver /usr/bin/chromedriver")
        os.system("rm chromedriver_linux64.zip")

    return chrome_bin, chromedriver_bin

# 🚀 Ensure the correct Chrome & ChromeDriver are set up
chrome_path, chromedriver_path = setup_chrome()

# ✅ Function to extract title and introduction using Headless Chrome in Streamlit
def extract_title_and_introduction_selenium(url):
    try:
        # Set up Selenium with Chromium in headless mode
        chrome_options = Options()
        chrome_options.add_argument("--headless")  # Run in headless mode
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--window-size=1920x1080")  # Prevent viewport issues
        chrome_options.binary_location = chrome_path  # ✅ Set Chrome binary location

        # ✅ Initialize WebDriver with the correct ChromeDriver path
        service = Service(chromedriver_path)
        driver = webdriver.Chrome(service=service, options=chrome_options)

        # Open the website
        driver.get(url)
        time.sleep(3)  # Allow initial page load

        # ✅ Extract title & introduction
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

# ✅ Input box for the URL
url = st.text_input("🔗 Website URL", "")

# ✅ Add a Scrape Button
if st.button("🚀 Scrape"):
    if url.strip():  # Ensure URL is not empty
        title, introduction = extract_title_and_introduction_selenium(url)
        
        # ✅ Display results
        st.subheader("📌 Extracted Title:")
        st.write(title)

        st.subheader("📌 Extracted Introduction:")
        st.write(introduction)
    else:
        st.warning("⚠️ Please enter a valid URL")
