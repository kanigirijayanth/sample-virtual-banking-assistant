#!/usr/bin/env python3
import asyncio
from main import list_accounts

class MockParams:
    def __init__(self):
        self.arguments = {}
        self.result = None
    
    async def result_callback(self, result):
        self.result = result
        print(f"Result received: {result.keys()}")
        if "accounts" in result:
            accounts_info = result["accounts"]
            print(f"Accounts info length: {len(accounts_info) if isinstance(accounts_info, str) else 'Not a string'}")
            print(f"First 200 characters: {accounts_info[:200] if isinstance(accounts_info, str) else 'Not a string'}")

async def test_list_accounts_function():
    params = MockParams()
    await list_accounts(params)
    
    if params.result:
        print("Function completed successfully")
    else:
        print("Function did not return a result")

if __name__ == "__main__":
    asyncio.run(test_list_accounts_function())
