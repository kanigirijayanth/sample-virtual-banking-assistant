#!/usr/bin/env python3
import boto3
import os
import sys
import json
import re

def extract_account_numbers(text):
    """Extract AWS account numbers from text using regex"""
    # Look for 12-digit numbers that might be AWS account IDs
    account_pattern = r'\b\d{12}\b'
    return re.findall(account_pattern, text)

def list_aws_accounts():
    """
    List all AWS account numbers from Knowledge Base
    """
    try:
        # Initialize Bedrock agent runtime client
        bedrock_agent_runtime = boto3.client("bedrock-agent-runtime", region_name="us-east-1")
        
        # Query the knowledge base for account numbers
        response = bedrock_agent_runtime.retrieve(
            knowledgeBaseId="40KPMEUSQC",
            retrievalQuery={
                "text": "list all AWS account numbers and their owners"
            },
            retrievalConfiguration={
                "vectorSearchConfiguration": {
                    "numberOfResults": 10
                }
            }
        )
        
        # Process results
        print("AWS Account Numbers from Knowledge Base:")
        print("=======================================")
        
        all_accounts = set()
        
        for result in response.get("retrievalResults", []):
            content = result.get("content", {})
            text = content.get("text", "")
            
            # Extract account numbers
            account_numbers = extract_account_numbers(text)
            
            # Add to our set of unique account numbers
            all_accounts.update(account_numbers)
            
            # Print the raw text for reference
            print(f"\nSource content:")
            print(f"{text[:200]}...")
        
        # Print the list of unique account numbers
        print("\nExtracted Account Numbers:")
        for account in sorted(all_accounts):
            print(account)
            
        return list(all_accounts)
            
    except Exception as e:
        print(f"Error retrieving from knowledge base: {e}")
        import traceback
        traceback.print_exc()
        return []

if __name__ == "__main__":
    list_aws_accounts()