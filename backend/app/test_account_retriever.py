#!/usr/bin/env python3
import sys
from aws_account_retriever import AWSAccountRetriever

def test_account_retriever():
    """Test the AWS Account Retriever functionality"""
    print("Testing AWS Account Retriever...")
    
    # Initialize the retriever
    retriever = AWSAccountRetriever()
    
    # Test getting all accounts
    print("\n=== Testing get_all_accounts() ===")
    all_accounts = retriever.get_all_accounts()
    print(f"Found {len(all_accounts)} accounts")
    
    # Test formatting account information
    print("\n=== Testing get_formatted_account_info() ===")
    formatted_info = retriever.get_formatted_account_info()
    print(formatted_info)
    
    # If an account ID was provided as a command-line argument, test getting that specific account
    if len(sys.argv) > 1:
        account_id = sys.argv[1]
        print(f"\n=== Testing get_formatted_account_info('{account_id}') ===")
        account_info = retriever.get_formatted_account_info(account_id)
        print(account_info)

if __name__ == "__main__":
    test_account_retriever()
