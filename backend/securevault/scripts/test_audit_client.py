import requests
import json

LOGIN_URL = 'http://127.0.0.1:5000/api/login'
AUDIT_URL = 'http://127.0.0.1:5000/api/audit'

def main():
    login_payload = {'email': 'admin@cloudopt.ai', 'password': 'securepassword123'}
    r = requests.post(LOGIN_URL, json=login_payload)
    print('LOGIN', r.status_code)
    try:
        print(r.json())
    except Exception:
        print(r.text)

    token = None
    try:
        token = r.json().get('token')
    except Exception:
        pass

    headers = {}
    if token:
        headers['Authorization'] = f'Bearer {token}'

    payload = {'repoUrl': 'https://github.com/AnirudhSGopal/repolearner'}
    print('\nPOST /api/audit ->', AUDIT_URL)
    r2 = requests.post(AUDIT_URL, json=payload, headers=headers, timeout=120)
    print('AUDIT', r2.status_code)
    try:
        print(json.dumps(r2.json(), indent=2))
    except Exception:
        print(r2.text)

if __name__ == '__main__':
    main()
