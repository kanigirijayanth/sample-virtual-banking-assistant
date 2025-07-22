import boto3
import os

def fetch_aws_accounts():
    """
    Fetch list of AWS account numbers from Knowledge Base
    """
    try:
        # Initialize Bedrock agent runtime client
        bedrock_agent_runtime = boto3.client("bedrock-agent-runtime", region_name="us-east-1")
        
        # Query the knowledge base for account numbers
        response = bedrock_agent_runtime.retrieve(
            knowledgeBaseId="40KPMEUSQC",
            retrievalQuery={
                "text": "list all AWS account numbers"
            },
            retrievalConfiguration={
                "vectorSearchConfiguration": {
                    "numberOfResults": 10
                }
            }
        )
        
        # Process results
        print("Knowledge Base Results:")
        print("======================")
        
        for i, result in enumerate(response.get("retrievalResults", [])):
            content = result.get("content", {})
            text = content.get("text", "")
            source = result.get("location", {}).get("s3Location", {}).get("uri", "Unknown source")
            
            print(f"\nResult {i+1}:")
            print(f"Source: {source}")
            print(f"Content: {text}")
            
        return response.get("retrievalResults", [])
            
    except Exception as e:
        print(f"Error retrieving from knowledge base: {e}")
        import traceback
        traceback.print_exc()
        return []

if __name__ == "__main__":
    fetch_aws_accounts()