import gspread
from google.oauth2.service_account import Credentials

# Path to your service account JSON key
SERVICE_ACCOUNT_FILE = r"C:\Users\lesta\OneDrive\Documents\Trent's Python\Pick-A-Date\database-445718-b3f994a39306.json"

# Define the scope
SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
]

# Authenticate and initialize gspread
credentials = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
gc = gspread.authorize(credentials)

# Open the Google Sheet by name or URL
spreadsheet = gc.open('Database')

# Access the first worksheet
worksheet = spreadsheet.sheet1

# Read data
data = worksheet.get_all_values()
print(data)

# Write data
worksheet.update_cell(2, 1, 'Admin')

# Read through the column and collect indices of empty cells
def find_empty(col):
    column_values = worksheet.col_values(col)  # Change the column index if needed
    for index, value in enumerate(column_values):
        # print(f'Row {index + 1}: "{value}"')  # Debugging: print each cell value
        if value.strip() == '':
            # print(f'Empty cell found at row {index + 1}')
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

    

    
