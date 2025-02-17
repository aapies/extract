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

# ✅ Cache WebDriver instance for better performance
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

# ✅ Function to process "volkskrant" URLs via removepaywall.com
def process_volkskrant_url(url):
    try:
        driver = get_driver()
        full_url = f"https://www.removepaywall.com/search?url={url}"  # Modify URL for removepaywall

        # Step 1: Get archive link
        driver.get(full_url)
        sleep(3)  # Allow page load

        # Locate the iframe and extract its src attribute
        try:
            iframe = driver.find_element(By.TAG_NAME, "iframe")
            archive_url = iframe.get_attribute("src")
        except:
            return "No iframe found", "No iframe found"

        # Step 2: Extract title & intro from the archive page
        driver.get(archive_url)
        sleep(3)  # Allow page load
        html = driver.page_source

        # ✅ Extract Introduction
        section_match = re.search(r'<section.*?>(.*?)</section>', html, re.DOTALL)
        if section_match:
            section_content = section_match.group(1)
            div_match = re.search(r'<div.*?>(.*?)</div>', section_content, re.DOTALL)
            introduction = re.sub(r'<.*?>', '', div_match.group(1)).strip() if div_match else "No introduction found"
        else:
            introduction = "No content section found"

        # ✅ Extract Title
        title_match = re.search(r'<h1.*?>(.*?)</h1>', html, re.DOTALL)
        title = re.sub(r'<.*?>', '', title_match.group(1)).strip() if title_match else "No title found"

        return title, introduction

    except Exception as e:
        return "Error", f"Error: {str(e)}"

# ✅ Function to extract title and introduction normally
def extract_title_and_introduction_selenium(url):
    try:
        driver = get_driver()  
        driver.get(url)
        sleep(3)  # Allow page load

        # ✅ Extract the page source
        soup = BeautifulSoup(driver.page_source, "html.parser")

        # ✅ Extract Title
        title = soup.title.text.strip() if soup.title else "Title not found"

        # ✅ Extract Introduction (fallback to first paragraph if needed)
        meta_description = soup.find("meta", attrs={"name": "description"})
        if meta_description and "content" in meta_description.attrs:
            introduction = meta_description["content"]
        else:
            title_tag = soup.find(["h1", "h2", "h3"])
            first_paragraph = title_tag.find_next("p").text.strip() if title_tag and title_tag.find_next("p") else "First paragraph not found."
            introduction = first_paragraph

        return title, introduction

    except Exception as e:
        return "Error", f"Error: {str(e)}"

# ✅ Streamlit UI
st.title("🔍 Selenium Web Scraper (Chromium) - Streamlit Cloud Ready")

url = st.text_input("Enter URL to scrape")

if st.button("Scrape"):
    if url:
        if "volkskrant" in url.lower():
            title, introduction = process_volkskrant_url(url)
        else:
            title, introduction = extract_title_and_introduction_selenium(url)

        # ✅ Display results
        st.subheader("Extracted Title:")
        st.write(title)
        st.subheader("Extracted Introduction:")
        st.write(introduction)
    else:
        st.warning("⚠️ Please enter a valid URL")
