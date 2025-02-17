#!/usr/bin/env python
# coding: utf-8

# ### Imports

# In[1]:


import email
from bs4 import BeautifulSoup
import pandas as pd
import requests
import streamlit as st


# In[4]:


#!pip install openai==1.3.0


# In[2]:


pd.set_option('display.max_colwidth', None)


# ### Take Google alerts and put in dataframe

# In[93]:


from email import policy
from email.parser import BytesParser


# Streamlit UI - File Upload
st.title("Google Alerts Email Processor")
uploaded_file = st.file_uploader("Upload a Google Alerts `.eml` file", type=["eml"])

# 🔹 If no file is uploaded, stop execution
if uploaded_file is None:
    st.warning("Please upload an `.eml` file to continue.")
    st.stop()  # 🚀 This prevents any further code from running



# 🔹 Initialize email_body BEFORE checking for file upload to prevent NameError
email_body = None  

if uploaded_file is not None:
    email_message = BytesParser(policy=policy.default).parse(uploaded_file)

    # Step 2: Extract the email body
    # Check if the email has multiple parts
    if email_message.is_multipart():
        for part in email_message.iter_parts():
            # Look for the text/html part
            if part.get_content_type() == 'text/html':
                email_body = part.get_content()
                break
            elif part.get_content_type() == 'text/plain':  # Fallback to plain text
                email_body = part.get_content()
    else:
        # Single-part email
        email_body = email_message.get_content()

# Step 3: Parse the content with BeautifulSoup (only if email_body exists)
if email_body:
    soup = BeautifulSoup(email_body, 'html.parser')
    st.write("Nicely formatted output of the HTML content")  # Nicely formatted output of the HTML content
else:
    st.write("No content found in the email.")


# In[94]:


# Initialize a list to store extracted data
articles = []

# Locate all articles based on schema.org Article
article_blocks = soup.find_all("tr", itemscope=True, itemtype="http://schema.org/Article")

# Iterate through each article block
for block in article_blocks:
    # Extract keyword: Search upward from the current article block
    keyword_tag = block.find_previous("span", style="color:#262626;font-size:22px")
    keyword = keyword_tag.get_text(strip=True) if keyword_tag else None
    
    # Extract title and link
    title_tag = block.find("a", itemprop="url")
    title = title_tag.find("span", itemprop="name").get_text(strip=True) if title_tag else None
    link = title_tag['href'] if title_tag and 'href' in title_tag.attrs else None
    
    # Extract publisher
    publisher_tag = block.find_all("span", itemprop="name")
    publisher = publisher_tag[1].get_text(strip=True) if len(publisher_tag) > 1 else None

    # Extract snippet
    snippet_tag = block.find("div", itemprop="description")
    snippet = snippet_tag.get_text(strip=True) if publisher_tag else None
    # Replace non-breaking spaces (\xa0) with regular spaces
    if snippet:
        snippet = snippet.replace('\xa0', ' ')
    
    # Append extracted data to the list
    articles.append({
        "Keyword": keyword,
        "Title": title,
        "Publisher": publisher,
        "Snippet": snippet,
        "Link": link
    })

# Convert the list of articles into a pandas DataFrame
df = pd.DataFrame(articles)

# Display the DataFrame
#df['Publisher'].unique()


# #### Set up openai

# In[5]:


# from openai import OpenAI


# In[6]:
import openai
from openai import OpenAI

import subprocess
import streamlit as st

result = subprocess.run(["pip", "install", "--upgrade", "openai==1.3.0"], capture_output=True, text=True)
st.write(result.stdout)

# ✅ Load API Key from Streamlit secrets
api_key = st.secrets.get("openai_api_key")

client = OpenAI(api_key=api_key)

# #### Test openai API

# In[10]:


# completion = client.chat.completions.create(
#     model="gpt-4o-mini",
#     messages=[
#         {"role": "system", "content":'Je moet controlleren of iets een gerenomeerde nieuwmedia is of niet. Voorbeelden van gerenomeerde media zijn NRC, Trouw, Parool,  Volkskrant, Algemeen Dagblad (AD), Telegraaf, NOS, NU.nl. Dit is niveau 1. Belangrijk om te benoemen is dat dit voorbeelden zijn. Er kunnen meerdere zijn of buitenlandse kranten. Het gaat erom dat het een gerenomeerde krant is vergelijkbaar met het niveau van de genoemde voorbeelden. Gebruik hiervoor je eigen kennis ook. Één niveau lager zijn bijv. metronieuws, Regionale dagbladen die onder AD vallen zoals Tubantia, Noordhollands Dagblad, De Stentor etc, Reformatorisch Dagblad. Dit is niveau 2. Één niveau lager is de rest. Dit is niveau 3. Wanneer een nieuwsmedia gegegeven wordt, antwoord je met "niveau 1", "niveau 2" of "niveau 3", afhankelijk waarvan je denk bij welk niveau de nieuwsmedia hoort. Zeg niks anders dan het niveau en het nummer.',
# },
#         {
#             "role": "user",
#             "content": "NOS"
#         }
#     ]
# )

# completion.choices[0].message.content


# #### Prompt for mediabedrijf

# In[7]:


# In[13]:


pd.set_option('display.max_rows', None)


# In[14]:





# #### maak media niveau lower string, misschien dat ik gewoon op "1", "2" of "3" ga zoeken though

# In[15]:




# ## Haal een bruikbare link uit dataframe

# In[8]:


from urllib.parse import urlparse, parse_qs


# In[9]:


def extract_working_link(google_redirect_url):
    parsed_url = urlparse(google_redirect_url)
    query_params = parse_qs(parsed_url.query)
    return query_params.get('url', [None])[0]


# In[10]:


df.loc[:, 'Link'] = df['Link'].apply(extract_working_link)


# ### Get country code

# In[19]:


def get_country_code(website):
    # Parse the website URL
    parsed_url = urlparse(website)
    # Extract the netloc (domain) and check for '.nl' or '.be'
    domain = parsed_url.netloc
    if '.nl' in domain:
        return 'NL'
    elif '.be' in domain:
        return 'BE'
    else:
        return None  # Or some default value

# Apply the function to create a new column
df['Country'] = df['Link'].apply(get_country_code)


# In[20]:


def classify_country(country):
    try:
        # Call the model
        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": 'Bekijk of je uit de url kan afleiden of het Nederlands (NL), Beglisch Vlaams (BENL) of Belgisch Frans (BERF) is. '
                    'Output alleen "NL", "BENL", "BEFR" of "None" en niks anders.'
                    'Ouput bij Nederlands: "NL"'
                    'Output bij Vlaams Belgisch: "BENL"'
                    'Output bij Frans Belgisch: "BEFR". Als de url franstalig is dan is het altijd Frans Belgisch.'
                    'Als je het niet zeker weet, output: "None"'
                },
                {
                    "role": "user",
                    "content": f"Dit is de url: '{country}'"
                }
            ]
        )
        # Extract the classification result
        return completion.choices[0].message.content.strip()
    except Exception as e:
        # Handle any errors (e.g., API rate limits or network issues)
        st.write(f"Error processing country '{country}': {e}")
        return None


# In[21]:


df_none = df[~df['Country'].isin(["NL", "BE"])]
df.loc[df_none.index, 'Country'] = df_none['Link'].apply(classify_country)


# !!! hier nog een check of alle landen NL, BE, BEFR of BENL zijn

# # Titel en Intro van websites halen

# In[67]:


