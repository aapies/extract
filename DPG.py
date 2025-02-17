import streamlit as st
from selenium import webdriver
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

# ✅ Function to extract title & introduction
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

        # ✅ Extract Introduction (fallback to first paragraph if needed)
        meta_description = soup.find("meta", attrs={"name": "description"})
        if meta_description and "content" in meta_description.attrs:
            introduction = meta_description["content"]
        else:
            title_tag = soup.find(["h1", "h2", "h3"])  # Look for headers
            if title_tag:
                first_paragraph = title_tag.find_next("p")
                introduction = first_paragraph.text.strip() if first_paragraph else "First paragraph not found."
            else:
                introduction = "Introduction not found."

        return title, introduction

    except Exception as e:
        return "Error", f"Error: {str(e)}"

# ✅ Streamlit UI
st.title("🔍 Bulk Selenium Web Scraper (Chromium) - Streamlit Cloud Ready")

# ✅ Input field for multiple URLs (newline-separated)
urls_input = st.text_area("Enter URLs (one per line):")

# ✅ Process URLs when user clicks "Scrape"
if st.button("🚀 Scrape"):
    urls = urls_input.strip().split("\n")  # Split input into a list of URLs

    for i, url in enumerate(urls, start=1):
        if url.strip():  # Ensure URL is not empty
            title, introduction = extract_title_and_introduction_selenium(url)

            # ✅ Display results directly in Streamlit
            st.subheader(f"🔹 Result {i}")
            st.write(f"**URL:** {url}")
            st.write(f"**Title:** {title}")
            st.write(f"**Introduction:** {introduction}")
            st.write("---")  # Separator between results
    if not urls:
        st.warning("⚠️ Please enter at least one valid URL")
