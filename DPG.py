import streamlit as st
import re
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.core.os_manager import ChromeType
from bs4 import BeautifulSoup
from time import sleep
import pandas as pd

# ✅ Caching WebDriver instance for performance
@st.cache_resource
def get_driver():
    options = Options()
    options.add_argument("--disable-gpu")
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")  # Helps with memory issues

    service = Service(ChromeDriverManager(chrome_type=ChromeType.CHROMIUM).install())
    driver = webdriver.Chrome(service=service, options=options)
    return driver

# ✅ Function to extract title and introduction (can handle both DataFrame rows & single URLs)
def process_row(row_or_url):
    """
    Extracts title and introduction.
    - If given a dictionary (row from DataFrame), processes based on "Publisher" and "Link".
    - If given a direct URL (string), processes the single URL.
    """

    # Determine if input is a row (dict) or direct URL (string)
    if isinstance(row_or_url, dict):
        # Processing a row from DataFrame
        if "volkskrant" not in row_or_url["Publisher"].lower():
            return row_or_url  # Skip rows that don't match the condition
        url = row_or_url["Link"]
    else:
        # Processing a direct URL input (string)
        url = row_or_url

    driver = get_driver()  # ✅ Use Chromium WebDriver

    try:
        # Construct the link with removepaywall prefix
        full_url = f"https://www.removepaywall.com/search?url={url}"
        
        # Step 1: Get the archive link
        driver.get(full_url)
        driver.implicitly_wait(10)  # Wait up to 10 seconds for elements to load
        
        # Locate the iframe and extract its src attribute
        try:
            iframe = driver.find_element(By.TAG_NAME, "iframe")
            archive_url = iframe.get_attribute("src")
        except:
            if isinstance(row_or_url, dict):
                row_or_url["title sel"] = "No iframe found"
                row_or_url["intro sel"] = "No iframe found"
                return row_or_url
            return "No iframe found", "No iframe found"

        # Step 2: Extract the title and introduction from the archive page
        driver.get(archive_url)
        driver.implicitly_wait(10)  # Wait for the page to load
        
        # Get the full HTML source
        html = driver.page_source
        
        # Find the section containing the introduction using raw HTML
        section_match = re.search(r'<section.*?>(.*?)</section>', html, re.DOTALL)
        if section_match:
            section_content = section_match.group(1)
            
            # Stop at the first </div> and extract text
            div_match = re.search(r'<div.*?>(.*?)</div>', section_content, re.DOTALL)
            if div_match:
                raw_intro_html = div_match.group(1)  # Raw HTML of the first <div>
                introduction = re.sub(r'<.*?>', '', raw_intro_html).strip()  # Strip any remaining HTML tags
            else:
                introduction = "No introduction found"
        else:
            introduction = "No content section found"
        
        # Extract the title
        title_match = re.search(r'<h1.*?>(.*?)</h1>', html, re.DOTALL)
        title = re.sub(r'<.*?>', '', title_match.group(1)).strip() if title_match else "No title found"
        
        # Update the row if processing a DataFrame
        if isinstance(row_or_url, dict):
            row_or_url["title sel"] = title
            row_or_url["intro sel"] = introduction
            return row_or_url
        
        return title, introduction  # Return title & intro for single URL input
    
    finally:
        driver.quit()  # ✅ Close the browser instance

# ✅ Streamlit UI
st.title("Selenium Web Scraper (Chromium) - Streamlit Cloud Ready")

url = st.text_input("Enter URL to scrape")

if st.button("Scrape"):
    if url:
        title, introduction = process_row(url)  # ✅ Now supports direct URL input
        st.subheader("Extracted Title:")
        st.write(title)
        st.subheader("Extracted Introduction:")
        st.write(introduction)
    else:
        st.warning("⚠️ Please enter a valid URL")