def extract_title_and_introduction(url):
    try:
        # Make a GET request to fetch the raw HTML content
        headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Gecko/20100101 Firefox/117.0"
    }
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        # Parse the HTML content
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Extract the title of the page
        title = soup.title.text.strip() if soup.title else 'Title not found'
        
        # Try to extract the introduction from the meta description
        meta_description = soup.find('meta', attrs={'name': 'description'})
        if meta_description and 'content' in meta_description.attrs:
            meta_content = meta_description['content']
            # If meta content ends with "...", ensure it has more characters than the fallback
            if meta_content.endswith('...'):
                title_tag = soup.find(['h1', 'h2', 'h3'])  # Look for header tags
                if title_tag:
                    first_paragraph = title_tag.find_next('p')
                    fallback_content = first_paragraph.text.strip() if first_paragraph else ''
                    if len(fallback_content) > len(meta_content):
                        introduction = fallback_content
                    else:
                        introduction = meta_content
                else:
                    introduction = meta_content
            else:
                introduction = meta_content
        else:
            # Fall back to extracting the first <p> after the title header
            title_tag = soup.find(['h1', 'h2', 'h3'])  # Look for header tags
            if title_tag:
                # Find the first <p> after the title
                first_paragraph = title_tag.find_next('p')  
                introduction = first_paragraph.text.strip() if first_paragraph else 'First paragraph not found.'
            else:
                introduction = 'Introduction not found.'
        
        return title, introduction
    except Exception as e:
        return 'Error', 'Error: ' + str(e)


# In[68]:


# Apply the function to the DataFrame and create new columns
df[['title_new', 'introduction_new']] = df['Link'].apply(lambda x: pd.Series(extract_title_and_introduction(x)))


# In[92]:


df.loc[[37]]


# #### Youtube check

# In[24]:


import pandas as pd
import requests
from bs4 import BeautifulSoup

# Your scrape_youtube_video function
def scrape_youtube_video(url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Gecko/20100101 Firefox/117.0"
    }
    response = requests.get(url, headers=headers)
    response.raise_for_status()  # Raise an exception for HTTP errors

    soup = BeautifulSoup(response.text, 'html.parser')

    # Extract the title
    title_tag = soup.find("meta", property="og:title")
    title = title_tag["content"] if title_tag else "Title not found"

    # Extract the description (shortDescription)
    description_tag = soup.find("script", string=lambda s: s and "shortDescription" in s)
    if description_tag:
        # Find the shortDescription text in the script content
        start = description_tag.string.find('"shortDescription":"') + len('"shortDescription":"')
        end = description_tag.string.find('",', start)
        raw_description = description_tag.string[start:end]

        # Stop at the first \n (new line character)
        first_paragraph_end = raw_description.find("\\n")
        if first_paragraph_end != -1:
            raw_description = raw_description[:first_paragraph_end]

        # Clean up escaped characters
        description = raw_description.replace('\\"', '"')
    else:
        description = "Description not found"

    # Extract the uploader
    uploader_tag = soup.find("link", itemprop="name")
    uploader = uploader_tag["content"] if uploader_tag else "Uploader not found"

    return {
        "title": title,
        "description": description,
        "uploader": uploader,
    }


# Function to process each row
def process_row(row):
    if row["Publisher"].lower() == "youtube":
        video_info = scrape_youtube_video(row["Link"])
        row["title_new"] = video_info["title"]
        row["introduction_new"] = video_info["description"]
        row["Publisher"] = video_info["uploader"]
    return row

# Apply the process_row function to each row
df = df.apply(process_row, axis=1)


# ### Check whether titel and introduction are correct

# In[69]:


def content_check(title, introduction, example_title, example_snippet):
    try:
        # Call the model
        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": (
                        'Je krijgt een titel en introductie van een artikel. Je taak is om te kijken of het op een juiste artikel en introductie lijkt. '
                        'Als het niet op een logische titel van het artikel lijkt (bijvoorbeeld: "error", "dpg media", "title not found", " " of andere niet logische titels) output dan "Fout". '
                        'De titel moet een beetje lijken op: "{example_title}" '
                        'Als het niet op een logische introductie van het artikel lijkt (bijvoorbeeld: "title not found", "auteurs", "introduction not found", "", de introductie eindigt halverwege een zin) output dan "Fout". Markdown tekens zoals /n mag het wel op eindigen.'
                        'De introductie moet een heel klein beetje lijken op: "{example_snippet}" . Het gaat dan over het onderwerp, niet over de letterlijke inleiding die hetzelfde moet zijn. '
                        "Let op: introducties kunnen ook in het Frans zijn en dus ook goed. les intros doivent être très vaguement liées, ce n'est pas grave si c'est une courte introduction, tant qu'elle ne se termine pas au milieu d'une phrase."
                        'Bij een onlogische title en introductie output je dus: "Fout, Fout". Bij een goede titel en onlogische introductie output je dus: "Goed, Fout". '
                        'Als alles goed lijkt output je: "Goed, Goed".'
                    ).format(example_title=example_title, example_snippet=example_snippet)
                },
                {
                    "role": "user",
                    "content": (
                        f"Dit is de titel: {title}. "
                        f"Dit is de introductie: {introduction}."
                    )
                }
            ]
        )
        # Extract the classification result
        return completion.choices[0].message.content.strip()
    except Exception as e:
        # Handle any errors (e.g., API rate limits or network issues)
        st.write(f"Error processing title '{title}': {e}")
        return None


# ### Apply the function

# In[70]:


df['evaluation'] = df.apply(
    lambda row: content_check(
        title=row['title_new'], 
        introduction=row['introduction_new'], 
        example_title=row['Title'], 
        example_snippet=row['Snippet']
    ), 
    axis=1
)


# In[71]:


import string

# Function to remove punctuation from a string
def remove_punctuation(text):
    return text.translate(str.maketrans('', '', string.punctuation))

# Split the 'evaluation' column and remove punctuation
df[['title check', 'intro check']] = df['evaluation'].str.split(',', expand=True)

# Remove punctuation from both new columns
df['title check'] = df['title check'].apply(remove_punctuation)
df['intro check'] = df['intro check'].apply(remove_punctuation)

# If you want to remove leading/trailing whitespace, you can use .str.strip() on both columns:
df['title check'] = df['title check'].str.strip()
df['intro check'] = df['intro check'].str.strip()

# Delete cell evaluation
df = df.drop(columns=['evaluation'])


# ### Een df_goed en df_fout aanmaken. Misschien niet handig maar laat het voor nu zo.

# In[72]:


# Filter rows matching the constraints
df_goed = df[
    (df['title check'].str.lower() == 'goed') & 
    (df['intro check'].str.lower() == 'goed')
]

# Rename specific columns to match df_goed
df_goed = df_goed.rename(columns={
    'title_new': 'title sel',
    'introduction_new': 'intro sel'
})


# In[73]:


# Create a new DataFrame where either 'title check' or 'intro check' contains "Fout"
df_fout = df[(df['title check'].str.contains('Fout', na=True)) | 
             (df['intro check'].str.contains('Fout', na=True))]


# In[30]:


### Kleine check of alles goed is
#len(df_goed), len(df_fout), len(df)


# ### Nog een paar specifieke aanpakken

# RTBF

# In[31]:


#pip install nltk


# In[32]:


import requests
from bs4 import BeautifulSoup
import json
import nltk

# Download NLTK's punkt tokenizer if not already available
nltk.download('punkt', quiet=True)

