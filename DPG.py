import streamlit as st
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.core.os_manager import ChromeType
from bs4 import BeautifulSoup
from time import sleep

# ✅ Caching WebDriver instance for better performance
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

# ✅ Function to extract title and introduction (without cookie handling)
def extract_title_and_introduction_selenium(url):
    try:
        driver = get_driver()  # ✅ Use the cached driver
        driver.get(url)
        sleep(3)  # Allow time for content to load

        # ✅ Extract the page source
        html_content = driver.page_source

        # ✅ Parse with BeautifulSoup
        soup = BeautifulSoup(html_content, "html.parser")

        # ✅ Extract Title
        title = soup.title.text.strip() if soup.title else "Title not found"

        # ✅ Extract Introduction (with fallback mechanism)
        meta_description = soup.find("meta", attrs={"name": "description"})
        if meta_description and "content" in meta_description.attrs:
            meta_content = meta_description["content"]
            # If meta content ends with "...", check if a longer fallback exists
            if meta_content.endswith("..."):
                title_tag = soup.find(["h1", "h2", "h3"])  # Look for header tags
                if title_tag:
                    first_paragraph = title_tag.find_next("p")
                    fallback_content = first_paragraph.text.strip() if first_paragraph else ""
                    introduction = fallback_content if len(fallback_content) > len(meta_content) else meta_content
                else:
                    introduction = meta_content
            else:
                introduction = meta_content
        else:
            # Fall back to extracting the first <p> after the title header
            title_tag = soup.find(["h1", "h2", "h3"])  # Look for header tags
            if title_tag:
                # Find the first <p> after the title
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
