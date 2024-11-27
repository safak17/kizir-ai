import requests
from bs4 import BeautifulSoup
import os

DATA_PATH = os.path.join("..", "data", "courses")
filepath = os.path.join(DATA_PATH, "di_courses.txt")

url = "https://di.metu.edu.tr/en/courses"

response = requests.get(url)

if response.status_code == 200:
    
    soup = BeautifulSoup(response.text, 'html.parser')
    
    
    div_content = soup.find('div', class_='field-item even', attrs={'property': 'content:encoded'})
    
    if div_content:
        div_elements = div_content.find_all(['p', 'li'])
        
        
        with open(filepath, 'w', encoding='utf-8') as file:
            for element in div_elements:
                file.write(element.get_text() + '\n')
    
else:
    print(f"Failed to retrieve the webpage. Status code: {response.status_code}")