def extract_title_and_introduction_rtbf(url, min_words=25, max_words=50):
    """
    Extract the title and introduction dynamically based on semantic boundaries.

    Args:
        url (str): The URL of the page to scrape.
        min_words (int): Minimum word count for a meaningful introduction.
        max_words (int): Maximum word count for the introduction.

    Returns:
        tuple: Extracted title and introduction.
    """
    try:
        # Make a GET request to fetch the raw HTML content
        response = requests.get(url)
        response.raise_for_status()
        
        # Parse the HTML content
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Extract the title of the page
        title = soup.title.text.strip() if soup.title else 'Title not found'
        
        # Extract the introduction using JSON-LD (articleBody)
        introduction = None
        script_tags = soup.find_all('script', type='application/ld+json')
        
        for script in script_tags:
            try:
                # Parse the script content as JSON
                json_data = json.loads(script.string)
                
                # Check if `articleBody` exists
                if 'articleBody' in json_data:
                    full_text = json_data['articleBody']
                    
                    # Tokenize the text into sentences using nltk
                    sentences = nltk.tokenize.sent_tokenize(full_text)
                    
                    # Dynamically select sentences for the introduction
                    word_count = 0
                    introduction_sentences = []
                    
                    for sentence in sentences:
                        sentence_word_count = len(sentence.split())
                        if word_count + sentence_word_count > max_words:
                            break
                        
                        introduction_sentences.append(sentence)
                        word_count += sentence_word_count
                        
                        # Ensure at least 2 sentences and minimum word count
                        if len(introduction_sentences) >= 2 and word_count >= min_words:
                            break
                    
                    # Combine the selected sentences
                    introduction = ' '.join(introduction_sentences)
                    break
            except json.JSONDecodeError:
                continue  # Skip if the script is not valid JSON
        
        # Fallback if JSON-LD `articleBody` is not found
        if not introduction:
            title_tag = soup.find(['h1', 'h2', 'h3'])  # Look for header tags
            if title_tag:
                # Aggregate paragraphs until the desired word count is met
                paragraphs = []
                word_count = 0
                sentence_count = 0
                
                for p_tag in title_tag.find_all_next('p'):
                    text = p_tag.get_text(strip=True)
                    if text:
                        sentences = nltk.tokenize.sent_tokenize(text)
                        for sentence in sentences:
                            sentence_word_count = len(sentence.split())
                            if word_count + sentence_word_count > max_words:
                                break
                            
                            paragraphs.append(sentence)
                            word_count += sentence_word_count
                            sentence_count += 1
                            if sentence_count >= 2 and word_count >= min_words:
                                break
                        if sentence_count >= 2 and word_count >= min_words:
                            break
                
                introduction = ' '.join(paragraphs) if paragraphs else 'Introduction not found.'
        
        return title, introduction
    except Exception as e:
        return 'Error', 'Error: ' + str(e)


# In[33]:


# Apply the function only to rows where Publisher is "RTBF"
def apply_rtbf_extraction(df):
    # Iterate through rows and update the relevant columns
    for idx, row in df.iterrows():
        if row['Publisher'] == "RTBF":
            title, introduction = extract_title_and_introduction_rtbf(row['Link'])
            df.at[idx, 'title sel'] = title
            df.at[idx, 'intro sel'] = introduction


# In[34]:


# Call the function on your DataFrame
apply_rtbf_extraction(df_fout)


# In[35]:


# Call the function on your DataFrame
apply_rtbf_extraction(df_goed)


# ### Nu alle selenium zooi. hopelijk dit deel vervangen met een API

# In[36]:


#!pip install selenium


# Volkskrant !!! gebruikt selenium dus daar nog naar kijken mbt API

# In[37]:


import pandas as pd
import re
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.core.os_manager import ChromeType


# def process_row(row):
#     """
#     Extract the title and introduction for rows where the Publisher contains 'volkskrant' (case insensitive).
#     Uses Selenium in headless mode.
#     """
#     if "volkskrant" not in row["Publisher"].lower():
#         return row  # Skip rows that don't match the condition

#     # Set up headless Firefox options
#     options = Options()
#     options.headless = True  # Run in headless mode

#     # Initialize the Firefox WebDriver
#     service = Service(GeckoDriverManager().install())
#     driver = webdriver.Firefox(service=service, options=options)

#     try:
#         # Construct the link with removepaywall prefix
#         url = row["Link"]
#         full_url = f"https://www.removepaywall.com/search?url={url}"
        
#         # Step 1: Get the archive link
#         driver.get(full_url)
#         driver.implicitly_wait(10)  # Wait up to 10 seconds for elements to load
        
#         # Locate the iframe and extract its src attribute
#         try:
#             iframe = driver.find_element(By.TAG_NAME, "iframe")
#             archive_url = iframe.get_attribute("src")
#         except:
#             row["title sel"] = "No iframe found"
#             row["intro sel"] = "No iframe found"
#             return row
        
#         # Step 2: Extract the title and introduction from the archive page
#         driver.get(archive_url)
#         driver.implicitly_wait(10)  # Wait for the page to load
        
#         # Get the full HTML source
#         html = driver.page_source
        
#         # Find the section containing the introduction using raw HTML
#         section_match = re.search(r'<section.*?>(.*?)</section>', html, re.DOTALL)
#         if section_match:
#             # Extract the raw HTML inside the <section>
#             section_content = section_match.group(1)
            
#             # Stop at the first </div> and extract text
#             div_match = re.search(r'<div.*?>(.*?)</div>', section_content, re.DOTALL)
#             if div_match:
#                 raw_intro_html = div_match.group(1)  # Raw HTML of the first <div>
#                 introduction = re.sub(r'<.*?>', '', raw_intro_html).strip()  # Strip any remaining HTML tags
#             else:
#                 introduction = "No introduction found"
#         else:
#             introduction = "No content section found"
        
#         # Extract the title
#         title_match = re.search(r'<h1.*?>(.*?)</h1>', html, re.DOTALL)
#         title = re.sub(r'<.*?>', '', title_match.group(1)).strip() if title_match else "No title found"
        
#         # Update the row
#         row["title sel"] = title
#         row["intro sel"] = introduction
    
#     finally:
#         # Close the browser
#         driver.quit()

#     return row

# df_fout.apply(process_row, axis=1)


# #### !!! MSN nog aanpakken

# Met consent o matic eerst

# In[36]:

import streamlit as st
import pandas as pd
import re
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
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

# ✅ Function to extract title and introduction
def extract_title_and_introduction_selenium(url, driver):
    try:
        driver.get(url)
        sleep(3)  # Allow time for content to load

        # ✅ Extract the page source
        html_content = driver.page_source

        # ✅ Parse with BeautifulSoup
        soup = BeautifulSoup(html_content, "html.parser")

        # ✅ Extract Title
        title = soup.title.text.strip() if soup.title else "Title not found"

        # ✅ Extract Introduction (fallback mechanism)
        meta_description = soup.find("meta", attrs={"name": "description"})
        if meta_description and "content" in meta_description.attrs:
            meta_content = meta_description["content"]
            if meta_content.endswith("..."):  # If meta content is truncated
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
            title_tag = soup.find(["h1", "h2", "h3"])
            first_paragraph = title_tag.find_next("p").text.strip() if title_tag and title_tag.find_next("p") else "First paragraph not found."
            introduction = first_paragraph

        return title, introduction

    except Exception as e:
        return "Error", f"Error: {str(e)}"

# ✅ Function to extract and add title/introduction to DataFrame
def extract_and_add_columns(row, driver):
    title, introduction = extract_title_and_introduction_selenium(row['Link'], driver)
    return pd.Series([title, introduction], index=['title sel', 'intro sel'])

# ✅ Streamlit UI
st.title("Selenium Web Scraper (Chromium) - Streamlit Cloud Ready")

# ✅ Initialize WebDriver once
driver = get_driver()

