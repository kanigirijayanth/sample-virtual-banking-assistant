"""
AWS Account Functions for Virtual Assistant Integration

This module provides functions for retrieving AWS account information
that can be integrated with the virtual assistant.
"""

from aws_account_retriever import AWSAccountRetriever

# Initialize the account retriever with absolute path
import os
# Use the CSV file at the root directory as that's where we're copying it in the Dockerfile
csv_path = "/AWS_AccountDetails.csv"
print(f"Using CSV file at: {csv_path}")
retriever = AWSAccountRetriever(csv_path)

async def get_account_info(params):
    """
    Get information about a specific AWS account
    
    Args:
        params: Function call parameters with account_id in arguments
    """
    account_id = params.arguments.get("account_id", "")
    
    if not account_id:
        await params.result_callback({
            "message": "Please provide an AWS account ID or name to look up."
        })
        return
    
    try:
        # Get account information from CSV
        info = retriever.get_account_info(account_id)
        
        await params.result_callback({
            "account_id": account_id,
            "information": info
        })
    except Exception as e:
        await params.result_callback({
            "message": f"Error retrieving account information: {str(e)}"
        })

async def list_accounts(params):
    """
    List all AWS accounts
    
    Args:
        params: Function call parameters
    """
    try:
        # Get all accounts from CSV
        info = retriever.get_formatted_account_info()
        
        await params.result_callback({
            "accounts": info
        })
    except Exception as e:
        await params.result_callback({
            "message": f"Error retrieving account information: {str(e)}"
        })

async def get_accounts_by_classification(params):
    """
    Get AWS accounts by classification
    
    Args:
        params: Function call parameters with classification in arguments
    """
    classification = params.arguments.get("classification", "")
    
    if not classification:
        await params.result_callback({
            "message": "Please provide a classification to look up."
        })
        return
    
    try:
        # Get accounts by classification from CSV
        info = retriever.get_accounts_by_classification(classification)
        
        await params.result_callback({
            "classification": classification,
            "accounts": info
        })
    except Exception as e:
        await params.result_callback({
            "message": f"Error retrieving account information: {str(e)}"
        })

async def get_accounts_by_status(params):
    """
    Get AWS accounts by status
    
    Args:
        params: Function call parameters with status in arguments
    """
    status = params.arguments.get("status", "")
    
    if not status:
        await params.result_callback({
            "message": "Please provide a status (ACTIVE or SUSPENDED) to look up."
        })
        return
    
    try:
        # Get accounts by status from CSV
        info = retriever.get_accounts_by_status(status)
        
        await params.result_callback({
            "status": status,
            "accounts": info
        })
    except Exception as e:
        await params.result_callback({
            "message": f"Error retrieving account information: {str(e)}"
        })

async def get_total_cost(params):
    """
    Get total cost of all AWS accounts
    
    Args:
        params: Function call parameters
    """
    try:
        # Get total cost from CSV
        info = retriever.get_total_cost()
        
        await params.result_callback({
            "total_cost": info
        })
    except Exception as e:
        await params.result_callback({
            "message": f"Error retrieving cost information: {str(e)}"
        })

async def get_account_provisioning_date(params):
    """
    Get provisioning date for a specific AWS account
    
    Args:
        params: Function call parameters with account_id in arguments
    """
    account_id = params.arguments.get("account_id", "")
    
    if not account_id:
        await params.result_callback({
            "message": "Please provide an AWS account ID or name to look up."
        })
        return
    
    try:
        # Get account provisioning date from CSV
        info = retriever.get_account_provisioning_date(account_id)
        
        await params.result_callback({
            "account_id": account_id,
            "information": info
        })
    except Exception as e:
        await params.result_callback({
            "message": f"Error retrieving account provisioning date: {str(e)}"
        })

async def get_accounts_by_year(params):
    """
    Get number of AWS accounts provisioned in a specific year
    
    Args:
        params: Function call parameters with year in arguments
    """
    year = params.arguments.get("year", "")
    
    if not year:
        await params.result_callback({
            "message": "Please provide a year to look up accounts provisioned in that year."
        })
        return
    
    try:
        # Get accounts by year from CSV
        info = retriever.get_accounts_by_year(year)
        
        await params.result_callback({
            "year": year,
            "information": info
        })
    except Exception as e:
        await params.result_callback({
            "message": f"Error retrieving accounts by year: {str(e)}"
        })

# Example of how to register these functions with the virtual assistant
"""
# In main.py:

from account_functions import get_account_info, list_accounts, get_accounts_by_classification, get_accounts_by_status, get_total_cost, get_account_provisioning_date, get_accounts_by_year

# Create function schemas
account_function = FunctionSchema(
    name="get_account_info",
    description="Get information about an AWS account.",
    properties={
        "account_id": {
            "type": "string",
            "description": "The AWS account ID or name to look up information for.",
        }
    },
    required=["account_id"],
)

list_accounts_function = FunctionSchema(
    name="list_accounts",
    description="List all AWS accounts.",
    properties={},
    required=[],
)

classification_function = FunctionSchema(
    name="get_accounts_by_classification",
    description="Get AWS accounts by classification.",
    properties={
        "classification": {
            "type": "string",
            "description": "The classification to filter accounts by (e.g., Class-1, Class-2, Class-3).",
        }
    },
    required=["classification"],
)

status_function = FunctionSchema(
    name="get_accounts_by_status",
    description="Get AWS accounts by status.",
    properties={
        "status": {
            "type": "string",
            "description": "The status to filter accounts by (ACTIVE or SUSPENDED).",
        }
    },
    required=["status"],
)

cost_function = FunctionSchema(
    name="get_total_cost",
    description="Get total cost of all AWS accounts.",
    properties={},
    required=[],
)

provisioning_date_function = FunctionSchema(
    name="get_account_provisioning_date",
    description="Get provisioning date for a specific AWS account.",
    properties={
        "account_id": {
            "type": "string",
            "description": "The AWS account ID or name to look up provisioning date for.",
        }
    },
    required=["account_id"],
)

accounts_by_year_function = FunctionSchema(
    name="get_accounts_by_year",
    description="Get number of AWS accounts provisioned in a specific year.",
    properties={
        "year": {
            "type": "string",
            "description": "The year to filter accounts by (e.g., '2019').",
        }
    },
    required=["year"],
)

# Add to tools schema
tools = ToolsSchema(standard_tools=[
    account_function, 
    list_accounts_function, 
    classification_function,
    status_function,
    cost_function,
    provisioning_date_function,
    accounts_by_year_function
])

# Register functions
llm.register_function("get_account_info", get_account_info)
llm.register_function("list_accounts", list_accounts)
llm.register_function("get_accounts_by_classification", get_accounts_by_classification)
llm.register_function("get_accounts_by_status", get_accounts_by_status)
llm.register_function("get_total_cost", get_total_cost)
llm.register_function("get_account_provisioning_date", get_account_provisioning_date)
llm.register_function("get_accounts_by_year", get_accounts_by_year)
"""