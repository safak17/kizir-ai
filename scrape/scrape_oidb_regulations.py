# Middle East Technical University Rules and Regulations Governing Undergraduate Studies
# https://oidb.metu.edu.tr/en/middle-east-technical-university-rules-and-regulations-governing-undergraduate-studies

import requests
from bs4 import BeautifulSoup
import os

DATA_PATH = os.path.join("..", "data", "regulations")

url = 'https://oidb.metu.edu.tr/en/middle-east-technical-university-rules-and-regulations-governing-undergraduate-studies'

response = requests.get(url)
response.raise_for_status()

soup = BeautifulSoup(response.text, 'html.parser')

titles = []
paragraphs = []

########################################################################
# TITLES & HEADERS
########################################################################
target_style_title = {
    "font-family" : "Roboto"
}

def matches_target_styles(span):
    if not span.has_attr("style"):
        return False
    styles = dict(item.split(":") for item in span["style"].split(";") if ":" in item)
    return all(styles.get(key, "").strip() == value for key, value in target_style_title.items())

matching_spans = soup.find_all("span")

for span in matching_spans:
    parent_span = span.find_parent("span")
    if parent_span and matches_target_styles(parent_span):
        titles.append(parent_span.get_text(strip=True))

# Write to file
title_path = os.path.join(DATA_PATH, "titles.txt")
with open(title_path, "w+") as file:
    for item in titles:
        file.write(item + "\n")



########################################################################
# PARAGRAPHS
########################################################################
target_style_paragraph = "text-align:justify; margin:0cm 0cm 8pt"

# Find all <p> elements with the exact matching style
matching_paragraphs = soup.find_all("p", style=target_style_paragraph)

# Print the text content of each matching paragraph, skipping those with only whitespace
for idx, paragraph in enumerate(matching_paragraphs, start=1):
    text = paragraph.get_text(strip=True)
    if text:  # Skip if text is empty or only whitespace
        paragraphs.append(text)
        
# Write to file
paragraph_path = os.path.join(DATA_PATH, "paragraphs.txt")
with open(paragraph_path, "w+") as file:
    for item in paragraphs:
        file.write(item + "\n")