# ✅ Apply function to DataFrame
df_fout.loc[:, ['title sel', 'intro sel']] = df_fout.apply(
    lambda row: extract_and_add_columns(row, driver), axis=1, result_type='expand'
)

# ✅ Close WebDriver after all processing
driver.quit()

# ✅ Display results
st.write("### 🔹 Scraping Results:")
st.dataframe(df_fout)




# #### Hier uncess codes weghalen. Als ik code echt beter maak dan moet ik title sel enzo nooit aanmaken en dan kan de check ook blijven maarja

# In[39]:


df_fout = df_fout.drop(columns=['title_new', 'introduction_new', 'title check', 'intro check'])


# ### Functie aanmaken voor GPT evaluation 

# In[40]:


import string

def process_dataframe(df, content_check):
    
    # Apply the content_check function and populate the 'evaluation' column
    df['evaluation'] = df.apply(
        lambda row: content_check(
            title=row['title sel'], 
            introduction=row['intro sel'], 
            example_title=row['Title'], 
            example_snippet=row['Snippet']
        ), 
        axis=1
    )
    
    # Function to remove punctuation from a string
    def remove_punctuation(text):
        return text.translate(str.maketrans('', '', string.punctuation))
    
    # Split the 'evaluation' column and remove punctuation
    df[['title check', 'intro check']] = df['evaluation'].str.split(',', expand=True)
    df['title check'] = df['title check'].apply(remove_punctuation).str.strip()
    df['intro check'] = df['intro check'].apply(remove_punctuation).str.strip()
    
    # Drop the 'evaluation' column
    df = df.drop(columns=['evaluation'])
    
    return df


# ### Hier de content check weer

# In[41]:


# Assuming df_fout and content_check are defined
df_fout = process_dataframe(df_fout, content_check)


# ### Goede naar df_goed sorteren en uit df_fout halen functie aanmaken

# In[42]:


def process_good_rows(df_fout, df_goed):
    """
    Filter rows with 'goed' in both 'title check' and 'intro check' columns, 
    append them to df_goed, and remove them from df_fout.
    
    Args:
        df_fout (pd.DataFrame): The source DataFrame to filter rows from.
        df_goed (pd.DataFrame): The target DataFrame to append filtered rows to.
        
    Returns:
        tuple: Updated DataFrames (df_fout, df_goed).
    """
    # Filter rows where both 'title check' and 'intro check' are 'goed'
    good_rows = df_fout[
        (df_fout['title check'].str.lower() == 'goed') & 
        (df_fout['intro check'].str.lower() == 'goed')
    ]
    
    # Append the filtered rows to df_goed
    df_goed = pd.concat([df_goed, good_rows], ignore_index=True)
    
    # Remove the filtered rows from df_fout
    df_fout = df_fout[
        ~((df_fout['title check'].str.lower() == 'goed') & 
          (df_fout['intro check'].str.lower() == 'goed'))
    ]
    
    return df_fout, df_goed


# ### Functie oproepen

# In[43]:


# Assuming df_fout and df_goed are already defined
df_fout, df_goed = process_good_rows(df_fout, df_goed)

### Hier kijken naar alles op streamlit hoe goed het werkt

# ✅ Print DataFrame lengths in Streamlit
st.write(f"🔹 Length of `df_fout`: {len(df_fout)}")
st.write(f"🔹 Length of `df_goed`: {len(df_goed)}")

# ✅ Display DataFrames in Streamlit
st.write("### ❌ Incorrect Entries (df_fout):")
st.dataframe(df_fout)  # Display df_fout

st.write("### ✅ Correct Entries (df_goed):")
st.dataframe(df_goed)  # Display df_goed




# In[44]:


#len(df_fout), len(df_goed)


# Doet de beautifulsoup iets? 5 eraf, maar twee fouten gevonde, weet niet of dat bij beautiful erbij is. Ik comment er voor nu uit voor de zekerheid

# In[45]:


# def extract_title_and_introduction_noheader(url):
#     try:
#         # Make a GET request to fetch the raw HTML content
#         response = requests.get(url)
        
#         # Parse the HTML content
#         soup = BeautifulSoup(response.text, 'html.parser')
        
#         # Extract the title of the page
#         title = soup.title.text.strip() if soup.title else 'Title not found'
        
#         # Try to extract the introduction from the meta description
#         meta_description = soup.find('meta', attrs={'name': 'description'})
#         if meta_description and 'content' in meta_description.attrs:
#             meta_content = meta_description['content']
#             # If meta content ends with "...", ensure it has more characters than the fallback
#             if meta_content.endswith('...'):
#                 title_tag = soup.find(['h1', 'h2', 'h3'])  # Look for header tags
#                 if title_tag:
#                     first_paragraph = title_tag.find_next('p')
#                     fallback_content = first_paragraph.text.strip() if first_paragraph else ''
#                     if len(fallback_content) > len(meta_content):
#                         introduction = fallback_content
#                     else:
#                         introduction = meta_content
#                 else:
#                     introduction = meta_content
#             else:
#                 introduction = meta_content
#         else:
#             # Fall back to extracting the first <p> after the title header
#             title_tag = soup.find(['h1', 'h2', 'h3'])  # Look for header tags
#             if title_tag:
#                 # Find the first <p> after the title
#                 first_paragraph = title_tag.find_next('p')  
#                 introduction = first_paragraph.text.strip() if first_paragraph else 'First paragraph not found.'
#             else:
#                 introduction = 'Introduction not found.'
        
#         return title, introduction
#     except Exception as e:
#         return 'Error', 'Error: ' + str(e)


# In[46]:


# Apply the function to the DataFrame and create new columns
# df_fout[['title sel', 'intro sel']] = df_fout['Link'].apply(lambda x: pd.Series(extract_title_and_introduction_noheader(x)))


# In[47]:


# df_fout = process_dataframe(df_fout, content_check)


# In[48]:


# # Assuming df_fout and df_goed are already defined
# df_fout, df_goed = process_good_rows(df_fout, df_goed)


# In[49]:


# len(df_fout), len(df_goed)


# In[50]:


# df_goed


# ### Normaal hier umatrix, maar aangezien dit toch niet met streamlit kan skip ik het

# ### Titels schoonmaken

# In[51]:


# # Replace 'title sel' with 'Title' where 'title check' == "Fout"
# df_fout.loc[df_fout['title check'] == "Fout", 'title sel'] = df_fout['Title']


# # In[52]:


# # Replace 'intro sel' with 'Snippet' where 'intro check' == "Fout"
# df_fout.loc[df_fout['intro check'] == "Fout", 'intro sel'] = df_fout['Snippet']


# # In[53]:


# # Add the 'Adjust' column to each DataFrame
# df_fout['Adjust'] = 0  # For rows from df_fout
# df_goed['Adjust'] = 1  # For rows from df_goed

# # Merge the DataFrames
# df_final = pd.concat([df_fout, df_goed], ignore_index=True)


# # ### Functie maken om titels te schonen

# # In[54]:


# def title_clean(title):
#     try:
#         # Call the model
#         completion = client.chat.completions.create(
#             model="gpt-4o-mini",
#             messages=[
#                 {
#                     "role": "system",
#                     "content": 'Je taak is om een titel op te schonen van dingen die er niet in horen te staan'
#                     'Het zijn titels van artikelen en soms zit er iets om de titel heen wat er niet hoort zoals de uitgever of krant.'
#                     ' De titel kan zowel in het Nederlands of Frans zijn.'
#                     'Haal dit allemaal eruit en geef alleen de titel terug.'
#                     'Bijvoorbeeld als je de volgende titel krijgt: "VIDEO |Urine als wasmiddel: zo kun je lichaamssappen gebruiken | Home | AD.nl" '
#                     'Dan output je alleen de titel: "Urine als wasmiddel: zo kun je lichaamssappen gebruiken"'
#                     'Let op dat er geen inhoud uit de titel verwijderd wordt'
#                     'Geef niks anders terug dan de opgeschoonde titel. Als de titel al schoon is, dan output je de titel gewoon weer zoals die al was.'
#                 },
#                 {
#                     "role": "user",
#                     "content": f"Dit is de titel: '{title}'"
#                 }
#             ]
#         )
#         # Extract the classification result
#         return completion.choices[0].message.content.strip()
#     except Exception as e:
#         # Handle any errors (e.g., API rate limits or network issues)
#         st.write(f"Error processing country '{title}': {e}")
#         return None


