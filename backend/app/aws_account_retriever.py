#!/usr/bin/env python3
import boto3
import json
import re
import os
import traceback
from typing import Dict, List, Any, Optional, Set, Union

class AWSAccountRetriever:
    """
    Class to retrieve AWS account information using Bedrock knowledge base and Nova Lite.
    """
    
    def __init__(self, kb_id: str = "KCZTEHHZFA", region: str = "us-east-1"):
        """
        Initialize the AWS Account Retriever.
        
        Args:
            kb_id (str): Knowledge base ID
            region (str): AWS region
        """
        self.kb_id = kb_id
        self.region = region
        self.bedrock_client = None
        self.bedrock_runtime_client = None
        
        try:
            self.bedrock_client = boto3.client("bedrock-agent-runtime", region_name=region)
            self.bedrock_runtime_client = boto3.client("bedrock-runtime", region_name=region)
            print(f"Initialized AWSAccountRetriever with KB ID: {kb_id}")
        except Exception as e:
            print(f"Error initializing AWS clients: {e}")
            traceback.print_exc()
    
    def query_knowledge_base(self, query: str, max_results: int = 5) -> str:
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
    
    def query_nova_lite(self, query: str, context: str) -> str:
        """
        Query Nova Lite (Claude 3 Sonnet) with context from the knowledge base.
        
        Args:
            query (str): User query
            context (str): Context from the knowledge base
            
        Returns:
            str: Response from Nova Lite
        """
        if not self.bedrock_runtime_client:
            return "Error: Bedrock runtime client not initialized."
        
        try:
            print(f"Querying Nova Lite with: {query}")
            
            # Prepare the prompt for Nova Lite
            prompt = f"""You are a helpful assistant that provides information about AWS accounts.
            
            Context from knowledge base:
            {context}
            
            User query: {query}
            
            Please provide a helpful response based on the context. If the information is not in the context, say so.
            """
            
            # Invoke Nova Lite
            response = self.bedrock_runtime_client.invoke_model(
                modelId="amazon.nova-lite-v1:0",
                contentType="application/json",
                accept="application/json",
                body=json.dumps({
                    "messages": [
                        {"role": "user", "content": [{"text": prompt}]}
                    ]
                })
            )
            
            response_body = json.loads(response["body"].read().decode())
            return response_body["output"]["message"]["content"][0]["text"]
            
        except Exception as e:
            print(f"Error querying Nova Lite: {e}")
            traceback.print_exc()
            
            # Fall back to just returning the context
            return f"I found the following information:\n\n{context}"
    
    def get_account_info(self, account_id: str) -> str:
        """
        Get information about a specific AWS account.
        
        Args:
            account_id (str): AWS account ID or name to look up
            
        Returns:
            str: Formatted account information
        """
        # Query the knowledge base for account information
        query = f"information about AWS account {account_id}"
        kb_results = self.query_knowledge_base(query)
        
        # Try to use Nova Lite to generate a response
        try:
            return self.query_nova_lite(query, kb_results)
        except Exception as e:
            print(f"Error using Nova Lite: {e}")
            # Fall back to just returning the knowledge base results
            return self.format_account_info(kb_results)
    
    def format_account_info(self, kb_info: str) -> str:
        """
        Format account information for display.
        
        Args:
            kb_info (str): Knowledge base information
            
        Returns:
            str: Formatted account information
        """
        if not kb_info or kb_info == "No results found in the knowledge base.":
            return "No account information found."
        
        # Extract account information from the knowledge base results
        formatted_info = "AWS Account Information:\n"
        formatted_info += "=======================\n\n"
        
        # Add the knowledge base information
        formatted_info += kb_info
        
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
            # Get information about a specific account
            return self.get_account_info(account_id)
        else:
            # Get information about all accounts
            query = "list all AWS account numbers and their owners"
            kb_results = self.query_knowledge_base(query)
            
            # Try to use Nova Lite to generate a response
            try:
                return self.query_nova_lite(query, kb_results)
            except Exception as e:
                print(f"Error using Nova Lite: {e}")
                # Fall back to just returning the knowledge base results
                return self.format_account_info(kb_results)


# Example usage
if __name__ == "__main__":
    retriever = AWSAccountRetriever()
    print(retriever.get_formatted_account_info())
