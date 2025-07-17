import os
import sys
import json
import boto3
from pathlib import Path

# Add parent directory to path to import the integration module
sys.path.append(str(Path(__file__).parent.parent.parent.parent))
from integrate_kb_with_app import create_kb_retrieval_function

class KnowledgeBaseEnhancer:
    """
    Class to enhance the virtual banking assistant with knowledge base capabilities.
    """
    
    def __init__(self, kb_id=None, region="us-east-1", max_results=3):
        """
        Initialize the knowledge base enhancer.
        
        Args:
            kb_id (str): Knowledge base ID. If None, will try to get from environment variable.
            region (str): AWS region
            max_results (int): Maximum number of results to retrieve from the knowledge base
        """
        # Get knowledge base ID from environment variable if not provided
        self.kb_id = kb_id or os.environ.get("BEDROCK_KB_ID")
        if not self.kb_id:
            print("Warning: No knowledge base ID provided. Knowledge base enhancement will be disabled.")
            self.retrieve_from_kb = None
        else:
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
When answering questions about banking products, services, or policies, 
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

# Example of how to use this in the main application:
"""
# In main.py:

from kb_integration import KnowledgeBaseEnhancer

# Initialize the knowledge base enhancer
kb_enhancer = KnowledgeBaseEnhancer(os.environ.get("BEDROCK_KB_ID"))

# When setting up the system prompt:
system_instruction = kb_enhancer.enhance_system_prompt(Path('prompt.txt').read_text())

# When processing user input (in a hypothetical process_user_input function):
def process_user_input(user_input, context):
    # Enhance the user input with knowledge base information
    enhanced_input = kb_enhancer.enhance_user_query(user_input, context)
    
    # Use the enhanced input for the LLM
    # ...
"""

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
    kb_enhancer = KnowledgeBaseEnhancer()
    
    if not kb_enhancer.retrieve_from_kb:
        await params.result_callback({"information": "Knowledge base not configured."})
        return
    
    # Retrieve information from the knowledge base
    kb_info = kb_enhancer.retrieve_from_kb(query)
    
    if not kb_info:
        await params.result_callback({"information": "No relevant information found in the knowledge base."})
    else:
        await params.result_callback({"information": kb_info})