# # In[55]:


# df_final['title sel'] = df_final['title sel'].apply(title_clean)


# # ### !!! misschien kan df_final ooit verandert worden naar df

# # ### Hier alle functies die we nodig gaan hebben

# # In[56]:


# def region_check(title, intro):
#     try:
#         # Call the model
#         completion = client.chat.completions.create(
#             model="gpt-4o-mini",
#             messages=[
#                 {
#                     "role": "system",
#                     "content": (
#                         'Je krijgt een titel en introductie van een artikel te zien. Als deze Nederlands-/Vlaamstalig is, output: "BENL". '
#                         'Is deze Franstalig, output: "BEFR". '
#                         'Output alleen deze hoofdletters zonder punten of iets toe te voegen.'
#                     )
#                 },
#                 {
#                     "role": "user",
#                     "content": (
#                         f"Dit is de titel: {title}. "
#                         f"Dit is de introductie: {intro}."
#                     )
#                 }
#             ]
#         )
#         # Extract the classification result
#         return completion.choices[0].message.content.strip()
#     except Exception as e:
#         # Handle any errors (e.g., API rate limits or network issues)
#         st.write(f"Error processing title '{title}': {e}")
#         return None


# # In[57]:


# def translate_title(title):
#     try:
#         # Call the model
#         completion = client.chat.completions.create(
#             model="gpt-4o-mini",
#             messages=[
#                 {
#                     "role": "system",
#                     "content": (
#                         'Je krijgt een titel van een artikel te zien. Deze is in het Frans.'
#                         'Vertraal deze naar het Nederlands.'
#                         'Output alleen de vertaling en niks anders'
#                     )
#                 },
#                 {
#                     "role": "user",
#                     "content": (
#                         f"Dit is de titel: {title}. "
#                     )
#                 }
#             ]
#         )
#         # Extract the classification result
#         return completion.choices[0].message.content.strip()
#     except Exception as e:
#         # Handle any errors (e.g., API rate limits or network issues)
#         st.write(f"Error processing title '{title}': {e}")
#         return None


# # In[58]:


# def translate_intro(intro):
#     try:
#         # Call the model
#         completion = client.chat.completions.create(
#             model="gpt-4o-mini",
#             messages=[
#                 {
#                     "role": "system",
#                     "content": (
#                         'Je krijgt introductie van een artikel te zien. Deze is in het Frans.'
#                         'Vertraal deze naar het Nederlands.'
#                         'Output alleen de vertaling en niks anders'
#                     )
#                 },
#                 {
#                     "role": "user",
#                     "content": (
#                         f"Dit is de introductie: {intro}."
#                     )
#                 }
#             ]
#         )
#         # Extract the classification result
#         return completion.choices[0].message.content.strip()
#     except Exception as e:
#         # Handle any errors (e.g., API rate limits or network issues)
#         st.write(f"Error processing title '{title}': {e}")
#         return None


# # In[59]:


# def make_text(df):
#     # Filter and extract the specified columns
#     media_order = ["niveau 1", "niveau 2", "niveau 3"]

#     selected_values_nl = df.loc[
#     (df['Country'] == "NL") & (df['select'] == "1"),['title sel', 'intro sel', 'Publisher', 'Link', 'Media niveau', 'Adjust', 'Keyword']].sort_values(by='Media niveau', key=lambda col: pd.Categorical(col, categories=media_order, ordered=True))

#     selected_values_benl = df.loc[
#     (df['Country'] == "BENL") & (df['select'] == "1"),['title sel', 'intro sel', 'Publisher', 'Link', 'Media niveau', 'Adjust', 'Keyword']].sort_values(by='Media niveau', key=lambda col: pd.Categorical(col, categories=media_order, ordered=True))

#     selected_values_befr = df.loc[
#     (df['Country'] == "BEFR") & (df['select'] == "1"),['title sel', 'intro sel', 'Publisher', 'Link', 'Media niveau', 'Adjust', 'Keyword']].sort_values(by='Media niveau', key=lambda col: pd.Categorical(col, categories=media_order, ordered=True))
    
#     #selected_values_nl = df.loc[(df['Country'] == "NL") & (df['select'] == "1"), ['title sel', 'intro sel', 'Publisher', 'Link']]
#     #selected_values_benl = df.loc[(df['Country'] == "BENL") & (df['select'] == "1"), ['title sel', 'intro sel', 'Publisher', 'Link']]
#     #selected_values_befr = df.loc[(df['Country'] == "BEFR") & (df['select'] == "1"), ['title sel', 'intro sel', 'Publisher', 'Link']]
    
#     # Format the output for each row
#     st.write("NL:\n")
#     for _, row in selected_values_nl.iterrows():
#         if row['Adjust'] == 0:
#             st.write(f"NIET VOLLEDIG! {row['Publisher']} | {row['title sel']} \n{row['intro sel']}\n{row['Link']}\n{row['Media niveau']} Steekwoord: {row['Keyword']}\n")
#         else:
#             st.write(f"{row['Publisher']} | {row['title sel']} \n{row['intro sel']}\n{row['Link']}\n{row['Media niveau']} Steekwoord: {row['Keyword']}\n")

#         # Format the output for each row
#     st.write("BENL:\n")
#     for _, row in selected_values_benl.iterrows():
#         if row['Adjust'] == 0:
#             st.write(f"NIET VOLLEDIG! {row['Publisher']} | {row['title sel']} \n{row['intro sel']}\n{row['Link']}\n{row['Media niveau']} Steekwoord: {row['Keyword']}\n")
#         else:
#             st.write(f"{row['Publisher']} | {row['title sel']} \n{row['intro sel']}\n{row['Link']}\n{row['Media niveau']} Steekwoord: {row['Keyword']}\n")

#     st.write("BEFR:\n")
#     for _, row in selected_values_befr.iterrows():
#         if row['Adjust'] == 0:
#             st.write(f"NIET VOLLEDIG! {row['Publisher']} | {row['title sel']} \n{row['intro sel']}\n{row['Link']}\n{row['Media niveau']} Steekwoord: {row['Keyword']}\n")
#         else:
#             st.write(f"{row['Publisher']} | {row['title sel']} \n{row['intro sel']}\n{row['Link']}\n{row['Media niveau']} Steekwoord: {row['Keyword']}\n")
    


# # In[60]:


# def make_text_fails(df):
#     # Filter and extract the specified columns
#     media_order = ["niveau 1", "niveau 2", "niveau 3"]

#     selected_values_nl = df.loc[
#     (df['Country'] == "NL") & (df['select'] == "0"),['title sel', 'intro sel', 'Publisher', 'Link', 'Media niveau', 'Adjust', 'Keyword']].sort_values(by='Media niveau', key=lambda col: pd.Categorical(col, categories=media_order, ordered=True))

