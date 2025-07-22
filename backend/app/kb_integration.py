import os
import sys
import json
import boto3
import traceback
from pathlib import Path

# Define the KB retrieval function directly
def create_kb_retrieval_function(kb_id, region="us-east-1"):
    """
    Create a function that retrieves information from a Bedrock knowledge base.
    
    Args:
        kb_id (str): Knowledge base ID
        region (str): AWS region
        
    Returns:
        function: A function that takes a query and returns knowledge base results
    """
    bedrock_agent_runtime = boto3.client("bedrock-agent-runtime", region_name=region)
    
    def retrieve_from_kb(query, max_results=3):
        try:
            print(f"Querying knowledge base {kb_id} with: {query}")
            response = bedrock_agent_runtime.retrieve(
                knowledgeBaseId=kb_id,
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
                source = result.get("location", {}).get("s3Location", {}).get("uri", "Unknown source")
                results.append(f"Source: {source}\n{text}\n")
            
            return "\n\n".join(results) if results else ""
        except Exception as e:
            print(f"Error retrieving from knowledge base: {e}")
            traceback.print_exc()
            return ""
    
    return retrieve_from_kb

class KnowledgeBaseEnhancer:
    """
    Class to enhance the virtual banking assistant with knowledge base capabilities.
    """
    
    def __init__(self, kb_id="KCZTEHHZFA", region="us-east-1", max_results=3):
        """
        Initialize the knowledge base enhancer.
        
        Args:
            kb_id (str): Knowledge base ID
            region (str): AWS region
            max_results (int): Maximum number of results to retrieve from the knowledge base
        """
        # Use specific knowledge base ID
        self.kb_id = kb_id
        # Create the retrieval function
        self.retrieve_from_kb = create_kb_retrieval_function(self.kb_id, region)
        
        self.max_results = max_results
    
    def enhance_system_prompt(self, original_prompt):
        """
        Enhance the system prompt with instructions for using the knowledge base.
        
        Args:
            original_prompt (str): The original system prompt
            
        Returns:
            str: Enhanced system prompt
        """
        kb_instructions = """
When answering questions about AWS accounts, account owners, or cloud operations, 
I will use information from the knowledge base when available.
If I retrieve information from the knowledge base, I will cite the source.
"""
        return original_prompt + kb_instructions
    
    def enhance_user_query(self, user_query, context):
        """
        Enhance the user query with relevant information from the knowledge base.
        
        Args:
            user_query (str): The user's query
            context (object): The conversation context
            
        Returns:
            str: Enhanced user query with knowledge base information if available
        """
        if not self.retrieve_from_kb:
            return user_query
        
        # Retrieve information from the knowledge base
        kb_info = self.retrieve_from_kb(user_query, self.max_results)
        
        if not kb_info:
            return user_query
        
        # Enhance the user query with knowledge base information
        enhanced_query = f"""
{user_query}

[Knowledge Base Information]
{kb_info}

Please use the above knowledge base information if relevant to answer my question.
"""
        return enhanced_query

# Function that can be used with the existing function call mechanism
async def get_kb_information(params):
    """
    Function to retrieve information from the knowledge base.
    Can be registered as a function for the LLM to call.
    
    Args:
        params: Function call parameters with query in arguments
    """
    query = params.arguments.get("query", "")
    
    if not query:
        await params.result_callback({"information": "No query provided."})
        return
    
    # Initialize the knowledge base enhancer
    kb_enhancer = KnowledgeBaseEnhancer(kb_id="KCZTEHHZFA")
    
    if not kb_enhancer.retrieve_from_kb:
        await params.result_callback({"information": "Knowledge base not configured."})
        return
    
    # Retrieve information from the knowledge base
    kb_info = kb_enhancer.retrieve_from_kb(query)
    
    if not kb_info:
        await params.result_callback({"information": "No relevant information found in the knowledge base."})
    else:
        await params.result_callback({"information": kb_info})
