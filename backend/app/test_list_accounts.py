#!/usr/bin/env python3
from aws_account_retriever import AWSAccountRetriever

def test_list_accounts():
    retriever = AWSAccountRetriever()
    accounts = retriever.get_all_accounts()
    print(f'Found {len(accounts)} accounts')
    print('First 5 accounts:')
    for i, (account_id, info) in enumerate(list(accounts.items())[:5]):
        print(f'{account_id}: {info.get("sources", ["Unknown"])[0]}')

if __name__ == "__main__":
    test_list_accounts()