#     selected_values_benl = df.loc[
#     (df['Country'] == "BENL") & (df['select'] == "0"),['title sel', 'intro sel', 'Publisher', 'Link', 'Media niveau', 'Adjust', 'Keyword']].sort_values(by='Media niveau', key=lambda col: pd.Categorical(col, categories=media_order, ordered=True))

#     selected_values_befr = df.loc[
#     (df['Country'] == "BEFR") & (df['select'] == "0"),['title sel', 'intro sel', 'Publisher', 'Link', 'Media niveau', 'Adjust', 'Keyword']].sort_values(by='Media niveau', key=lambda col: pd.Categorical(col, categories=media_order, ordered=True))
    
#     #selected_values_nl = df.loc[(df['Country'] == "NL") & (df['select'] == "1"), ['title sel', 'intro sel', 'Publisher', 'Link']]
#     #selected_values_benl = df.loc[(df['Country'] == "BENL") & (df['select'] == "1"), ['title sel', 'intro sel', 'Publisher', 'Link']]
#     #selected_values_befr = df.loc[(df['Country'] == "BEFR") & (df['select'] == "1"), ['title sel', 'intro sel', 'Publisher', 'Link']]

#     st.write("DEZE ZIJN ERUIT GEFILTERD, DUS OVERHEEN SKIMMEN\n\n")
#     # Format the output for each row
#     st.write("NL:\n")
#     for _, row in selected_values_nl.iterrows():
#         if row['Adjust'] == 0:
#             st.write(f"NIET VOLLEDIG! {row['Publisher']} | {row['title sel']} \n{row['intro sel']}\n{row['Link']}\n{row['Media niveau']} Steekwoord: {row['Keyword']}\n")
#         else:
#             st.write(f"{row['Publisher']} | {row['title sel']} \n{row['intro sel']}\n{row['Link']}\n{row['Media niveau']} Steekwoord: {row['Keyword']}\n")

#         # Format the output for each row
#     st.write("BENL:\n")
#     for _, row in selected_values_benl.iterrows():
#         if row['Adjust'] == 0:
#             st.write(f"NIET VOLLEDIG! {row['Publisher']} | {row['title sel']} \n{row['intro sel']}\n{row['Link']}{row['Media niveau']} Steekwoord: {row['Keyword']}\n")
#         else:
#             st.write(f"{row['Publisher']} | {row['title sel']} \n{row['intro sel']}\n{row['Link']}\n{row['Media niveau']} Steekwoord: {row['Keyword']}\n")

#     st.write("BEFR:\n")
#     for _, row in selected_values_befr.iterrows():
#         if row['Adjust'] == 0:
#             st.write(f"NIET VOLLEDIG! {row['Publisher']} | {row['title sel']} \n{row['intro sel']}\n{row['Link']}{row['Media niveau']} Steekwoord: {row['Keyword']}\n")
#         else:
#             st.write(f"{row['Publisher']} | {row['title sel']} \n{row['intro sel']}\n{row['Link']}\n{row['Media niveau']} Steekwoord: {row['Keyword']}\n")
    


# # We kunnen nu beginnen per bedrijf! !!! Dit kan denk ik ook efficienter door een column met een waarde te maken, en niet steeds een nieuwe dataframe aan te maken per bedrijf maarja

# # ## Greenwheels

# # In[61]:


# # Define the list of keywords to filter
# keyword_greenwheels = [
#     "Deelauto",
#     "Deelvervoer",
#     "Autoluw",
#     "Autoluwe stad",
#     "Autovrije stad",
#     "Verkeer(sregels) Amsterdam",
#     "Verkeersveiligheid Amsterdam",
#     "Leefbare steden",
#     "Parkeren",
# ]

# # Convert the keywords list to lowercase
# keyword_greenwheels = [k.lower() for k in keyword_greenwheels]

# # Filter the DataFrame to include only rows with these keywords
# df_green = df_final[df_final['Keyword'].str.lower().isin(keyword_greenwheels)]

# # Save the filtered DataFrame to a new variable
# df_green.reset_index(drop=True, inplace=True)


# # ### Relevante prompt Greenwheels !!! Hier ook een standaard prompt met aanvullingen per bedrijf, maar dat hoort bij prompt gedeelte

# # In[62]:


# def green_select(title, intro):
#     try:
#         # Call the model
#         completion = client.chat.completions.create(
#             model="gpt-4o-mini",
#             messages=[
#                 {
#                    "role": "system",
#                    "content": "Je bent een nieuwsmonitor-expert voor het bedrijf Greenwheels." 
#              "Greenwheels is een autodeelservice waarmee gebruikers eenvoudig een auto kunnen huren voor korte of langere periodes, zonder de lasten van autobezit." 
#              "Het bedrijf biedt een duurzame en flexibele mobiliteitsoplossing, vooral in stedelijke gebieden, waarbij brandstof, verzekering en onderhoud meestal inbegrepen zijn." 
#              "Jouw taak is om te beoordelen of een artikel relevant kan zijn voor Greenwheels, op basis van de titel en introductie van het artikel." 
#              "Relevante artikelen zijn bijvoorbeeld artikelen die gaan over: autoluwe steden, deelauto’s, (betaald) parkeren, autobezit, relevante wet- en regelgeving, of als Greenwheels zelf wordt genoemd."
#              "Let op de volgende richtlijnen:" 
#              "- Artikelen over lokale of regionale gebeurtenissen zijn meestal niet relevant, tenzij het gaat over grote steden zoals Amsterdam of Rotterdam, of als het onderwerp meerdere steden of gemeenten betreft."
#              "- Het artikel moet impact hebben op een breed publiek en niet over individuele gevallen of fun facts gaan." 
#              "- Artikelen moeten voornamelijk betrekking hebben op landen in de Benelux of relevante regelgeving die invloed heeft op Greenwheels. "
#              "- Het is mogelijk dat een artikel over een relevant onderwerp gaat, maar toch niet relevant is omdat het over één specifieke (kleinere) stad of gemeente gaat. Let op: één gemeente of stad is niet relevant, meerdere gemeente of steden zijn wel relevant!"
#              "Als het artikel relevant is voor Greenwheels, output: 1. Als het artikel niet relevant is voor Greenwheels, output: 0."
#                 },
#                 {
#                     "role": "user",
#                     "content": f"Dit zijn de titel en introductie van het artikel: '{title, intro}'"
#                 }
#             ]
#         )
#         # Extract the classification result
#         return completion.choices[0].message.content.strip()
#     except Exception as e:
#         # Handle any errors (e.g., API rate limits or network issues)
#         st.write(f"Error processing country '{title, intro}': {e}")
#         return None


# # In[63]:


# df_green['select'] = df_green.apply(lambda row: green_select(row['title sel'], row['intro sel']), axis=1)


# # In[64]:


# df_green['select'] = df_green['select'].apply(lambda x: '1' if '1' in x else ('0' if '0' in x else x))


# # ### Opmaak

# # In[65]:


# make_text(df_green)


# # In[66]:


# make_text_fails(df_green)


# # ### Too Good To Go

# # In[67]:


