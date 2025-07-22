from fastapi import FastAPI, HTTPException, WebSocket
from fastapi.middleware.cors import CORSMiddleware
import csv
import json
import os
import re
from typing import List, Dict, Optional, Union

app = FastAPI()

# Add CORS middleware to allow frontend to access the API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Path to the CSV file
CSV_FILE = "../AWS_AccountDetails.csv"

# Function to read the CSV file
def read_csv_file():
    accounts = []
    try:
        with open(CSV_FILE, 'r', encoding='utf-8-sig') as file:
            csv_reader = csv.DictReader(file)
            for row in csv_reader:
                # Skip empty rows
                if not row['AWS Account Number']:
                    continue
                accounts.append(row)
        return accounts
    except Exception as e:
        print(f"Error reading CSV file: {e}")
        return []

# Function to read digit by digit
def read_digit_by_digit(number):
    digit_names = {
        '0': 'zero',
        '1': 'one',
        '2': 'two',
        '3': 'three',
        '4': 'four',
        '5': 'five',
        '6': 'six',
        '7': 'seven',
        '8': 'eight',
        '9': 'nine'
    }
    
    return ' '.join(digit_names[digit] for digit in str(number))

# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "ok"}

# Get all accounts
@app.get("/accounts")
async def get_accounts():
    accounts = read_csv_file()
    if not accounts:
        raise HTTPException(status_code=404, detail="No accounts found")
    
    # Add digit-by-digit reading for account numbers
    for account in accounts:
        if account['AWS Account Number']:
            account['account_number_reading'] = read_digit_by_digit(account['AWS Account Number'])
    
    return {"accounts": accounts}

# Get account by ID
@app.get("/accounts/{account_id}")
async def get_account(account_id: str):
    accounts = read_csv_file()
    
    # Find account by ID or name
    for account in accounts:
        if account['AWS Account Number'] == account_id or account['AWS account Name'] == account_id:
            # Add digit-by-digit reading
            account['account_number_reading'] = read_digit_by_digit(account['AWS Account Number'])
            return {"account": account}
    
    raise HTTPException(status_code=404, detail=f"Account {account_id} not found")

# Get accounts by classification
@app.get("/accounts/classification/{classification}")
async def get_accounts_by_classification(classification: str):
    accounts = read_csv_file()
    filtered_accounts = [
        account for account in accounts 
        if account['Classification'] and account['Classification'].lower() == classification.lower()
    ]
    
    if not filtered_accounts:
        raise HTTPException(status_code=404, detail=f"No accounts found with classification {classification}")
    
    # Add digit-by-digit reading
    for account in filtered_accounts:
        account['account_number_reading'] = read_digit_by_digit(account['AWS Account Number'])
    
    return {"accounts": filtered_accounts}

# Get accounts by status
@app.get("/accounts/status/{status}")
async def get_accounts_by_status(status: str):
    accounts = read_csv_file()
    filtered_accounts = [
        account for account in accounts 
        if account['Active / Suspended'] and account['Active / Suspended'].lower() == status.lower()
    ]
    
    if not filtered_accounts:
        raise HTTPException(status_code=404, detail=f"No accounts found with status {status}")
    
    # Add digit-by-digit reading
    for account in filtered_accounts:
        account['account_number_reading'] = read_digit_by_digit(account['AWS Account Number'])
    
    return {"accounts": filtered_accounts}

# Get accounts by management type
@app.get("/accounts/management/{management_type}")
async def get_accounts_by_management(management_type: str):
    accounts = read_csv_file()
    filtered_accounts = [
        account for account in accounts 
        if account['Management Type'] and account['Management Type'].lower() == management_type.lower()
    ]
    
    if not filtered_accounts:
        raise HTTPException(status_code=404, detail=f"No accounts found with management type {management_type}")
    
    # Add digit-by-digit reading
    for account in filtered_accounts:
        account['account_number_reading'] = read_digit_by_digit(account['AWS Account Number'])
    
    return {"accounts": filtered_accounts}

# Get total cost
@app.get("/accounts/cost/total")
async def get_total_cost():
    accounts = read_csv_file()
    total_cost = sum(float(account['Total Cost in Indian Rupees']) for account in accounts if account['Total Cost in Indian Rupees'])
    return {"total_cost": total_cost, "currency": "Indian Rupees"}

# Get account provisioning date
@app.get("/accounts/provisioning-date/{account_id}")
async def get_account_provisioning_date(account_id: str):
    accounts = read_csv_file()
    
    # Find account by ID or name
    for account in accounts:
        if account['AWS Account Number'] == account_id or account['AWS account Name'] == account_id:
            return {
                "account_id": account_id,
                "account_name": account['AWS account Name'],
                "provisioning_date": account['Account Provisioning Date']
            }
    
    raise HTTPException(status_code=404, detail=f"Account {account_id} not found")

