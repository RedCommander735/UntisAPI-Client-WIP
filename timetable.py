import requests
import json
import logging
from datetime import datetime, timedelta

class Period:
    def __init__(self, start_time, end_time, room, subject, class_, teacher = None, type_ = None):
        self.start_time = start_time
        self.end_time = end_time
        self.room = room
        self.subject = subject
        self.class_ = class_
        self.teacher = teacher
        self.type_ = type_

WEEKDAYS = ["Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag"]


def get_date():
    day = datetime.today()
    start = day - timedelta(days=day.weekday())
    week_end = (start + timedelta(days=4)).strftime('%Y%m%d')
    week_start = start.strftime('%Y%m%d')
    return week_start, week_end


def load_credentials():
    try:
        with open("credentials.json") as credentials:
            creds = json.load(credentials)
            return creds["username"], creds["password"], creds["school"], creds["base_url"]
    except FileNotFoundError:
        print("Credentials file not found. Please fill in the following values")
        with open("credentials.json", "w") as credentials:
            json.dump({"username": input("Username: "), "password": input("Password: "), "school": input("School name [On WebUntis loginsite: ...?school= →SCHOOLNAME← ...]: "), "base_url": input("Base URL [On WebUntis loginsite: ...https:// →BASE URL← /WebUntis...]: ")}, credentials)
            credentials.close()
            return load_credentials()


def login(URL, params, user, password):
    auth = {"id":"ID","method": "authenticate","params": {"user": user, "password": password, "client": "python"},"jsonrpc":"2.0"}

    session = json.loads(requests.post(URL, params = params, json = auth).text)

    session_id = session["result"]["sessionId"]
    person_id = session["result"]["personId"]
    # person_type = session["result"]["personType"]
    # klasse_id = session["result"]["klasseId"]

    return session_id, person_id


def get_id_lists(URL, params, session_id):
    rooms = json.loads(requests.post(URL, params = params, json = {"id":"ID","method": "getRooms","params": {},"jsonrpc":"2.0"}, cookies = {'JSESSIONID': session_id}).text)["result"]
    subjects = json.loads(requests.post(URL, params = params, json = {"id":"ID","method": "getSubjects","params": {},"jsonrpc":"2.0"}, cookies = {'JSESSIONID': session_id}).text)["result"]
    schoolyear_id = json.loads(requests.post(URL, params = params, json = {"id":"ID","method": "getCurrentSchoolyear","params": {},"jsonrpc":"2.0"}, cookies = {'JSESSIONID': session_id}).text)["result"]["id"]
    classes = json.loads(requests.post(URL, params = params, json = {"id":"ID","method": "getKlassen","params": {"schoolyearId": schoolyear_id},"jsonrpc":"2.0"}, cookies = {'JSESSIONID': session_id}).text)["result"]
    
    return rooms, subjects, classes


def arrange_timetable(unstructured_timetable, room_list, subject_list, class_list):
    
    #replace room ids with names for better readability
    for room in room_list:
        for period in unstructured_timetable:
            if room["id"] == period["ro"][0]["id"]:
                period["ro"][0]["id"] = room["name"]
            try:
                if room["id"] == period["ro"][0]["orgid"]:
                    period["ro"][0]["orgid"] = room["name"]
            except:
                logging.info(f"No alternate room found for Period ID: {period['id']}")

    #replace subject ids with names for better readability
    for subject in subject_list:
        for period in unstructured_timetable:
            if subject["id"] == period["su"][0]["id"]:
                period["su"][0]["id"] = subject["name"]

    #replace class ids with names for better readability
    for klasse in class_list:
        for period in unstructured_timetable:
            if klasse["id"] == period["kl"][0]["id"]:
                period["kl"][0]["id"] = klasse["name"]

    sorted_timetable = sorted(unstructured_timetable, key = lambda x: x["date"], reverse = False)

    # save every period with the same date in a list
    date_list = []
    for period in sorted_timetable:
        if period["date"] not in date_list:
            date_list.append(period["date"])
    # and then sort the list by starting time and append it to a week list
    week_ = []
    for date in date_list:
        days = []
        for period in sorted_timetable:
            if period["date"] == date:
                days.append(period)
        week_.append(sorted(days, key = lambda x: x["startTime"], reverse = False))
    
    new_day = []
    new_week = []
    for i in week_:
        new_day = []
        for j in i:
            # TODO: fix this
            start_ = datetime.strptime(str(j["startTime"]).rjust(4, "0"), "%H%M")
            end_ = datetime.strptime(str(j["endTime"]).rjust(4, "0"), "%H%M")
            new_period = Period(start_, end_, j["ro"][0]["id"], j["su"][0]["id"], j["kl"][0]["id"])
            new_day.append(new_period)
        new_week.append(new_day)

    return new_week


def get_timetable():
    user, password, school_name, base_url = load_credentials()

    URL = f"https://{base_url}/WebUntis/jsonrpc.do"
    params = {'school': school_name}
    
    week_start, week_end = get_date()

    session_id, person_id = login(URL, params, user, password)

    rooms, subjects, classes = get_id_lists(URL, params, session_id)

    timetable_params = {"id":"ID","method": "getTimetable","params": {"id": person_id, "type": 5, "startDate": week_start, "endDate": week_end},"jsonrpc":"2.0"}
    
    timetable = json.loads(requests.post(URL, params = params, json = timetable_params, cookies = {'JSESSIONID': session_id}).text)["result"]

    week = arrange_timetable(timetable, rooms, subjects, classes)

    # logout to free up server space
    requests.post(URL, params = params, json = {"id":"ID","method": "logout","params": {},"jsonrpc":"2.0"}, cookies = {'JSESSIONID': session_id})

    return week

def print_tt(week_):
    for j, k in zip(week_, WEEKDAYS):
        print(k + ":")
        for i in j:
            print(f"{i.start_time.strftime('%H:%M')} - {i.end_time.strftime('%H:%M')}\n{i.subject} | {i.room}\n")
        print("\n")

if __name__ == "__main__":
    print_tt(get_timetable())