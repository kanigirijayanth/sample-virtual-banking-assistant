import requests
import json
import websocket
import threading
import time
from typing import Dict, List, Optional, Union, Callable

class AWSAccountClient:
    """Client for interacting with the AWS Account API"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        """
        Initialize the AWS Account Client
        
        Args:
            base_url: Base URL of the API server
        """
        self.base_url = base_url
        self.ws = None
        self.ws_thread = None
        self.callback = None
    
    def get_all_accounts(self) -> List[Dict]:
        """Get all AWS accounts"""
        response = requests.get(f"{self.base_url}/accounts")
        if response.status_code == 200:
            return response.json()["accounts"]
        else:
            print(f"Error: {response.status_code} - {response.text}")
            return []
    
    def get_account(self, account_id: str) -> Dict:
        """Get a specific AWS account by ID or name"""
        response = requests.get(f"{self.base_url}/accounts/{account_id}")
        if response.status_code == 200:
            return response.json()["account"]
        else:
            print(f"Error: {response.status_code} - {response.text}")
            return {}
    
    def get_accounts_by_classification(self, classification: str) -> List[Dict]:
        """Get AWS accounts by classification"""
        response = requests.get(f"{self.base_url}/accounts/classification/{classification}")
        if response.status_code == 200:
            return response.json()["accounts"]
        else:
            print(f"Error: {response.status_code} - {response.text}")
            return []
    
    def get_accounts_by_status(self, status: str) -> List[Dict]:
        """Get AWS accounts by status"""
        response = requests.get(f"{self.base_url}/accounts/status/{status}")
        if response.status_code == 200:
            return response.json()["accounts"]
        else:
            print(f"Error: {response.status_code} - {response.text}")
            return []
    
    def get_accounts_by_management(self, management_type: str) -> List[Dict]:
        """Get AWS accounts by management type"""
        response = requests.get(f"{self.base_url}/accounts/management/{management_type}")
        if response.status_code == 200:
            return response.json()["accounts"]
        else:
            print(f"Error: {response.status_code} - {response.text}")
            return []
    
    def get_total_cost(self) -> Dict:
        """Get total cost of all AWS accounts"""
        response = requests.get(f"{self.base_url}/accounts/cost/total")
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Error: {response.status_code} - {response.text}")
            return {}
    
    def connect_websocket(self, callback: Callable[[Dict], None]):
        """
        Connect to the WebSocket for real-time queries
        
        Args:
            callback: Function to call when a response is received
        """
        self.callback = callback
        ws_url = f"ws://{self.base_url.split('://')[-1]}/ws"
        
        def on_message(ws, message):
            data = json.loads(message)
            if self.callback:
                self.callback(data)
        
        def on_error(ws, error):
            print(f"WebSocket error: {error}")
        
        def on_close(ws, close_status_code, close_msg):
            print("WebSocket connection closed")
        
        def on_open(ws):
            print("WebSocket connection opened")
        
        self.ws = websocket.WebSocketApp(
            ws_url,
            on_message=on_message,
            on_error=on_error,
            on_close=on_close,
            on_open=on_open
        )
        
        def run_websocket():
            self.ws.run_forever()
        
        self.ws_thread = threading.Thread(target=run_websocket)
        self.ws_thread.daemon = True
        self.ws_thread.start()
    
    def send_query(self, query: str):
        """
        Send a natural language query through the WebSocket
        
        Args:
            query: Natural language query about AWS accounts
        """
        if self.ws and self.ws.sock and self.ws.sock.connected:
            self.ws.send(json.dumps({
                "type": "query",
                "query": query
            }))
        else:
            print("WebSocket not connected")
    
    def disconnect(self):
        """Disconnect from the WebSocket"""
        if self.ws:
            self.ws.close()

# Example usage
if __name__ == "__main__":
    client = AWSAccountClient()
    
    # Get all accounts
    print("Getting all accounts...")
    accounts = client.get_all_accounts()
    print(f"Found {len(accounts)} accounts")
    
    # Get a specific account
    print("\nGetting account 100942612345...")
    account = client.get_account("100942612345")
    print(f"Account: {account}")
    
    # Get accounts by classification
    print("\nGetting Class-1 accounts...")
    class1_accounts = client.get_accounts_by_classification("Class-1")
    print(f"Found {len(class1_accounts)} Class-1 accounts")
    
    # Get total cost
    print("\nGetting total cost...")
    cost = client.get_total_cost()
    print(f"Total cost: {cost}")
    
    # Connect to WebSocket
    def handle_response(data):
        print(f"Received response: {data}")
    
    print("\nConnecting to WebSocket...")
    client.connect_websocket(handle_response)
    
    # Send a query
    print("\nSending query...")
    client.send_query("Show me all active accounts")
    
    # Wait for response
    time.sleep(2)
    
    # Disconnect
    client.disconnect()