"""
AWS Account Retriever using Bedrock Knowledge Base

This module provides functions for retrieving AWS account information
from a Bedrock Knowledge Base instead of a CSV file.
"""

import os
import json
import boto3
import traceback
import re
from typing import Dict, List, Any, Optional, Union

class KBAccountRetriever:
    """
    Class to retrieve AWS account information from a Bedrock Knowledge Base.
    """
    
    def __init__(self, kb_id="KCZTEHHZFA", region="us-east-1"):
        """
        Initialize the AWS Account Retriever with Bedrock Knowledge Base.
        
        Args:
            kb_id (str): Knowledge base ID
            region (str): AWS region
        """
        self.kb_id = kb_id
        self.region = region
        self.bedrock_agent_runtime = boto3.client("bedrock-agent-runtime", region_name=region)
        print(f"Initialized KBAccountRetriever with Knowledge Base ID: {kb_id}")
        
    def read_digit_by_digit(self, number):
        """Read a number digit by digit"""
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
    
    def query_kb(self, query, max_results=5):
        """
        Query the knowledge base with the given query.
        
        Args:
            query (str): The query to send to the knowledge base
            max_results (int): Maximum number of results to retrieve
            
        Returns:
            list: List of results from the knowledge base
        """
        try:
            print(f"Querying knowledge base {self.kb_id} with: {query}")
            response = self.bedrock_agent_runtime.retrieve(
                knowledgeBaseId=self.kb_id,
                retrievalQuery={
                    "text": query
                },
                retrievalConfiguration={
                    "vectorSearchConfiguration": {
                        "numberOfResults": max_results
                    }
                }
            )
            
            print(f"Knowledge base response received. Results: {len(response.get('retrievalResults', []))}")
            
            results = []
            for result in response.get("retrievalResults", []):
                content = result.get("content", {})
                text = content.get("text", "")
                results.append(text)
            
            return results
        except Exception as e:
            print(f"Error retrieving from knowledge base: {e}")
            traceback.print_exc()
            return []
    
    def parse_account_info(self, text):
        """
        Parse account information from text.
        
        Args:
            text (str): Text containing account information
            
        Returns:
            dict: Parsed account information
        """
        account = {}
        
        # Try to extract account number
        account_number_match = re.search(r'Account Number:?\s*(\d+)', text)
        if account_number_match:
            account['AWS Account Number'] = account_number_match.group(1)
            account['account_number_reading'] = self.read_digit_by_digit(account['AWS Account Number'])
        
        # Try to extract account name
        account_name_match = re.search(r'Account Name:?\s*([^\n]+)', text)
        if account_name_match:
            account['AWS account Name'] = account_name_match.group(1).strip()
        
        # Try to extract provisioning date
        provisioning_date_match = re.search(r'Provisioning Date:?\s*([^\n]+)', text)
        if provisioning_date_match:
            account['Provisioning Date'] = provisioning_date_match.group(1).strip()
        
        # Try to extract status
        status_match = re.search(r'Status:?\s*([^\n]+)', text)
        if status_match:
            account['Status'] = status_match.group(1).strip()
        
        # Try to extract classification
        classification_match = re.search(r'Classification:?\s*([^\n]+)', text)
        if classification_match:
            account['Classification'] = classification_match.group(1).strip()
        
        # Try to extract management type
        management_type_match = re.search(r'Management Type:?\s*([^\n]+)', text)
        if management_type_match:
            account['Management Type'] = management_type_match.group(1).strip()
        
        # Try to extract cost
        cost_match = re.search(r'Cost:?\s*(\d+(?:\.\d+)?)\s*Indian Rupees', text)
        if cost_match:
            account['Total Cost in Indian Rupees'] = cost_match.group(1).strip()
        
        return account
    
    def get_account_info(self, account_id: str) -> str:
        """
        Get information about a specific AWS account.
        
        Args:
            account_id (str): AWS account ID or name to look up
            
        Returns:
            str: Formatted account information
        """
        query = f"Get information about AWS account {account_id}"
        results = self.query_kb(query)
        
        if not results:
            return f"No information found for AWS account {account_id}."
        
        # Use the first result that contains the account ID
        account_info = None
        for result in results:
            if account_id in result:
                account_info = result
                break
        
        if not account_info:
            account_info = results[0]
        
        # Parse the account information
        account = self.parse_account_info(account_info)
        
        if not account:
            return account_info  # Return the raw text if parsing fails
        
        # Format the response
        info = f"AWS Account Information:\n"
        info += f"=======================\n\n"
        
        if 'AWS Account Number' in account:
            info += f"Account Number: {account['AWS Account Number']} (read as: {account['account_number_reading']})\n"
        
        if 'AWS account Name' in account:
            info += f"Account Name: {account['AWS account Name']}\n"
        
        if 'Provisioning Date' in account:
            info += f"Provisioning Date: {account['Provisioning Date']}\n"
        
        if 'Status' in account:
            info += f"Status: {account['Status']}\n"
        
        if 'Classification' in account:
            info += f"Classification: {account['Classification']}\n"
        
        if 'Management Type' in account:
            info += f"Management Type: {account['Management Type']}\n"
        
        if 'Total Cost in Indian Rupees' in account:
            info += f"Total Cost: {account['Total Cost in Indian Rupees']} Indian Rupees"
        
        return info
    
    def get_account_cost(self, account_id: str) -> str:
        """
        Get the cost for a specific AWS account.
        
        Args:
            account_id (str): AWS account ID or name to look up
            
        Returns:
            str: Formatted cost information
        """
        query = f"What is the cost of AWS account {account_id}"
        results = self.query_kb(query)
        
        if not results:
            return f"No cost information found for AWS account {account_id}."
        
        # Use the first result that contains the account ID
        account_info = None
        for result in results:
            if account_id in result:
                account_info = result
                break
        
        if not account_info:
            account_info = results[0]
        
        # Parse the account information
        account = self.parse_account_info(account_info)
        
        if not account or 'Total Cost in Indian Rupees' not in account:
            return f"Could not extract cost information for AWS account {account_id} from the knowledge base."
        
        # Format the response
        info = f"AWS Account Cost Information:\n"
        info += f"=======================\n\n"
        
        if 'AWS Account Number' in account:
            info += f"Account Number: {account['AWS Account Number']} (read as: {account['account_number_reading']})\n"
        
        if 'AWS account Name' in account:
            info += f"Account Name: {account['AWS account Name']}\n"
        
        info += f"Total Cost: {account['Total Cost in Indian Rupees']} Indian Rupees"
        
        return info
    
    def get_accounts_by_classification(self, classification: str) -> str:
        """
        Get AWS accounts by classification.
        
        Args:
            classification (str): Classification to filter by
            
        Returns:
            str: Formatted account information
        """
        query = f"List AWS accounts with classification {classification}"
        results = self.query_kb(query)
        
        if not results:
            return f"No accounts found with classification {classification}."
        
        # Format the response
        info = f"AWS Accounts with Classification {classification}:\n"
        info += f"=======================\n\n"
        
        accounts_info = []
        for result in results:
            account = self.parse_account_info(result)
            if account and account.get('Classification', '').lower() == classification.lower():
                accounts_info.append(account)
        
        if not accounts_info:
            return f"No accounts found with classification {classification} in the knowledge base."
        
        info += f"Found {len(accounts_info)} accounts:\n\n"
        
        for account in accounts_info[:10]:  # Limit to first 10 accounts
            if 'AWS Account Number' in account:
                info += f"Account Number: {account['AWS Account Number']} (read as: {account['account_number_reading']})\n"
            
            if 'AWS account Name' in account:
                info += f"Account Name: {account['AWS account Name']}\n"
            
            if 'Status' in account:
                info += f"Status: {account['Status']}\n\n"
        
        if len(accounts_info) > 10:
            info += f"... and {len(accounts_info) - 10} more accounts."
        
        return info
    
    def get_accounts_by_status(self, status: str) -> str:
        """
        Get AWS accounts by status.
        
        Args:
            status (str): Status to filter by (ACTIVE or SUSPENDED)
            
        Returns:
            str: Formatted account information
        """
        query = f"List AWS accounts with status {status}"
        results = self.query_kb(query)
        
        if not results:
            return f"No accounts found with status {status}."
        
        # Format the response
        info = f"AWS Accounts with Status {status}:\n"
        info += f"=======================\n\n"
        
        accounts_info = []
        for result in results:
            account = self.parse_account_info(result)
            if account and account.get('Status', '').lower() == status.lower():
                accounts_info.append(account)
        
        if not accounts_info:
            return f"No accounts found with status {status} in the knowledge base."
        
        info += f"Found {len(accounts_info)} accounts:\n\n"
        
        for account in accounts_info[:10]:  # Limit to first 10 accounts
            if 'AWS Account Number' in account:
                info += f"Account Number: {account['AWS Account Number']} (read as: {account['account_number_reading']})\n"
            
            if 'AWS account Name' in account:
                info += f"Account Name: {account['AWS account Name']}\n"
            
            if 'Classification' in account:
                info += f"Classification: {account['Classification']}\n\n"
        
        if len(accounts_info) > 10:
            info += f"... and {len(accounts_info) - 10} more accounts."
        
        return info
    
    def get_total_cost(self) -> str:
        """
        Get total cost of all AWS accounts.
        
        Returns:
            str: Formatted cost information
        """
        query = "What is the total cost of all AWS accounts"
        results = self.query_kb(query)
        
        if not results:
            return "No cost information found."
        
        # Try to extract total cost from the results
        total_cost = None
        for result in results:
            cost_match = re.search(r'total cost.*?(\d+(?:\.\d+)?)\s*Indian Rupees', result, re.IGNORECASE)
            if cost_match:
                total_cost = cost_match.group(1)
                break
        
        if not total_cost:
            # If we can't extract the total cost directly, try to sum up individual account costs
            accounts_info = []
            for result in results:
                account = self.parse_account_info(result)
                if account and 'Total Cost in Indian Rupees' in account:
                    accounts_info.append(account)
            
            if accounts_info:
                try:
                    total_cost = sum(float(account['Total Cost in Indian Rupees']) for account in accounts_info)
                except:
                    pass
        
        # Format the response
        info = f"Total Cost of AWS Accounts:\n"
        info += f"=======================\n\n"
        
        if total_cost:
            info += f"The total cost of all AWS accounts is {total_cost} Indian Rupees."
        else:
            info += "Could not determine the total cost of all AWS accounts from the knowledge base."
        
        return info
    
    def get_formatted_account_info(self, account_id: Optional[str] = None) -> str:
        """
        Get formatted account information for a specific account or all accounts.
        
        Args:
            account_id (Optional[str]): AWS account ID to look up. If None, returns all accounts.
            
        Returns:
            str: Formatted account information
        """
        if account_id:
            # Get information about a specific account
            return self.get_account_info(account_id)
        else:
            # Get information about all accounts
            query = "List all AWS accounts"
            results = self.query_kb(query)
            
            if not results:
                return "No accounts found in the knowledge base."
            
            # Parse account information from results
            accounts_info = []
            for result in results:
                account = self.parse_account_info(result)
                if account and 'AWS Account Number' in account:
                    accounts_info.append(account)
            
            # Format the response
            info = f"AWS Account Information:\n"
            info += f"=======================\n\n"
            info += f"Found {len(accounts_info)} AWS accounts:\n\n"
            
            for account in accounts_info[:10]:  # Limit to first 10 accounts
                if 'AWS Account Number' in account:
                    info += f"Account Number: {account['AWS Account Number']} (read as: {account['account_number_reading']})\n"
                
                if 'AWS account Name' in account:
                    info += f"Account Name: {account['AWS account Name']}\n"
                
                if 'Status' in account:
                    info += f"Status: {account['Status']}\n"
                
                if 'Classification' in account:
                    info += f"Classification: {account['Classification']}\n\n"
            
            if len(accounts_info) > 10:
                info += f"... and {len(accounts_info) - 10} more accounts."
            
            return info
            
    def get_account_provisioning_date(self, account_id: str) -> str:
        """
        Get the provisioning date for a specific AWS account.
        
        Args:
            account_id (str): AWS account ID or name to look up
            
        Returns:
            str: Formatted provisioning date information
        """
        query = f"When was AWS account {account_id} provisioned"
        results = self.query_kb(query)
        
        if not results:
            return f"No information found for AWS account {account_id}."
        
        # Use the first result that contains the account ID
        account_info = None
        for result in results:
            if account_id in result:
                account_info = result
                break
        
        if not account_info:
            account_info = results[0]
        
        # Parse the account information
        account = self.parse_account_info(account_info)
        
        if not account or 'Provisioning Date' not in account:
            return f"Could not extract provisioning date for AWS account {account_id} from the knowledge base."
        
        # Format the response
        info = f"AWS Account Provisioning Date:\n"
        info += f"=======================\n\n"
        
        if 'AWS Account Number' in account:
            info += f"Account Number: {account['AWS Account Number']}\n"
        
        if 'AWS account Name' in account:
            info += f"Account Name: {account['AWS account Name']}\n"
        
        info += f"Provisioning Date: {account['Provisioning Date']}\n"
        
        return info
    
    def get_accounts_by_year(self, year: str) -> str:
        """
        Get the number of AWS accounts provisioned in a specific year.
        
        Args:
            year (str): Year to filter by (e.g., "2019")
            
        Returns:
            str: Formatted account count information
        """
        query = f"List AWS accounts provisioned in year {year}"
        results = self.query_kb(query)
        
        if not results:
            return f"No accounts were provisioned in the year {year}."
        
        # Parse account information from results
        accounts_info = []
        for result in results:
            account = self.parse_account_info(result)
            if account and 'Provisioning Date' in account and year in account['Provisioning Date']:
                accounts_info.append(account)
        
        if not accounts_info:
            return f"No accounts were provisioned in the year {year} according to the knowledge base."
        
        # Format the response
        info = f"AWS Accounts Provisioned in {year}:\n"
        info += f"=======================\n\n"
        info += f"Found {len(accounts_info)} accounts provisioned in {year}:\n\n"
        
        for account in accounts_info[:10]:  # Limit to first 10 accounts
            if 'AWS Account Number' in account:
                info += f"Account Number: {account['AWS Account Number']}\n"
            
            if 'AWS account Name' in account:
                info += f"Account Name: {account['AWS account Name']}\n"
            
            if 'Provisioning Date' in account:
                info += f"Provisioning Date: {account['Provisioning Date']}\n\n"
        
        if len(accounts_info) > 10:
            info += f"... and {len(accounts_info) - 10} more accounts."
        
        return info
