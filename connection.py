#!/usr/bin/env python3

from datetime import datetime, timedelta

import plaid
from plaid.api import plaid_api

from plaid.model.country_code import CountryCode

from plaid.model.transactions_get_request_options \
    import TransactionsGetRequestOptions
from plaid.model.transactions_get_request import TransactionsGetRequest

from plaid.model.accounts_get_request import AccountsGetRequest

from plaid.model.institutions_get_by_id_request \
    import InstitutionsGetByIdRequest


class Connection:
    access_tokens = {}

    def __init__(self, access_tokens, client_id, secret):
        configuration = plaid.Configuration(
            host=plaid.Environment.Development,
            api_key={
                'clientId': client_id,
                'secret': secret,
            }
        )

        api_client = plaid.ApiClient(configuration)
        self.client = plaid_api.PlaidApi(api_client)

        for token in access_tokens.split(' '):
            request = AccountsGetRequest(access_token=token)
            response = self.client.accounts_get(request)
            institution_id = response['item']['institution_id']

            request = InstitutionsGetByIdRequest(
                institution_id=institution_id,
                country_codes=[CountryCode("US")],
            )
            response = self.client.institutions_get_by_id(request)
            self.access_tokens[response['institution']['name']] = token

    # return transactions across all accounts sorted by date
    def get_transactions(self, start_date):
        # keep the end date always one ahead of the current date to retrieve
        # every transaction to date
        end_date = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        transactions = []

        for (institution, access_token) in self.access_tokens.items():
            request = TransactionsGetRequest(
                access_token=access_token,
                start_date=datetime.strptime(start_date, '%Y-%m-%d').date(),
                end_date=datetime.strptime(end_date, '%Y-%m-%d').date(),
            )
            response = self.client.transactions_get(request)
            for transaction in response['transactions']:
                temp = {
                    'amount': transaction['amount'],
                    'category': transaction['category'],
                    'date': transaction['date'],
                    'institution': institution,
                    'location': transaction['location'],
                    'merchant_name': transaction['merchant_name'],
                    'name': transaction['name'],
                }
                transactions.append(temp)

            while len(transactions) < response['total_transactions']:
                options = TransactionsGetRequestOptions()
                options.offset = len(transactions)

                request = TransactionsGetRequest(
                    access_token=access_token,
                    start_date=datetime.strptime(start_date, '%Y-%m-%d').date(),
                    end_date=datetime.strptime(end_date, '%Y-%m-%d').date(),
                    options=options
                )
                response = self.client.transactions_get(request)
                for transaction in response['transactions']:
                    temp = {
                        'amount': transaction['amount'],
                        'category': transaction['category'],
                        'date': transaction['date'],
                        'institution': institution,
                        'location': transaction['location'],
                        'merchant_name': transaction['merchant_name'],
                        'name': transaction['name'],
                    }
                    transactions.append(temp)

        # sort merged list of transactions across accounts by date
        transactions.sort(key=lambda x: x['date'])
        return transactions