# keywords_TGTG = [
#     "Voedselverspilling",
#     "Verspillingsvrije week",
#     "Eten weggooien",
#     "Eten redden",
#     "overgebleven eten",
#     "Voedselverspilling horeca",
#     "Voedselverspilling supermarkten",
#     "eten over de datum",
#     "voedsel overschotten",
#     "Voedsel",
#     "Voedselprijzen",
#     "derving",
#     "voedselketen",
#     "Toogoodtogo",
#     "Foodwaste",
#     "anti verspillings app",
#     "AH overblijvers",
#     "regelgeving voedselverspilling",
#     "Gaspillage alimentaire",
#     "Semaine sans gaspillage",
#     "Jeter de la nourriture",
#     "Sauver de la nourriture",
#     "Restes de repas",
#     "Gaspillage alimentaire dans la restauration",
#     "Gaspillage alimentaire dans les supermarchés",
#     "Nourriture périmée",
#     "Excédents alimentaires",
#     "Alimentation",
#     "Prix des denrées alimentaires",
#     "Pertes",
#     "Chaîne alimentaire",
#     "Too good to go",
#     "toogoodtogo",
#     "(anti-)voedselverspilling",
#     "THT/TGT-datum",
#     "Verspillingsvrije week",
#     "Eten redden",
#     "wetgeving voedsel(verspilling)",
#     "voedselketen",
#     "Chaîne alimentaire"
# ]

# # Convert the keywords list to lowercase
# keywords_TGTG = [k.lower() for k in keywords_TGTG]

# # Filter the DataFrame, converting 'Keyword' to lowercase for comparison
# df_TGTG = df_final[df_final['Keyword'].str.lower().isin(keywords_TGTG)]

# # Save the filtered DataFrame to a new variable
# df_TGTG.reset_index(drop=True, inplace=True)


# # ### Region check !!! dit moet echt allemaal tegelijk maar dat komt later

# # In[68]:


# df_TGTG.loc[df_TGTG['Country'] == "BE", 'Country'] = df_TGTG.loc[df_TGTG['Country'] == "BE", ['title sel', 'intro sel']].apply(
#     lambda row: region_check(row['title sel'], row['intro sel']), axis=1
# )


# # ### Vertaalschatjes !!! Net als deze in één keer

# # In[69]:


# # Apply the translation functions separately for the 'title sel' and 'intro sel' columns
# df_TGTG.loc[df_TGTG['Country'] == "BEFR", 'title sel'] = df_TGTG.loc[df_TGTG['Country'] == "BEFR", 'title sel'].apply(translate_title)
# df_TGTG.loc[df_TGTG['Country'] == "BEFR", 'intro sel'] = df_TGTG.loc[df_TGTG['Country'] == "BEFR", 'intro sel'].apply(translate_intro)


# # ### Relevante prompt Greenwheels

# # In[70]:


# def TGTG_select(title, intro):
#     try:
#         # Call the model
#         completion = client.chat.completions.create(
#             model="gpt-4o-mini",
#             messages=[
#                 {
#                       "role": "system",
#                       "content": "Je bent een nieuwsmonitor-expert voor het bedrijf Too Good To Go. "
#                       "Too Good To Go is een app waarmee gebruikers voordelig overgebleven voedsel kunnen kopen bij lokale winkels en restaurants, met als doel voedselverspilling te verminderen. "
#                       "Het bedrijf biedt een duurzame oplossing door consumenten te verbinden met bedrijven die hun overtollige eten willen verkopen in verrassingspakketten. "
#                       "Jouw taak is om te beoordelen of een artikel relevant kan zijn voor Too Good To Go, op basis van de titel en introductie van het artikel. "
#     "Relevante artikelen kunnen bijvoorbeeld gaan over: "
#     "- Voedselverspilling en manieren om dit te verminderen; "
#     "- Onderzoek of statistieken over voedselverspilling; "
#     "- Wetgeving, initiatieven of samenwerkingen die voedselverspilling aanpakken; "
#     "- Mogelijkheden voor Too Good To Go om zich als expert te positioneren; "
#     "- Andere onderwerpen met een duidelijke link naar de missie en activiteiten van Too Good To Go. "
#     "Let op de volgende richtlijnen:"
#     " - Artikelen die niet over eten gaan, zijn altijd niet relevant. "
#     "- Lokale of regionale gebeurtenissen zijn meestal niet relevant, tenzij het gaat over grote steden zoals Amsterdam of Rotterdam, of als het onderwerp meerdere steden of gemeenten betreft. "
#     "- Het artikel moet impact hebben op een breed publiek en niet over specifieke gevallen of fun facts gaan. "
#     "- Artikelen moeten voornamelijk betrekking hebben op landen in de Benelux of relevante regelgeving die invloed heeft op Too Good To Go. "
#     "- Het is mogelijk dat een artikel over een relevant onderwerp gaat, maar toch niet relevant is als het te lokaal of te specifiek is. "
#     "Als het artikel relevant kan zijn voor Too Good To Go, output: 1. Als het artikel niet relevant is voor Too Good To Go, output: 0."
#                 },
#                 {
#                     "role": "user",
#                     "content": f"Dit zijn de titel en introductie van het artikel: '{title, intro}'"
#                 }
#             ]
#         )
#         # Extract the classification result
#         return completion.choices[0].message.content.strip()
#     except Exception as e:
#         # Handle any errors (e.g., API rate limits or network issues)
#         st.write(f"Error processing country '{title, intro}': {e}")
#         return None


# # In[71]:


# df_TGTG['select'] = df_TGTG.apply(lambda row: TGTG_select(row['title sel'], row['intro sel']), axis=1)


# # In[72]:


# df_TGTG['select'] = df_TGTG['select'].apply(lambda x: '1' if '1' in x else ('0' if '0' in x else x))


# # ### Opmaak

# # In[73]:


# make_text(df_TGTG)


# # In[74]:


# make_text_fails(df_TGTG)


# # ### Ecover

# # In[75]:


# keywords_eco = ["Schoonmaak",
#     "Schoonmaken",
#     "Duurzaam",
#     "Ecologisch schoonmaken",
#     "(Duurzame) schoonmaaktips",
#     "Hacks",
#     "(Kleding) wassen",
#     "Wasmiddel",
#     "Hergebruik",
#     "Hervullen",
#     "Plastic",
#     "Verpakking",
#     "Le nettoyage",
#     "Nettoyer",
#     "Nettoyage durable",
#     "Nettoyage écologique",
#     "Trucs et astuces de nettoyage (durable)",
#     "Lavage",
#     "Détergent",
#     "Réutilisation",
#     "Recharge",
#     "Plastique",
#     "Emballage", 
#     "duurzaam/ecologisch",
#     "wassen"
# ]

# # Convert the keywords list to lowercase
# keywords_eco = [k.lower() for k in keywords_eco]

# # Filter the DataFrame, converting 'Keyword' to lowercase for comparison
# df_eco = df_final[df_final['Keyword'].str.lower().isin(keywords_eco)]

# # Save the filtered DataFrame to a new variable
# df_eco.reset_index(drop=True, inplace=True)



# # ### Country check

# # In[76]:


# df_eco.loc[df_eco['Country'] == "BE", 'Country'] = df_eco.loc[df_eco['Country'] == "BE", ['title sel', 'intro sel']].apply(
#     lambda row: region_check(row['title sel'], row['intro sel']), axis=1
# )


# # ### Vertaalschatjes

# # In[77]:


# # Apply the translation functions separately for the 'title sel' and 'intro sel' columns
# df_eco.loc[df_eco['Country'] == "BEFR", 'title sel'] = df_eco.loc[df_eco['Country'] == "BEFR", 'title sel'].apply(translate_title)
# df_eco.loc[df_eco['Country'] == "BEFR", 'intro sel'] = df_eco.loc[df_eco['Country'] == "BEFR", 'intro sel'].apply(translate_intro)


# # ### Relevante Prompt

# # In[78]:


