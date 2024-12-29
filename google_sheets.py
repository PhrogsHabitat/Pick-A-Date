import gspread
from google.oauth2.service_account import Credentials
from oauth2client.service_account import ServiceAccountCredentials

# Path to your service account JSON key
SERVICE_ACCOUNT_FILE = r"database-445718-b3f994a39306.json"

# Define the scope
SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
]

# Initialize the cache
cache = {}

# Preload Google Sheets data
def preload_google_sheets():
    global cache
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name("database-445718-b3f994a39306.json", scope)
    client = gspread.authorize(creds)
    sheet = client.open("Database").sheet1
    expected_headers = ["Email", "Token", "Xtra", "HasToken"]  # Adjust this list based on your actual headers
    data = sheet.get_all_records(expected_headers=expected_headers)
    cache = {row['Email']: row for row in data}

# Authenticate and initialize gspread
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
credentials = ServiceAccountCredentials.from_json_keyfile_name("database-445718-b3f994a39306.json", scope)
gc = gspread.authorize(credentials)

# Open the Google Sheet by name or URL
spreadsheet = gc.open('Database')

# Access the first worksheet
worksheet = spreadsheet.sheet1

# Read data
data = worksheet.get_all_values()

# Write data
worksheet.update_cell(2, 1, 'Admin')

# Read through the column and collect indices of empty cells
def find_empty(col):
    column_values = worksheet.col_values(col)  # Change the column index if needed
    for index, value in enumerate(column_values):
        # print(f'Row {index + 1}: "{value}"')  # Debugging: print each cell value
        if not value:
            print(f'Empty cell found at row {index + 1}')
            empty_column = index + 1
            return empty_column
            
    else:
        print('No empty cell found in the column')

def change_row(col, row, username, password, email):
    column_values = worksheet.col_values(col)
    present = False
    for value in column_values:
        if value.lower() == email.lower():
            present = True
            break

    if not present:
        worksheet.update_cell(row, col, email.lower())
        worksheet.update_cell(row, col + 1, username)
        worksheet.update_cell(row, col + 2, password)

# Get cell value from cache
def get_cell_value(email, column_name):
    global cache
    if email not in cache:
        preload_google_sheets()
    return cache[email].get(column_name, "")

# Set cell value and refresh cache
def set_cell_value(email, column_name, value):
    global cache
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name("database-445718-b3f994a39306.json", scope)
    client = gspread.authorize(creds)
    sheet = client.open("Database").sheet1
    cell = sheet.find(email)
    col_index = sheet.find(column_name).col
    sheet.update_cell(cell.row, col_index, value)
    preload_google_sheets()

def signin(email, password):
    emailpresent = False
    passwordpresent = False

    column_values = worksheet.col_values(1)
    for value in column_values:
        if value.lower() == email.lower():
            emailpresent = True
            break

    column_values = worksheet.col_values(3)
    for value in column_values:
        if value == password:
            passwordpresent = True
            break

    if emailpresent and passwordpresent:
        for index, value in enumerate(worksheet.col_values(1)):
            if value.lower() == email.lower():
                row = index + 1
                worksheet.update_cell(row, 4, "True")
                break
    else:
        return False
    print(emailpresent)
    print(passwordpresent)

# Call preload_google_sheets at startup
preload_google_sheets()
