import gspread
from google.oauth2.service_account import Credentials
import os

SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
]

SHEET_URL = "https://docs.google.com/spreadsheets/d/1ieYlf08NfQMZMpsKlMcC2OIzOMjrn5bGmg1dMKgXcrY/edit"

HEADERS = [
    "Post ID", "Role", "Company Name", "Location", "Primary Skills",
    "Secondary Skills", "Must To Have", "Years of Experience",
    "Looking For College Students", "Intern", "Salary Package",
    "Email", "Phone", "Hiring Intent", "Author Name",
    "Author LinkedIn URL", "Post URL", "Date Posted",
    "Date Processed", "Keyword Matched"
]

def get_sheet():
    creds = Credentials.from_service_account_file('credentials.json', scopes=SCOPES)
    client = gspread.authorize(creds)
    sheet = client.open_by_url(SHEET_URL).sheet1
    return sheet

def setup_headers(sheet):
    existing = sheet.row_values(1)
    if not existing:
        sheet.insert_row(HEADERS, 1)
        print("Headers added!")

def write_jobs_to_sheet(jobs):
    sheet = get_sheet()
    setup_headers(sheet)
    for job in jobs:
        row = [
            job.get("post_id", ""),
            job.get("role", ""),
            job.get("company_name", ""),
            job.get("location", ""),
            job.get("primary_skills", ""),
            job.get("secondary_skills", ""),
            job.get("must_have", ""),
            job.get("years_of_experience", ""),
            job.get("looking_for_college_students", ""),
            job.get("intern", ""),
            job.get("salary_package", ""),
            job.get("email", ""),
            job.get("phone", ""),
            job.get("hiring_intent", ""),
            job.get("author_name", ""),
            job.get("author_linkedin_url", ""),
            job.get("post_url", ""),
            job.get("date_posted", ""),
            job.get("date_processed", ""),
            job.get("keyword_matched", "")
        ]
        sheet.append_row(row)
        print(f"Written to sheet: {job.get('role')} @ {job.get('company_name')}")
    print(f"\nTotal {len(jobs)} jobs written to Google Sheet!")

if __name__ == "__main__":
    sheet = get_sheet()
    setup_headers(sheet)
    print("Sheet connection successful!")