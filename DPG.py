import streamlit as st
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.core.os_manager import ChromeType
from bs4 import BeautifulSoup

# ✅ Caching the WebDriver instance to prevent re-initialization
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

# ✅ Function to extract title & introduction
def extract_title_and_introduction_selenium(url):
    try:
        driver = get_driver()  # ✅ Always get the cached driver
        driver.get(url)

        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "body")))

        # ✅ Handle Cookie Banner (if exists)
        try:
            accept_button = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.ID, "pg-accept-btn"))
            )
            accept_button.click()
            st.success("✅ Clicked 'Akkoord' button to accept cookies!")
        except Exception:
            st.warning("⚠️ No cookie banner found or clickable.")

        # ✅ Extract page source
        html_content = driver.page_source

        # ✅ Parse with BeautifulSoup
        soup = BeautifulSoup(html_content, "html.parser")

        # ✅ Extract Title
        title = soup.title.text.strip() if soup.title else "Title not found"

        # ✅ Extract Introduction
        meta_description = soup.find("meta", attrs={"name": "description"})
        if meta_description and "content" in meta_description.attrs:
            introduction = meta_description["content"]
        else:
            # Fallback: Extract first <p> after a main heading
            title_tag = soup.find(["h1", "h2", "h3"])
            if title_tag:
                first_paragraph = title_tag.find_next("p")
                introduction = first_paragraph.text.strip() if first_paragraph else "First paragraph not found."
            else:
                introduction = "Introduction not found."

        return title, introduction

    except Exception as e:
        return "Error", f"Error: {str(e)}"

# ✅ Streamlit UI
st.title("Selenium Web Scraper (Chromium) - Streamlit Cloud Ready")

url = st.text_input("Enter URL to scrape")

if st.button("Scrape"):
    if url:
        title, introduction = extract_title_and_introduction_selenium(url)
        st.subheader("Extracted Title:")
        st.write(title)
        st.subheader("Extracted Introduction:")
        st.write(introduction)
    else:
        st.warning("⚠️ Please enter a valid URL")
