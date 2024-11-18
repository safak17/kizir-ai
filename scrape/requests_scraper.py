import csv
import re
import requests
import os

PROGRAMS = [901, 902, 903, 904, 905, 906, 908, 909, 910, 911]

CSV_HEADERS = ["Semester", "Program Code", "Program Short Name", "Course Code", "Course Name", "Credit", "ECTS Credit", "Course Section", "Capacity", "Day1", "Start Hour1", "End Hour1", "Instructor Name", "Instructor Title"]


def findCourses(s):
    pat = r'tr\s(((?!<tr).)*)<\\/tr>'
    courses = re.findall(pat, s)
    return [i[0] for i in courses]


def findHeaders(s):
    pat = r'"><b>(((?!<).)*)<'
    headers = re.findall(pat, s)
    return [i[0] for i in headers]


def findValues(s):
    pat = r'clickable\\">(((?!<td).)*)<\\/td>'
    values = re.findall(pat, s)
    return [i[0] for i in values]


def getContextofWebsite(semester, code):
    headers = {'Host': 'sis.metu.edu.tr',
                'Connection': 'close',
                'Content-Length': '155',
                'X-Requested-With': 'XMLHttpRequest',
                'Content-Type': 'application/x-www-form-urlencoded'}
    url = "https://sis.metu.edu.tr/main.php"
    params = {'selectSemester': semester, 'selectProgram': code,
            'stamp' : "O3ekT_0jEXuExWvQBp1fEfLkpowgmhkEsJxQJji_7tSsThqlXcFLKJmgaRMZ-X_gRkhqMZEEraY5lROApQPUDQ", 'submitSearchForm' : 'Search'}
    r = requests.post(url, data=params, headers=headers)
    raw = r.text
    return raw


def getUserInputs():
    code = input("code : ")
    semester = input("semester : ")
    section = input("section : ")
    ret = {'code': code, 'semester': semester, 'section': section}
    return ret


def makeDict(headers, values):
    ret = {}
    for i in range(len(values)):
        ret[headers[i]] = values[i].encode('utf-8').decode('unicode_escape')
    return ret


def findAllAvailableSections(courses, wantedCourse, header):
    availables = []
    for course in courses:
        if wantedCourse in course:
            values = findValues(course)
            valuesWithHeaders = makeDict(header,values)
            if int(valuesWithHeaders['Used Capacity']) < int(valuesWithHeaders['Capacity']):
                availables.append(valuesWithHeaders['Course Section'])
    return availables


def getProgramCodes(content):
    pattern = r'<option value="(\d{3})">[^<]+</option>'
    matches = re.findall(pattern, content)
    return matches


def getAllPrograms():
    url = 'https://sis.metu.edu.tr/get.php?package=KfvnzLOdhabgg5kUnlR4dBg4MvsAI9vaFnzBHyTioFwa7cRP5x65L_IpbLgxWxOejJK2shuQfZvN3VJEMWQTmA'

    headers = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'Accept-Language': 'tr-TR,tr;q=0.9,en-GB;q=0.8,en;q=0.7,ru-RU;q=0.6,ru;q=0.5,en-US;q=0.4',
        'Cache-Control': 'no-cache',
        'Connection': 'keep-alive',
        'Cookie': '_SIS_APP_LOCALE=EN',
        'Pragma': 'no-cache',
        'Referer': 'https://sis.metu.edu.tr/',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'same-origin',
        'Sec-Fetch-User': '?1',
        'Upgrade-Insecure-Requests': '1',
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36',
        'sec-ch-ua': '"Chromium";v="130", "Google Chrome";v="130", "Not?A_Brand";v="99"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"macOS"',
    }

    r = requests.get(url, headers=headers)
    return r.text


def getSemesters(content):
    pattern = r'<option value="(\d{5})">[^<]+</option>'
    matches = re.findall(pattern, content)
    return matches


def convertDictToCSV(dict):
    return [dict[header] for header in CSV_HEADERS]


def saveToCSV(data, filename):
    with open(filename, 'w') as file:
        writer = csv.writer(file)
        writer.writerow(CSV_HEADERS)
        for d in data:
            writer.writerow(d)


def main():
    content = getAllPrograms()
    programs = PROGRAMS or getProgramCodes(content)
    semesters = getSemesters(content)
    current_semester = semesters[0]

    for program in programs:
        raw_site = getContextofWebsite(current_semester, program)
        headers = findHeaders(raw_site)
        courses = findCourses(raw_site)

        course_data = []
        for course in courses:
            values = findValues(course)
            valuesWithHeaders = makeDict(headers, values)
            csv_data = convertDictToCSV(valuesWithHeaders)
            course_data.append(csv_data)
        
        filename = os.path.join("data", f"{current_semester}-{program}.csv")    
        saveToCSV(course_data, filename)


if __name__ == "__main__":
    main()