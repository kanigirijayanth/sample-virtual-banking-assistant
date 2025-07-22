"""
Simplified FastAPI WebSocket Server for Virtual Cloud Operations Assistant

This module implements a simplified WebSocket server using FastAPI that handles
communication between the frontend and the AWS account data.
"""

import asyncio
import json
import base64
import os
from pathlib import Path

from fastapi import FastAPI, WebSocket, Request, Response, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# Import account functions
from account_functions import (
    get_account_info, 
    list_accounts, 
    get_accounts_by_classification, 
    get_accounts_by_status, 
    get_total_cost,
    get_account_provisioning_date,
    get_accounts_by_year
)

# API key for WebSocket authentication
API_KEY = "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"

# Initialize FastAPI application
app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Store active connections
active_connections = {}

# Function to process queries
async def process_query(query: str, connection_id: str):
    """
    Process a natural language query and return relevant account information
    
    Args:
        query: The query from the user
        connection_id: The connection ID for the WebSocket
    """
    # Simple query processing
    query = query.lower()
    
    # Create a mock params object for the functions
    class MockParams:
        def __init__(self, connection_id):
            self.arguments = {}
            self.connection_id = connection_id
        
        async def result_callback(self, result):
            if self.connection_id in active_connections:
                # Format the response
                response = {
                    "event": "text",
                    "speaker": "assistant",
                    "data": format_response(result)
                }
                await active_connections[self.connection_id].send_text(json.dumps(response))
    
    params = MockParams(connection_id)
    
    # Check for account number in the query
    if "account" in query and any(digit in query for digit in "0123456789"):
        # Extract account number
        import re
        account_pattern = r'\b\d{12}\b'
        account_matches = re.findall(account_pattern, query)
        
        if account_matches:
            params.arguments["account_id"] = account_matches[0]
            await get_account_info(params)
            return
    
    # Check for list accounts
    if "list" in query and "account" in query:
        await list_accounts(params)
        return
    
    # Check for classification queries
    if "class" in query:
        for classification in ["class-1", "class-2", "class-3"]:
            if classification in query:
                params.arguments["classification"] = classification
                await get_accounts_by_classification(params)
                return
    
    # Check for status queries
    if "active" in query:
        params.arguments["status"] = "ACTIVE"
        await get_accounts_by_status(params)
        return
    
    if "suspended" in query:
        params.arguments["status"] = "SUSPENDED"
        await get_accounts_by_status(params)
        return
    
    # Check for cost queries
    if "cost" in query or "total" in query:
        await get_total_cost(params)
        return
    
    # Check for provisioning date queries
    if "provisioning date" in query or "provision date" in query:
        # Extract account number
        import re
        account_pattern = r'\b\d{12}\b'
        account_matches = re.findall(account_pattern, query)
        
        if account_matches:
            params.arguments["account_id"] = account_matches[0]
            await get_account_provisioning_date(params)
            return
    
    # Check for accounts by year queries
    if "year" in query and any(year in query for year in ["2019", "2020", "2021", "2022", "2023", "2024", "2025"]):
        # Extract year
        import re
        year_pattern = r'\b(20\d{2})\b'
        year_matches = re.findall(year_pattern, query)
        
        if year_matches:
            params.arguments["year"] = year_matches[0]
            await get_accounts_by_year(params)
            return
    
    # Default: list all accounts
    await list_accounts(params)

def format_response(result):
    """Format the response for the frontend"""
    if "message" in result:
        return result["message"]
    
    if "information" in result:
        return result["information"]
    
    if "accounts" in result:
        return result["accounts"]
    
    if "total_cost" in result:
        return f"The total cost of all AWS accounts is {result['total_cost']} {result['currency']}."
    
    return json.dumps(result)

@app.get('/health')
async def health(request: Request):
    """Health check endpoint."""
    return 'ok'

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint handling client connections.
    """
    # Accept the connection with the API key as subprotocol
    await websocket.accept(subprotocol=API_KEY)
    
    # Generate a unique connection ID
    connection_id = f"conn_{len(active_connections) + 1}"
    active_connections[connection_id] = websocket
    
    try:
        # Send welcome message
        welcome_message = {
            "event": "text",
            "speaker": "assistant",
            "data": "Hello! I'm your Virtual Cloud Operations Assistant. I can help you with AWS account information. What would you like to know?"
        }
        await websocket.send_text(json.dumps(welcome_message))
        
        # Listen for messages
        while True:
            message = await websocket.receive_text()
            
            try:
                # Try to parse as JSON
                data = json.loads(message)
                
                if isinstance(data, dict) and "query" in data:
                    # Process the query
                    await process_query(data["query"], connection_id)
                else:
                    # Treat as a query string
                    await process_query(message, connection_id)
            except json.JSONDecodeError:
                # Treat as a query string
                await process_query(message, connection_id)
            
    except WebSocketDisconnect:
        # Remove the connection
        if connection_id in active_connections:
            del active_connections[connection_id]
    except Exception as e:
        print(f"WebSocket error: {e}")
        if connection_id in active_connections:
            del active_connections[connection_id]

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)