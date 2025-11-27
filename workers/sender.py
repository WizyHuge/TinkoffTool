import requests

def send_signal(message, telegram_token, telegram_chat_id):
    if not telegram_token or not telegram_chat_id:
        return False
    
    try:
        url = f"https://api.telegram.org/bot{telegram_token}/sendMessage"
        payload = {'chat_id': telegram_chat_id, 'text': message, 'parse_mode': 'HTML'}
        return requests.post(url, json=payload, timeout=10).status_code == 200
    except Exception:
        return False