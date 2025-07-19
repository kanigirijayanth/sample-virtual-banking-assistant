#!/usr/bin/env python3
import boto3
import json
import re
import os
import traceback
from typing import Dict, List, Any, Optional, Set, Union

class AWSAccountRetriever:
    """
    Enhanced class to retrieve AWS account information from various sources.
    This class combines direct knowledge base queries with S3 data extraction
    for more comprehensive account information.
    """
    
    def __init__(self, kb_id: str = "40KPMEUSQC", region: str = "us-east-1", 
                 s3_bucket: str = "aws-workshop-july17-blr"):
        """
        Initialize the AWS Account Retriever.
        
        Args:
            kb_id (str): Knowledge base ID
            region (str): AWS region
            s3_bucket (str): S3 bucket containing account data
        """
        self.kb_id = kb_id
        self.region = region
        self.s3_bucket = s3_bucket
        self.bedrock_client = None
        self.s3_client = None
        
        try:
            self.bedrock_client = boto3.client("bedrock-agent-runtime", region_name=region)
            self.s3_client = boto3.client("s3", region_name=region)
            print(f"Initialized AWSAccountRetriever with KB ID: {kb_id}")
        except Exception as e:
            print(f"Error initializing AWS clients: {e}")
            traceback.print_exc()
    
    def extract_account_numbers(self, text: str) -> List[str]:
        """
        Extract AWS account numbers from text using regex.
        
        Args:
            text (str): Text to extract account numbers from
            
        Returns:
            List[str]: List of extracted account numbers
        """
        # Look for 12-digit numbers that might be AWS account IDs
        account_pattern = r'\b\d{12}\b'
        return re.findall(account_pattern, text)
    
    def query_knowledge_base(self, query: str, max_results: int = 10) -> str:
        """
        Query the knowledge base for information.
        
        Args:
            query (str): Query to search for
            max_results (int): Maximum number of results to return
            
        Returns:
            str: Formatted results from the knowledge base
        """
        if not self.bedrock_client:
            return "Error: Bedrock client not initialized."
        
        try:
            print(f"Querying knowledge base {self.kb_id} with: {query}")
            response = self.bedrock_client.retrieve(
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
            
            results = []
            for result in response.get("retrievalResults", []):
                content = result.get("content", {})
                text = content.get("text", "")
                source = result.get("location", {}).get("s3Location", {}).get("uri", "Unknown source")
                results.append(f"Source: {source}\n{text}")
            
            return "\n\n".join(results) if results else "No results found in the knowledge base."
            
        except Exception as e:
            print(f"Error querying knowledge base: {e}")
            traceback.print_exc()
            return f"Error querying knowledge base: {str(e)}"
    
    def get_account_info_from_kb(self, account_id: str) -> str:
        """
        Get information about a specific AWS account from the knowledge base.
        
        Args:
            account_id (str): AWS account ID or name to look up
            
        Returns:
            str: Formatted account information
        """
        query = f"information about AWS account {account_id}"
        return self.query_knowledge_base(query)
    
    def list_accounts_from_kb(self) -> Dict[str, Any]:
        """
        List all AWS accounts from the knowledge base.
        
        Returns:
            Dict[str, Any]: Dictionary with account information
        """
        query = "list all AWS account numbers and their owners"
        kb_results = self.query_knowledge_base(query)
        
        # Extract account numbers from the results
        accounts = {}
        
        # Process the text to extract account numbers and associated information
        for line in kb_results.split('\n'):
            account_numbers = self.extract_account_numbers(line)
            for account in account_numbers:
                if account not in accounts:
                    accounts[account] = {
                        "descriptions": [],
                        "sources": ["Knowledge Base"]
                    }
                
                # Add the line as a description if it's not already there
                if line.strip() and line not in accounts[account]["descriptions"]:
                    accounts[account]["descriptions"].append(line.strip())
        
        return accounts
    
    def download_s3_file(self, key: str, local_path: str) -> bool:
        """
        Download a file from S3.
        
        Args:
            key (str): S3 object key
            local_path (str): Local path to save the file
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.s3_client:
            print("Error: S3 client not initialized.")
            return False
        
        try:
            print(f"Downloading {key} from S3 bucket {self.s3_bucket}")
            self.s3_client.download_file(self.s3_bucket, key, local_path)
            return True
        except Exception as e:
            print(f"Error downloading file from S3: {e}")
            traceback.print_exc()
            return False
    
    def list_s3_objects(self) -> List[str]:
        """
        List objects in the S3 bucket.
        
        Returns:
            List[str]: List of object keys
        """
        if not self.s3_client:
            print("Error: S3 client not initialized.")
            return []
        
        try:
            response = self.s3_client.list_objects_v2(Bucket=self.s3_bucket)
            return [obj['Key'] for obj in response.get('Contents', [])]
        except Exception as e:
            print(f"Error listing S3 objects: {e}")
            traceback.print_exc()
            return []
    
    def extract_accounts_from_excel(self, excel_path: str) -> Dict[str, Any]:
        """
        Extract account information from an Excel file.
        
        Args:
            excel_path (str): Path to the Excel file
            
        Returns:
            Dict[str, Any]: Dictionary with account information
        """
        try:
            import pandas as pd
            
            # Read the Excel file
            df = pd.read_excel(excel_path)
            
            # Initialize accounts dictionary
            accounts = {}
            
            # Process each row in the dataframe
            for _, row in df.iterrows():
                # Try to get account ID from the 'AWS Account Number' column
                if 'AWS Account Number' in df.columns and pd.notna(row['AWS Account Number']):
                    account_id = str(row['AWS Account Number']).strip()
                    # Clean up the account ID - remove any non-digit characters
                    account_id = re.sub(r'\D', '', account_id)
                    
                    # Check if it looks like an AWS account ID (12 digits)
                    if len(account_id) == 12:
                        if account_id not in accounts:
                            accounts[account_id] = {"descriptions": [], "sources": [excel_path]}
                        
                        # Create a description with key information
                        description = {}
                        for col in df.columns:
                            if pd.notna(row[col]) and str(row[col]).strip() and str(row[col]).strip() != 'nan':
                                description[col] = str(row[col]).strip()
                        
                        accounts[account_id]["descriptions"].append(description)
                
                # Check all cells for 12-digit numbers that might be account IDs
                for col in df.columns:
                    if pd.notna(row[col]):
                        cell_value = str(row[col])
                        account_matches = self.extract_account_numbers(cell_value)
                        
                        for account_id in account_matches:
                            # Skip if it's the same as the AWS Account Number column to avoid duplicates
                            if 'AWS Account Number' in df.columns and pd.notna(row['AWS Account Number']) and str(row['AWS Account Number']).strip() == account_id:
                                continue
                                
                            if account_id not in accounts:
                                accounts[account_id] = {"descriptions": [], "sources": [f"{excel_path} (found in cell)"]}
                            
                            # Create a description with key information
                            description = {}
                            for c in df.columns:
                                if pd.notna(row[c]) and str(row[c]).strip() and str(row[c]).strip() != 'nan':
                                    description[c] = str(row[c]).strip()
                            
                            # Add which cell contained this account ID
                            description["Found in column"] = col
                            
                            accounts[account_id]["descriptions"].append(description)
            
            return accounts
        except Exception as e:
            print(f"Error extracting accounts from Excel: {e}")
            traceback.print_exc()
            return {}
    
    def extract_accounts_from_pdf(self, pdf_path: str) -> Dict[str, Any]:
        """
        Extract account information from a PDF file.
        
        Args:
            pdf_path (str): Path to the PDF file
            
        Returns:
            Dict[str, Any]: Dictionary with account information
        """
        try:
            import PyPDF2
            
            # Open the PDF file
            with open(pdf_path, 'rb') as file:
                # Create a PDF reader object
                pdf_reader = PyPDF2.PdfReader(file)
                
                # Initialize accounts dictionary
                accounts = {}
                
                # Extract text from each page
                for page_num in range(len(pdf_reader.pages)):
                    page = pdf_reader.pages[page_num]
                    text = page.extract_text()
                    
                    # Look for 12-digit numbers that might be AWS account IDs
                    account_matches = self.extract_account_numbers(text)
                    
                    # Also look for account IDs in the format xxxx-xxxx-xxxx
                    hyphenated_matches = re.findall(r'\b\d{4}-\d{4}-\d{4}\b', text)
                    for match in hyphenated_matches:
                        # Convert to 12-digit format by removing hyphens
                        account_id = match.replace('-', '')
                        account_matches.append(account_id)
                    
                    # Look for "Account ID:" followed by any format
                    account_id_matches = re.findall(r'Account ID:[\s]*([\w\d\-]+)', text)
                    for match in account_id_matches:
                        # Clean up the ID - remove any non-digit characters
                        account_id = re.sub(r'\D', '', match)
                        if len(account_id) == 12:
                            account_matches.append(account_id)
                    
                    for account_id in account_matches:
                        if account_id not in accounts:
                            accounts[account_id] = {"descriptions": [], "sources": [f"{pdf_path} (page {page_num + 1})"]}
                        
                        # Try to find context around the account ID
                        lines = text.split('\n')
                        context = []
                        for i, line in enumerate(lines):
                            # Check for the account ID or its hyphenated form
                            if account_id in line or account_id[:4] + '-' + account_id[4:8] + '-' + account_id[8:12] in line:
                                # Add the line and surrounding lines for context
                                start = max(0, i - 2)
                                end = min(len(lines), i + 3)
                                for j in range(start, end):
                                    if lines[j].strip() and lines[j].strip() not in context:
                                        context.append(lines[j].strip())
                        
                        if context and context not in accounts[account_id]["descriptions"]:
                            accounts[account_id]["descriptions"].append(context)
                
                return accounts
        except Exception as e:
            print(f"Error extracting accounts from PDF: {e}")
            traceback.print_exc()
            return {}
    
    def get_all_accounts(self) -> Dict[str, Any]:
        """
        Get all AWS accounts from all available sources.
        
        Returns:
            Dict[str, Any]: Dictionary with account information
        """
        # Initialize combined accounts dictionary
        combined_accounts = {}
        
        # First try to get accounts from the knowledge base
        kb_accounts = self.list_accounts_from_kb()
        for account_id, info in kb_accounts.items():
            combined_accounts[account_id] = info
        
        # Try to get accounts from S3 files
        try:
            # Create a temporary directory for downloaded files
            import tempfile
            import os
            
            temp_dir = tempfile.mkdtemp()
            
            # List S3 objects
            s3_objects = self.list_s3_objects()
            
            # Look for Excel and PDF files
            for obj_key in s3_objects:
                local_path = os.path.join(temp_dir, os.path.basename(obj_key))
                
                if obj_key.endswith('.xlsx') or obj_key.endswith('.xls'):
                    # Download and process Excel file
                    if self.download_s3_file(obj_key, local_path):
                        try:
                            excel_accounts = self.extract_accounts_from_excel(local_path)
                            
                            # Merge with combined accounts
                            for account_id, info in excel_accounts.items():
                                if account_id in combined_accounts:
                                    # Account exists in both sources, merge the information
                                    combined_accounts[account_id]["sources"].extend(info["sources"])
                                    combined_accounts[account_id]["descriptions"].extend(info["descriptions"])
                                else:
                                    # Account only exists in Excel
                                    combined_accounts[account_id] = info
                        except Exception as e:
                            print(f"Error processing Excel file {obj_key}: {e}")
                
                elif obj_key.endswith('.pdf'):
                    # Download and process PDF file
                    if self.download_s3_file(obj_key, local_path):
                        try:
                            pdf_accounts = self.extract_accounts_from_pdf(local_path)
                            
                            # Merge with combined accounts
                            for account_id, info in pdf_accounts.items():
                                if account_id in combined_accounts:
                                    # Account exists in both sources, merge the information
                                    combined_accounts[account_id]["sources"].extend(info["sources"])
                                    combined_accounts[account_id]["descriptions"].extend(info["descriptions"])
                                else:
                                    # Account only exists in PDF
                                    combined_accounts[account_id] = info
                        except Exception as e:
                            print(f"Error processing PDF file {obj_key}: {e}")
        except Exception as e:
            print(f"Error processing S3 files: {e}")
            traceback.print_exc()
        
        # If no accounts found or there was an error, try to load from local file
        if not combined_accounts:
            try:
                local_data_path = os.path.join(os.path.dirname(__file__), 'data', 'combined_accounts.json')
                if os.path.exists(local_data_path):
                    print(f"Loading account data from local file: {local_data_path}")
                    with open(local_data_path, 'r') as f:
                        combined_accounts = json.load(f)
                    print(f"Loaded {len(combined_accounts)} accounts from local file")
            except Exception as e:
                print(f"Error loading local account data: {e}")
                traceback.print_exc()
        
        return combined_accounts
    
    def format_account_info(self, accounts: Dict[str, Any]) -> str:
        """
        Format account information for display.
        
        Args:
            accounts (Dict[str, Any]): Dictionary with account information
            
        Returns:
            str: Formatted account information
        """
        if not accounts:
            return "No account information found."
        
        formatted_info = "AWS Account Information:\n"
        formatted_info += "=======================\n\n"
        
        for account_id, info in accounts.items():
            formatted_info += f"Account: {account_id}\n"
            formatted_info += "-" * 50 + "\n"
            
            # Extract key information
            account_names = set()
            owners = set()
            status = set()
            classes = set()
            provisioning_dates = set()
            management_types = set()
            
            for desc in info.get("descriptions", []):
                if isinstance(desc, dict):
                    # From Excel
                    if "AWS account Name(AWS Console)" in desc:
                        account_names.add(desc["AWS account Name(AWS Console)"])
                    if "AWS account Name(Cloud Health)" in desc and desc["AWS account Name(Cloud Health)"] != account_id:
                        account_names.add(desc["AWS account Name(Cloud Health)"])
                    if "Account Owner Email ID" in desc:
                        owners.add(desc["Account Owner Email ID"])
                    if "751362898289Active / Suspended /" in desc:
                        status.add(desc["751362898289Active / Suspended /"])
                    if "Class" in desc:
                        classes.add(desc["Class"])
                    if "Account Provisioning Date" in desc:
                        provisioning_dates.add(desc["Account Provisioning Date"])
                    if "Self-Service\u00a0/ Managed" in desc:
                        management_types.add(desc["Self-Service\u00a0/ Managed"])
                elif isinstance(desc, list):
                    # From PDF
                    for line in desc:
                        if "Account Name:" in line:
                            account_names.add(line.split("Account Name:")[1].strip())
                        if "Owner:" in line:
                            owners.add(line.split("Owner:")[1].strip())
            
            # Add account names
            if account_names:
                formatted_info += "Account Names:\n"
                for name in account_names:
                    formatted_info += f"  - {name}\n"
            
            # Add owners
            if owners:
                formatted_info += "Account Owners:\n"
                for owner in owners:
                    formatted_info += f"  - {owner}\n"
            
            # Add status
            if status:
                formatted_info += "Account Status:\n"
                for s in status:
                    formatted_info += f"  - {s}\n"
            
            # Add provisioning dates
            if provisioning_dates:
                formatted_info += "Provisioning Dates:\n"
                for date in provisioning_dates:
                    formatted_info += f"  - {date}\n"
            
            # Add management types
            if management_types:
                formatted_info += "Management Type:\n"
                for mtype in management_types:
                    formatted_info += f"  - {mtype}\n"
            
            # Add classes
            if classes:
                formatted_info += "Class:\n"
                for c in classes:
                    formatted_info += f"  - {c}\n"
            
            # Add sources
            if "sources" in info and info["sources"]:
                formatted_info += "Sources:\n"
                for source in info["sources"]:
                    formatted_info += f"  - {source}\n"
            
            formatted_info += "\n"
        
        return formatted_info
    
    def get_formatted_account_info(self, account_id: Optional[str] = None) -> str:
        """
        Get formatted account information for a specific account or all accounts.
        
        Args:
            account_id (Optional[str]): AWS account ID to look up. If None, returns all accounts.
            
        Returns:
            str: Formatted account information
        """
        if account_id:
            # First try the knowledge base
            kb_info = self.get_account_info_from_kb(account_id)
            
            # Then try to get more detailed information from S3 files
            all_accounts = self.get_all_accounts()
            
            if account_id in all_accounts:
                account_info = {account_id: all_accounts[account_id]}
                formatted_info = self.format_account_info(account_info)
                
                # Add knowledge base information if available
                if kb_info and kb_info != "No results found in the knowledge base.":
                    formatted_info += "\nAdditional Information from Knowledge Base:\n"
                    formatted_info += "=" * 50 + "\n"
                    formatted_info += kb_info
                
                return formatted_info
            else:
                # If not found in S3 files, return knowledge base information
                if kb_info and kb_info != "No results found in the knowledge base.":
                    return f"Account Information for {account_id}:\n\n{kb_info}"
                else:
                    return f"No information found for AWS account {account_id}."
        else:
            # Get all accounts
            all_accounts = self.get_all_accounts()
            return self.format_account_info(all_accounts)


# Example usage
if __name__ == "__main__":
    retriever = AWSAccountRetriever()
    print(retriever.get_formatted_account_info())
