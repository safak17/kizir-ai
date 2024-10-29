import csv
import re
import requests
from bs4 import BeautifulSoup

PROGRAMS = [901, 904, 906, 908, 909, 911]

def get_context_of_website(prog):
    url = f'https://catalog.metu.edu.tr/prog_courses.php?prog={prog}'

    response = requests.get(url)

    return response.text



def saveToCSV(data, filename):
    
    with open(filename, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerows(data)



def main():
    global PROGRAMS

    for program in PROGRAMS:
        html_content = get_context_of_website(program)
        
        if "<table>" in html_content:
            soup = BeautifulSoup(html_content, "html.parser")
            tables = soup.find_all("table")
            table = tables[0]
                     
            rows = table.find_all("tr")
            
            course_data = []
            for row in rows:    
                # Extract all cells (both <td> and <th>)
                cells = row.find_all(["td", "th"])
                cell_text = [cell.get_text(strip=True) for cell in cells]
                
                # Extract all <a> tags defined in <td>
                links = row.find_all(["a"])
                if len(links) == 0:
                    cell_text.append("URL")
                else:
                    cell_text.append(f"{links[0]['href']}")
                
                course_data.append(cell_text)
            
            filename = f"{program}_all_courses.csv"
            saveToCSV(course_data, filename)
            print(f"{filename} is saved.")
        else:
            print("Oops something went wrong!")



if __name__ == "__main__":
    main()