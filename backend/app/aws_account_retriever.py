#!/usr/bin/env python3
import csv
import json
import re
import os
import traceback
from typing import Dict, List, Any, Optional, Union

class AWSAccountRetriever:
    """
    Class to retrieve AWS account information from CSV file.
    """
    
    def __init__(self, csv_file: str = "AWS_AccountDetails.csv"):
        """
        Initialize the AWS Account Retriever.
        
        Args:
            csv_file (str): Path to the CSV file with account details
        """
        # Convert to absolute path if it's a relative path
        import os
        # Get the directory of the current file
        current_dir = os.path.dirname(os.path.abspath(__file__))
        
        if not os.path.isabs(csv_file):
            csv_file = os.path.abspath(os.path.join(current_dir, csv_file))
        
        self.csv_file = csv_file
        print(f"Using CSV file at: {csv_file}")
        print(f"Initialized AWSAccountRetriever with CSV file: {csv_file}")
        
        # Verify the file exists
        if not os.path.exists(csv_file):
            print(f"WARNING: CSV file not found: {csv_file}")
            # Try to find the file in parent directories
            parent_dir = os.path.dirname(current_dir)
            alternative_path = os.path.join(parent_dir, "AWS_AccountDetails.csv")
            if os.path.exists(alternative_path):
                self.csv_file = alternative_path
                print(f"Found CSV file at alternative location: {alternative_path}")
            else:
                # Try to find the file in the current directory
                current_dir_path = os.path.join(current_dir, "AWS_AccountDetails.csv")
                if os.path.exists(current_dir_path):
                    self.csv_file = current_dir_path
                    print(f"Found CSV file in current directory: {current_dir_path}")
                else:
                    print(f"Could not find CSV file in parent directory or current directory")
    
    def read_csv_file(self):
        """Read the CSV file and return a list of account dictionaries"""
        accounts = []
        try:
            # Check if file exists
            import os
            if not os.path.exists(self.csv_file):
                print(f"CSV file does not exist: {self.csv_file}")
                return []
                
            with open(self.csv_file, 'r', encoding='utf-8-sig') as file:
                csv_reader = csv.DictReader(file)
                for row in csv_reader:
                    # Skip empty rows
                    if not row.get('AWS Account Number'):
                        continue
                    # Add digit-by-digit reading
                    row['account_number_reading'] = self.read_digit_by_digit(row['AWS Account Number'])
                    accounts.append(row)
            
            print(f"Successfully read {len(accounts)} accounts from CSV file")
            return accounts
        except Exception as e:
            print(f"Error reading CSV file: {e}")
            traceback.print_exc()
            return []
    
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
    
    def get_all_accounts(self):
        """Get all AWS accounts"""
        return self.read_csv_file()
    
    def get_account_info(self, account_id: str) -> str:
        """
        Get information about a specific AWS account.
        
        Args:
            account_id (str): AWS account ID or name to look up
            
        Returns:
            str: Formatted account information
        """
        accounts = self.read_csv_file()
        
        # Find account by ID or name
        for account in accounts:
            if account['AWS Account Number'] == account_id or account['AWS account Name'] == account_id:
                # Format the response
                info = f"AWS Account Information:\n"
                info += f"=======================\n\n"
                info += f"Account Number: {account['AWS Account Number']} (read as: {account['account_number_reading']})\n"
                info += f"Account Name: {account['AWS account Name']}\n"
                info += f"Provisioning Date: {account['Account Provisioning Date']}\n"
                info += f"Status: {account['Active / Suspended']}\n"
                # Handle the space in the Classification field name
                classification_key = ' Classification' if ' Classification' in account else 'Classification'
                info += f"Classification: {account.get(classification_key, 'N/A')}\n"
                info += f"Management Type: {account['Management Type']}\n"
                info += f"Total Cost: {account['Total Cost in Indian Rupees']} Indian Rupees"
                
                return info
        
        return f"No information found for AWS account {account_id}."
    
    def get_accounts_by_classification(self, classification: str) -> str:
        """
        Get AWS accounts by classification.
        
        Args:
            classification (str): Classification to filter by
            
        Returns:
            str: Formatted account information
        """
        accounts = self.read_csv_file()
        
        # Handle the space in the Classification field name
        classification_key = ' Classification' if ' Classification' in accounts[0] else 'Classification'
        
        # Filter accounts by classification
        filtered_accounts = [
            account for account in accounts 
            if account.get(classification_key) and account.get(classification_key).lower() == classification.lower()
        ]
        
        if not filtered_accounts:
            return f"No accounts found with classification {classification}."
        
        # Format the response
        info = f"AWS Accounts with Classification {classification}:\n"
        info += f"=======================\n\n"
        info += f"Found {len(filtered_accounts)} accounts:\n\n"
        
        for account in filtered_accounts[:10]:  # Limit to first 10 accounts
            info += f"Account Number: {account['AWS Account Number']} (read as: {account['account_number_reading']})\n"
            info += f"Account Name: {account['AWS account Name']}\n"
            info += f"Status: {account['Active / Suspended']}\n\n"
        
        if len(filtered_accounts) > 10:
            info += f"... and {len(filtered_accounts) - 10} more accounts."
        
        return info
    
    def get_accounts_by_status(self, status: str) -> str:
        """
        Get AWS accounts by status.
        
        Args:
            status (str): Status to filter by (ACTIVE or SUSPENDED)
            
        Returns:
            str: Formatted account information
        """
        accounts = self.read_csv_file()
        
        # Filter accounts by status
        filtered_accounts = [
            account for account in accounts 
            if account['Active / Suspended'] and account['Active / Suspended'].lower() == status.lower()
        ]
        
        if not filtered_accounts:
            return f"No accounts found with status {status}."
        
        # Format the response
        info = f"AWS Accounts with Status {status}:\n"
        info += f"=======================\n\n"
        info += f"Found {len(filtered_accounts)} accounts:\n\n"
        
        for account in filtered_accounts[:10]:  # Limit to first 10 accounts
            info += f"Account Number: {account['AWS Account Number']} (read as: {account['account_number_reading']})\n"
            info += f"Account Name: {account['AWS account Name']}\n"
            # Handle the space in the Classification field name
            classification_key = ' Classification' if ' Classification' in account else 'Classification'
            info += f"Classification: {account.get(classification_key, 'N/A')}\n\n"
        
        if len(filtered_accounts) > 10:
            info += f"... and {len(filtered_accounts) - 10} more accounts."
        
        return info
    
    def get_accounts_by_management(self, management_type: str) -> str:
        """
        Get AWS accounts by management type.
        
        Args:
            management_type (str): Management type to filter by
            
        Returns:
            str: Formatted account information
        """
        accounts = self.read_csv_file()
        
        # Filter accounts by management type
        filtered_accounts = [
            account for account in accounts 
            if account['Management Type'] and account['Management Type'].lower() == management_type.lower()
        ]
        
        if not filtered_accounts:
            return f"No accounts found with management type {management_type}."
        
        # Format the response
        info = f"AWS Accounts with Management Type {management_type}:\n"
        info += f"=======================\n\n"
        info += f"Found {len(filtered_accounts)} accounts:\n\n"
        
        for account in filtered_accounts[:10]:  # Limit to first 10 accounts
            info += f"Account Number: {account['AWS Account Number']} (read as: {account['account_number_reading']})\n"
            info += f"Account Name: {account['AWS account Name']}\n"
            # Handle the space in the Classification field name
            classification_key = ' Classification' if ' Classification' in account else 'Classification'
            info += f"Classification: {account.get(classification_key, 'N/A')}\n\n"
        
        if len(filtered_accounts) > 10:
            info += f"... and {len(filtered_accounts) - 10} more accounts."
        
        return info
    
    def get_total_cost(self) -> str:
        """
        Get total cost of all AWS accounts.
        
        Returns:
            str: Formatted cost information
        """
        accounts = self.read_csv_file()
        
        # Calculate total cost
        total_cost = sum(float(account['Total Cost in Indian Rupees']) for account in accounts if account['Total Cost in Indian Rupees'])
        
        # Format the response
        info = f"Total Cost of AWS Accounts:\n"
        info += f"=======================\n\n"
        info += f"The total cost of all AWS accounts is {total_cost} Indian Rupees."
        
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
            accounts = self.read_csv_file()
            
            # Format the response
            info = f"AWS Account Information:\n"
            info += f"=======================\n\n"
            info += f"Found {len(accounts)} AWS accounts:\n\n"
            
            for account in accounts[:10]:  # Limit to first 10 accounts
                info += f"Account Number: {account['AWS Account Number']} (read as: {account['account_number_reading']})\n"
                info += f"Account Name: {account['AWS account Name']}\n"
                info += f"Status: {account['Active / Suspended']}\n"
                # Handle the space in the Classification field name
                classification_key = ' Classification' if ' Classification' in account else 'Classification'
                info += f"Classification: {account.get(classification_key, 'N/A')}\n\n"
            
            if len(accounts) > 10:
                info += f"... and {len(accounts) - 10} more accounts."
            
            return info

# Example usage
if __name__ == "__main__":
    retriever = AWSAccountRetriever()
    print(retriever.get_formatted_account_info())