# Get accounts by year
@app.get("/accounts/year/{year}")
async def get_accounts_by_year(year: str):
    accounts = read_csv_file()
    filtered_accounts = [
        account for account in accounts 
        if year in account['Account Provisioning Date']
    ]
    
    if not filtered_accounts:
        raise HTTPException(status_code=404, detail=f"No accounts found provisioned in year {year}")
    
    # Add digit-by-digit reading
    for account in filtered_accounts:
        account['account_number_reading'] = read_digit_by_digit(account['AWS Account Number'])
    
    return {"year": year, "accounts": filtered_accounts, "count": len(filtered_accounts)}

# WebSocket endpoint for real-time communication
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()
            request = json.loads(data)
            
            if request.get("type") == "query":
                query = request.get("query", "").lower()
                
                # Process the query
                response = process_query(query)
                await websocket.send_text(json.dumps(response))
            
    except Exception as e:
        print(f"WebSocket error: {e}")

def process_query(query: str):
    """Process a natural language query and return relevant account information"""
    accounts = read_csv_file()
    
    # Check for account number in the query
    account_pattern = r'\b\d{12}\b'
    account_matches = re.findall(account_pattern, query)
    
    if account_matches:
        # Query is about a specific account
        account_id = account_matches[0]
        for account in accounts:
            if account['AWS Account Number'] == account_id:
                account['account_number_reading'] = read_digit_by_digit(account['AWS Account Number'])
                return {
                    "type": "account_info",
                    "account": account
                }
    
    # Check for classification queries
    if "class" in query:
        for classification in ["class-1", "class-2", "class-3"]:
            if classification in query:
                filtered_accounts = [
                    account for account in accounts 
                    if account['Classification'] and account['Classification'].lower() == classification.lower()
                ]
                for account in filtered_accounts:
                    account['account_number_reading'] = read_digit_by_digit(account['AWS Account Number'])
                return {
                    "type": "classification_info",
                    "classification": classification,
                    "accounts": filtered_accounts
                }
    
    # Check for status queries
    if "active" in query:
        filtered_accounts = [
            account for account in accounts 
            if account['Active / Suspended'] and account['Active / Suspended'].lower() == "active"
        ]
        for account in filtered_accounts:
            account['account_number_reading'] = read_digit_by_digit(account['AWS Account Number'])
        return {
            "type": "status_info",
            "status": "active",
            "accounts": filtered_accounts
        }
    
    if "suspended" in query:
        filtered_accounts = [
            account for account in accounts 
            if account['Active / Suspended'] and account['Active / Suspended'].lower() == "suspended"
        ]
        for account in filtered_accounts:
            account['account_number_reading'] = read_digit_by_digit(account['AWS Account Number'])
        return {
            "type": "status_info",
            "status": "suspended",
            "accounts": filtered_accounts
        }
    
    # Check for management type queries
    if "managed" in query or "self" in query or "service" in query:
        management_type = "managed services" if "managed" in query else "self service"
        filtered_accounts = [
            account for account in accounts 
            if account['Management Type'] and account['Management Type'].lower() == management_type.lower()
        ]
        for account in filtered_accounts:
            account['account_number_reading'] = read_digit_by_digit(account['AWS Account Number'])
        return {
            "type": "management_info",
            "management_type": management_type,
            "accounts": filtered_accounts
        }
    
    # Check for cost queries
    if "cost" in query or "total" in query:
        total_cost = sum(float(account['Total Cost in Indian Rupees']) for account in accounts if account['Total Cost in Indian Rupees'])
        return {
            "type": "cost_info",
            "total_cost": total_cost,
            "currency": "Indian Rupees"
        }
    
    # Check for provisioning date queries
    if "provisioning date" in query or "provision date" in query:
        if account_matches:
            account_id = account_matches[0]
            for account in accounts:
                if account['AWS Account Number'] == account_id or account['AWS account Name'] == account_id:
                    return {
                        "type": "provisioning_date_info",
                        "account_id": account_id,
                        "account_name": account['AWS account Name'],
                        "provisioning_date": account['Account Provisioning Date']
                    }
    
    # Check for accounts by year queries
    year_pattern = r'\b(20\d{2})\b'
    year_matches = re.findall(year_pattern, query)
    
    if year_matches and ("year" in query or "provisioned" in query):
        year = year_matches[0]
        filtered_accounts = [
            account for account in accounts 
            if year in account['Account Provisioning Date']
        ]
        for account in filtered_accounts:
            account['account_number_reading'] = read_digit_by_digit(account['AWS Account Number'])
        return {
            "type": "year_info",
            "year": year,
            "accounts": filtered_accounts,
            "count": len(filtered_accounts)
        }
    
    # Default: return all accounts
    for account in accounts:
        account['account_number_reading'] = read_digit_by_digit(account['AWS Account Number'])
    return {
        "type": "all_accounts",
        "accounts": accounts
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)