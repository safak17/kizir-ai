import requests
from bs4 import BeautifulSoup
import os

DATA_PATH = os.path.join("..", "data", "courses")
filepath_content = os.path.join(DATA_PATH, "csec_courses.txt")
filepath_titles = os.path.join(DATA_PATH, "csec_titles.txt")


url = "https://ii.metu.edu.tr/cybersecurity-ms"

response = requests.get(url)


titles = []
content = []

if response.status_code == 200:
    
    soup = BeautifulSoup(response.text, 'html.parser')
    
    
    div_content = soup.find('div', class_='field-body')
    
    if div_content:
        div_elements = div_content.find_all(['p', 'h2', 'h3', 'h4', 'li'])
        
        
        for element in div_elements:
            content.append(element.get_text())
            
            if element.name.startswith("h"):
                titles.append(element.get_text())
                

        with open(filepath_content, 'w', encoding='utf-8') as file:
            file.writelines([item + '\n' for item in content])
        
        with open(filepath_titles, 'w', encoding='utf-8') as file:
            file.writelines([item + '\n' for item in titles])
            
        
else:
    print(f"Failed to retrieve the webpage. Status code: {response.status_code}")
