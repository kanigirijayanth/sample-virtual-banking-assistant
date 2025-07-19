# AWS Account Retrieval Functionality

This document explains how to use the enhanced AWS account retrieval functionality that has been integrated into the Virtual Banking Assistant.

## Overview

The account retrieval functionality allows the assistant to:

1. Retrieve comprehensive information about AWS accounts from multiple sources:
   - AWS Bedrock Knowledge Base
   - S3 bucket data (Excel files and PDFs)
   - Local cached data

2. Support two main operations:
   - List all AWS accounts with detailed information
   - Look up specific account information by account ID or name

## Setup

1. Run the setup script to install required dependencies:

```bash
./setup.sh
```

2. Ensure AWS credentials are properly configured with access to:
   - AWS Bedrock Knowledge Base (ID: 40KPMEUSQC)
   - S3 bucket (aws-workshop-july17-blr)

## Testing

You can test the account retrieval functionality using the provided test script:

```bash
# Test retrieving all accounts
python test_account_retriever.py

# Test retrieving a specific account
python test_account_retriever.py 100942612345
```

## Integration with the Virtual Banking Assistant

The account retrieval functionality is integrated into the Virtual Banking Assistant through two main functions:

1. `get_account_info(account_id)`: Retrieves information about a specific AWS account
2. `list_accounts()`: Lists all AWS accounts with their details

These functions are available as tools for the assistant to use when responding to user queries about AWS accounts.

## How It Works

1. When a user asks about AWS accounts, the assistant will use the appropriate function.
2. The function will first try to retrieve information from the AWS Bedrock Knowledge Base.
3. If that fails or returns limited information, it will try to retrieve information from S3 data sources.
4. If S3 access fails, it will fall back to locally cached account data.
5. The retrieved information is formatted and returned to the user.

## Data Sources

The account retrieval functionality uses the following data sources:

1. AWS Bedrock Knowledge Base (ID: 40KPMEUSQC)
2. S3 bucket (aws-workshop-july17-blr) containing:
   - Excel files with account information
   - PDF files with account information
3. Local cached data in `data/combined_accounts.json`

## Troubleshooting

If you encounter issues with the account retrieval functionality:

1. Check AWS credentials and permissions
2. Verify the Knowledge Base ID is correct
3. Ensure the S3 bucket exists and contains the expected files
4. Check that the local data file exists in the `data` directory

## Example Usage

Users can ask the assistant questions like:

- "List all AWS accounts"
- "Tell me about account 100942612345"
- "Who owns the AWS account for Infosys Central Production?"
- "What's the status of account 211125759895?"
