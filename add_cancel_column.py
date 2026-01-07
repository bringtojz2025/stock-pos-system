"""
Script to add "No" to Cancel column for existing rows that don't have the Cancel value
Run this once to initialize the Cancel column for all existing rows
"""

import gspread
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
import os

SCOPES = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']

def authenticate():
    creds = None
    if os.path.exists('token.pickle'):
        try:
            import pickle
            with open('token.pickle', 'rb') as token:
                creds = pickle.load(token)
        except:
            os.remove('token.pickle')

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except:
                creds = None
        
        if not creds:
            flow = InstalledAppFlow.from_client_secrets_file('client_secret.json', SCOPES)
            creds = flow.run_local_server(port=0)
        
        import pickle
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)
    return creds

def main():
    try:
        creds = authenticate()
        gc = gspread.authorize(creds)
        sh = gc.open("StockDB")
        sheet_sales = sh.worksheet("Sales")
        
        records = sheet_sales.get_all_values()
        print(f"Total rows (including header): {len(records)}")
        
        if len(records) > 0:
            print(f"Header: {records[0]}")
            print(f"Total columns: {len(records[0])}")
        
        # Update rows that don't have Cancel value (column 12)
        updated_count = 0
        for row_idx, row in enumerate(records[1:], start=2):  # Start from row 2 (after header)
            if len(row) >= 11:  # Has at least up to column 11
                # Check if column 12 (index 11) is empty
                cancel_value = row[11].strip() if len(row) > 11 and row[11] else ""
                
                if not cancel_value:  # Empty or doesn't exist
                    print(f"Row {row_idx}: Adding 'No' to Cancel column")
                    sheet_sales.update_cell(row_idx, 12, "No")  # column 12 = Cancel
                    updated_count += 1
        
        print(f"\nUpdated {updated_count} rows with 'No' in Cancel column")
        print("Done! All rows now have a Cancel value.")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
