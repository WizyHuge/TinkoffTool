import database


def load_accounts():
    return database.get_all_accounts()


def save_accounts(accounts_dict):
    database.clear_accounts()
    for account_name, token in accounts_dict.items():
        database.save_account(account_name, token)


def get_account_token(account_name):
    return database.get_account_token(account_name)


def save_account_token(account_name, token):
    database.save_account(account_name, token)


def delete_account(account_name):
    database.delete_account(account_name)

