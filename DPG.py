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

# ✅ Manually set up Chrome & ChromeDriver in Streamlit Cloud
@st.cache_resource
def setup_chromedriver():
    chrome_bin = "/usr/bin/chromium-browser"
    chromedriver_bin = "/usr/bin/chromedriver"

    # ✅ Install correct ChromeDriver version if not present
    if not os.path.exists(chromedriver_bin):
        os.system("wget -q https://chromedriver.storage.googleapis.com/114.0.5735.90/chromedriver_linux64.zip")
        os.system("unzip chromedriver_linux64.zip")
        os.system("chmod +x chromedriver")
        os.system("mv chromedriver /usr/bin/chromedriver")
        os.system("rm chromedriver_linux64.zip")

    return chrome_bin, chromedriver_bin

# 🚀 Ensure the correct Chrome & ChromeDriver are set up
chrome_path, chromedriver_path = setup_chromedriver()

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

        # ✅ Step 1: Locate the Shadow DOM host element
        try:
            shadow_host = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, "pg-host-shadow-root"))
            )
            st.success("✅ Shadow DOM host found!")

            # ✅ Step 2: Access the Shadow Root
            shadow_root = driver.execute_script("return arguments[0].shadowRoot", shadow_host)

            # ✅ Step 3: Find the "Akkoord" button inside the Shadow DOM
            accept_button = WebDriverWait(shadow_root, 10).until(
                EC.element_to_be_clickable((By.ID, "pg-accept-btn"))
            )

            # ✅ Step 4: Click the button
            try:
                accept_button.click()
                st.success("✅ Clicked 'Akkoord' button with Selenium!")
            except:
                driver.execute_script("arguments[0].click();", accept_button)
                st.success("✅ Clicked 'Akkoord' button using JavaScript!")

            time.sleep(3)  # Allow page reload

        except Exception as e:
            st.warning(f"❌ Could not find or click 'Akkoord' button: {e}")

        # Extract the page source after accepting cookies
        html_content = driver.page_source
        driver.quit()  # Close the browser

        # Parse HTML with BeautifulSoup
        soup = BeautifulSoup(html_content, "html.parser")

        # Extract Title
        title = soup.title.text.strip() if soup.title else "Title not found"

        # Extract Introduction from <meta name="description">
        meta_description = soup.find("meta", attrs={"name": "description"})
        if meta_description and "content" in meta_description.attrs:
            introduction = meta_description["content"]
        else:
            # Fallback: Extract first <p> after the main title header
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
