import boto3
import os
import sys
import json

def test_kb_retrieval(kb_id="KCZTEHHZFA", query="What are the AWS account policies?"):
    """
    Test retrieving information from a Bedrock knowledge base.
    
    Args:
        kb_id (str): Knowledge base ID
        query (str): Query to search for
    """
    try:
        print(f"Testing knowledge base retrieval with KB ID: {kb_id}")
        print(f"Query: {query}")
        
        # Create Bedrock agent runtime client
        bedrock_agent_runtime = boto3.client("bedrock-agent-runtime", region_name="us-east-1")
        
        # Retrieve from knowledge base
        response = bedrock_agent_runtime.retrieve(
            knowledgeBaseId=kb_id,
            retrievalQuery={
                "text": query
            },
            retrievalConfiguration={
                "vectorSearchConfiguration": {
                    "numberOfResults": 3
                }
            }
        )
        
        # Process results
        print(f"Knowledge base response received. Results: {len(response.get('retrievalResults', []))}")
        
        results = []
        for result in response.get("retrievalResults", []):
            content = result.get("content", {})
            text = content.get("text", "")
            source = result.get("location", {}).get("s3Location", {}).get("uri", "Unknown source")
            results.append(f"Source: {source}\n{text}\n")
        
        print("\n=== RESULTS ===\n")
        print("\n\n".join(results) if results else "No results found")
        
        return True
    except Exception as e:
        print(f"Error retrieving from knowledge base: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    # Get KB ID from command line or use default
    kb_id = sys.argv[1] if len(sys.argv) > 1 else "KCZTEHHZFA"
    
    # Get query from command line or use default
    query = sys.argv[2] if len(sys.argv) > 2 else "What are the AWS account policies?"
    
    # Test KB retrieval
    test_kb_retrieval(kb_id, query)
