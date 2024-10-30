import os
import csv
import re
import requests
from bs4 import BeautifulSoup
import pandas as pd
import json


PROGRAMS = [901, 904, 906, 908, 909, 911]
SUFFIX = "all_courses.csv"
PROGRAMS = [f"{prog}_{SUFFIX}" for prog in PROGRAMS]
SEPARATOR = "$"


def get_context_of_website(path_and_query):
    """
        An example path_and_query:
            https://catalog.metu.edu.tr/course.php?prog=911&course_code=9110725
        path:
            course.php?
        query:
            prog=911&course_code=9110725
    """
    
    url = f'https://catalog.metu.edu.tr/{path_and_query}'

    response = requests.get(url)

    return response.text



def saveToCSV(data, filename):
    
    with open(filename, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerows(data)



def extract_iframe(html_content, id_name):
    info = ""
    
    soup = BeautifulSoup(html_content, "html.parser")
    section = soup.find(id=id_name)
    
    if section:
        
        iframe_src = section.get('src')    
        try:
            # Make a request to the iframe's URL to retrieve its content
            response = requests.get(iframe_src)
            # Check for any HTTP errors
            response.raise_for_status()  
            
            # Parse the iframe content with BeautifulSoup
            iframe_soup = BeautifulSoup(response.content, "html.parser")
            # Display the content text from the iframe
            info = iframe_soup.get_text(strip=True)
        
        except requests.exceptions.RequestException as e:
            # print(f"Error retrieving content from {iframe_id}: {e}")
            info = ""
    else:
        info = ""
    
    return info

def extract_course_content(html_content):
    content = ""
    
    soup = BeautifulSoup(html_content, "html.parser")    
    course_content_header = soup.find('h3', string="Course Content")
    
    if course_content_header:
        # print(f"\n{course_content_header.get_text()}:")
        
        # Extract the following text content (e.g., sibling or adjacent tags)
        content = course_content_header.find_next_sibling(string=True)
        if content:
            content = content.strip()
        else:
            content = ""
    else:
        content = ""
    
    return content

def make_dict(list_items):
    global SEPARATOR
    
    result_dict = {}
    for item in list_items:
        key, value = item.split(SEPARATOR, 1)  # Use maxsplit=1 to handle colons in keys
        result_dict[key.strip()] = value.strip()    
    
    return result_dict


def save_dict(dictionary, filename):

    with open(filename, 'w', encoding='utf-8') as json_file:
        json.dump(dictionary, json_file, ensure_ascii=False, indent=4)
    

def main():
    global PROGRAMS, SEPARATOR

    for program in PROGRAMS:
        
        df = pd.read_csv(program, encoding='utf-8')
        
        for url in df['URL'].tolist():
            html_content = get_context_of_website(url)
            soup = BeautifulSoup(html_content, "html.parser")

            tables = soup.find_all("table")
            table = tables[0]
            
            rows = table.find_all("tr")
            
            course_data = []
            for row in rows:
                cells = row.find_all(["td", "th"])
                cell_text = [cell.get_text(strip=True) for cell in cells]
                cell_text = " ".join(cell_text)
                
                # To eliminate the rows that does not contain ":"
                # For example: "The course set above should be completed before taking DI502 DATA INFORMATICS PROJECT ."
                # Please click: https://catalog.metu.edu.tr/course.php?prog=911&course_code=9110502 
                if ":" in cell_text:
                    
                    # "Prerequisite: 	Set 1: 9010509 , 9110501" has two colons
                    # Replace only the first occurrence of ":"
                    cell_text = cell_text.replace(":", SEPARATOR, 1)
                    
                    course_data.append(cell_text)
            
            course_data_dict = make_dict(course_data)
            
            
            course_data_dict["Course Objectives"]           = extract_iframe(html_content, "courseObjectives")
            course_data_dict["Course Learning Outcomes"]    = extract_iframe(html_content, "courseLearningOutcomes")
            course_data_dict["Course Content"]              = extract_course_content(html_content)
            
            
            filename = course_data_dict["Course Code"] +".json"
            save_dict(course_data_dict, filename)
            print(f"{filename} is saved.")



if __name__ == "__main__":
    main()