# def eco_select(title, intro):
#     try:
#         # Call the model
#         completion = client.chat.completions.create(
#             model="gpt-4o-mini",
#             messages=[
#                 {
#                     "role": "system",
#                     "content": 'Je bent een nieuwsmonitor expert for het bedrijf Ecover. Je taak is om relevante nieuwsartikelen voor het bedrijf te markeren.'
#                     'Ecover is een Belgisch merk dat ecologische schoonmaak- en wasproducten ontwikkelt, gemaakt van hernieuwbare en biologisch afbreekbare ingrediënten.'
#                     'Het merk richt zich op duurzaamheid en milieuvriendelijkheid, met verpakkingen van gerecycleerde materialen en een productieproces met minimale impact op het milieu. Hier volgen wat criteria waar relevante nieuws aan moet voldoen:'
#                     '1. Duurzaamheid en Milieu: Nieuws over duurzaamheid, milieuvriendelijke innovaties tot de verpakking of zeep van het bedrijf, of regelgeving rondom duurzame zeep of plastic, en biologisch afbreekbare producten.'
#                     '2. Wet- en Regelgeving: Nieuwe nationale of internationale regelgeving die betrekking heeft op verpakkingen, of duurzaamheidsstandaarden die impact kunnen hebben op Ecover’s producten of productie.'
#                     '3. Consumententrends: Trends of veranderend consumentengedrag gericht op ecologische schoonmaakmiddelen.'
#                     '4. Concurrentie en Marktontwikkelingen: Nieuws over concurrenten of nieuwe spelers in de markt van ecologische schoonmaakmiddelen, evenals grote marktontwikkelingen in deze sector.'
#                     '5. Hergebruik huishoudelijk afval'
#                     '6. Beleid over het verminderen van plastic.'
#                     '7. Nieuw onderzoek over zeep of plastic verpakkingen.'
#                     'Je krijgt de titel en introductie van het artikel te zien.'
#                     'Jouw taak is om te kijken of het artikel relevant kan zijn voor Ecover. '
#                     'Let op: het nieuws moet niet te regionaal of lokaal zijn. Gaat het dus over iets wat er in een stad of gemeente gebeurt, dan is dit niet relevant (uitzonderingen zijn grote steden zoals Amsterdam of Rotterdam). Het moet niet over specifieke gevallen gaan. Het moet over nieuws gaan wat impact heeft op veel mensen, niet over fun facts.'
#                     'Het kan dus voorkomen dat het artikel over gerecyclede verpakkingen gaat, maar dat dit niet relevant is, omdat het zich afspeelt in een kleine stad.'
#                     'Het moet voornamelijk betrekking hebben op landen in de benelux of relevante nieuwe regegeving zijn voor het bedrijf.'
#                     'Als het artikel relevant kan zijn voor het bedrijf, output: 1'
#                     'Als het artikel niet relevant is voor het bedrijf, output: 0'
#                 },
#                 {
#                     "role": "user",
#                     "content": f"Dit zijn de titel en introductie van het artikel: '{title, intro}'"
#                 }
#             ]
#         )
#         # Extract the classification result
#         return completion.choices[0].message.content.strip()
#     except Exception as e:
#         # Handle any errors (e.g., API rate limits or network issues)
#         st.write(f"Error processing country '{title, intro}': {e}")
#         return None


# # In[79]:


# df_eco['select'] = df_eco.apply(lambda row: eco_select(row['title sel'], row['intro sel']), axis=1)


# # In[80]:


# df_eco['select'] = df_eco['select'].apply(lambda x: '1' if '1' in x else ('0' if '0' in x else x))


# # ### Opmaak

# # In[81]:


# make_text(df_eco)


# # In[82]:


# make_text_fails(df_eco)


# # ### Alsico

# # In[83]:


# keywords_als = ["bedrijfskleding", "beschermende kleding", "duurzaam textiel", "persoonlijke beschermingsmiddelen (PBM)", "Professionele werkkleding",
#                 "Vêtements de travail",
#                 "werkkledij",
#                 "Werkkleding",
#                 "wetgeving kleding(industrie)",
#                 "Workwear"
# ]

# # Convert the keywords list to lowercase
# keywords_als = [k.lower() for k in keywords_als]

# # Filter the DataFrame, converting 'Keyword' to lowercase for comparison
# df_als = df_final[df_final['Keyword'].str.lower().isin(keywords_als)]

# # Save the filtered DataFrame to a new variable
# df_als.reset_index(drop=True, inplace=True)


# # ### Country Check

# # In[84]:


# df_als.loc[df_als['Country'] == "BE", 'Country'] = df_als.loc[df_als['Country'] == "BE", ['title sel', 'intro sel']].apply(
#     lambda row: region_check(row['title sel'], row['intro sel']), axis=1
# )


# # ### Vertaalschatjes

# # In[85]:


# # Apply the translation functions separately for the 'title sel' and 'intro sel' columns
# df_als.loc[df_als['Country'] == "BEFR", 'title sel'] = df_als.loc[df_als['Country'] == "BEFR", 'title sel'].apply(translate_title)
# df_als.loc[df_als['Country'] == "BEFR", 'intro sel'] = df_als.loc[df_als['Country'] == "BEFR", 'intro sel'].apply(translate_intro)


# # ### Relevante prompt

# # In[86]:


# def als_select(title, intro):
#     try:
#         # Call the model
#         completion = client.chat.completions.create(
#             model="gpt-4o-mini",
#             messages=[
#                 {
                    
#   "role": "system",
#   "content": "Je bent een nieuwsmonitor-expert voor het bedrijf Alsico. Je taak is om relevante nieuwsartikelen voor het bedrijf te markeren. Alsico is een van de grootste producenten van werkkleding. Het bedrijf is gespecialiseerd in duurzame kleding die bescherming biedt tegen omgevingsfactoren zoals hitte, contaminatie en andere risico's. Daarnaast richt Alsico zich op de circulaire economie en innovatie binnen de textielsector. Jouw taak is om artikelen te selecteren die relevant zijn voor de bedrijfsactiviteiten van Alsico, met een focus op werkkleding (niet voor particuliere consumenten). Voorbeelden van relevante artikelen zijn: - Artikelen over werkkleding, inclusief innovaties in textieltechnologie of beschermende kleding. - Nieuws over mogelijke concurrenten of samenwerkingen binnen de sector. - Ontwikkelingen rondom duurzaamheid of circulaire economie in de textielindustrie. - Regelgeving die impact kan hebben op de productie, verkoop of het gebruik van werkkleding. Let op: Het nieuws moet niet te regionaal of lokaal zijn. Artikelen over gebeurtenissen die alleen in een stad of gemeente plaatsvinden, zijn niet relevant (uitzonderingen zijn grote steden zoals Brussel of Antwerpen, of als het meerdere steden en gemeenten betreft). Het artikel moet impact hebben op een breed publiek en niet over specifieke gevallen of fun facts gaan. Artikelen moeten voornamelijk betrekking hebben op landen in de Benelux of relevante internationale regelgeving voor de werkkledingsector. Als het artikel relevant kan zijn voor Alsico, output: 1. Als het artikel niet relevant is voor Alsico, output: 0."


#                 },
#                 {
#                     "role": "user",
#                     "content": f"Dit zijn de titel en introductie van het artikel: '{title, intro}'"
#                 }
#             ]
#         )
#         # Extract the classification result
#         return completion.choices[0].message.content.strip()
#     except Exception as e:
#         # Handle any errors (e.g., API rate limits or network issues)
#         st.write(f"Error processing country '{title, intro}': {e}")
#         return None


# # In[87]:


# df_als['select'] = df_als.apply(lambda row: als_select(row['title sel'], row['intro sel']), axis=1)


# # In[88]:


# df_als['select'] = df_als['select'].apply(lambda x: '1' if '1' in x else ('0' if '0' in x else x))


# # ### Opmaak

# # In[89]:


# make_text(df_als)


# # In[90]:


# make_text_fails(df_als)


# # 
