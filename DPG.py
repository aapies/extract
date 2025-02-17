import os
import time
import streamlit as st
from selenium import webdriver
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.firefox import GeckoDriverManager
from bs4 import BeautifulSoup
import subprocess

# ✅ Install Firefox & Geckodriver Manually (Fix for Streamlit Cloud)
@st.cache_resource
def install_firefox_and_geckodriver():
    os.system("apt-get update")
    os.system("apt-get install -y firefox-esr")
    os.system("apt-get install -y wget")
    os.system("wget https://github.com/mozilla/geckodriver/releases/latest/download/geckodriver-linux64.tar.gz")
    os.system("tar -xvzf geckodriver-linux64.tar.gz")
    os.system("chmod +x geckodriver")
    os.system("mv geckodriver /usr/local/bin/")

install_firefox_and_geckodriver()  

# Define Firefox profile path (Only needed if running locally)
# profile_path = "/Users/jo/Library/Application Support/Firefox/Profiles/g6jrmmdl.Cookieblock"

# Function to extract title and introduction using Selenium in Streamlit
def extract_title_and_introduction_selenium(url):
    try:
        # Set up Selenium with Firefox in headless mode
        firefox_options = Options()
        firefox_options.add_argument("--headless")  # Run in headless mode
        #firefox_options.set_preference("browser.privatebrowsing.autostart", True)  # Ensures private mode
        #firefox_options.set_preference("profile", profile_path)  # Load custom Firefox profile (if applicable)

        # Initialize WebDriver for Firefox
        service = Service(GeckoDriverManager().install())
        driver = webdriver.Firefox(service=service, options=firefox_options)

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
st.title("Selenium Web Scraper (Headless) - Streamlit Cloud Ready")

url = st.text_input("Enter URL to scrape")

if st.button("Scrape"):
    if url:
        title, introduction = extract_title_and_introduction_selenium(url)
        st.subheader("Extracted Title:")
        st.write(title)
        st.subheader("Extracted Introduction:")
        st.write(introduction)
    else:
        st.warning("Please enter a valid URL")
