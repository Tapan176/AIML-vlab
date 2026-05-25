import json
from google_auth_oauthlib.flow import InstalledAppFlow
from config import GOOGLE_CREDENTIALS_PATH, GOOGLE_CREDENTIALS_JSON, GOOGLE_TOKEN_PATH


SCOPES = ['https://www.googleapis.com/auth/drive.file']


def generate_token():
    print("\n==================================")
    print("Drive Token Generator")
    print("==================================\n")
    print("This script will help you generate a new Google Drive token.")
    print("It will open a browser window for you to authenticate.")

    creds = None

    if GOOGLE_CREDENTIALS_JSON:
        print("[*] Found GOOGLE_CREDENTIALS_JSON in .env! Using this...")
        try:
            client_config = json.loads(GOOGLE_CREDENTIALS_JSON)
            flow = InstalledAppFlow.from_client_config(client_config, SCOPES)
            creds = flow.run_local_server(port=0)
        except Exception as e:
            print(f"[!] Failed to process GOOGLE_CREDENTIALS_JSON: {e}")
    elif GOOGLE_CREDENTIALS_PATH:
        import os
        if os.path.exists(GOOGLE_CREDENTIALS_PATH):
            print(f"[*] Found local credentials file at {GOOGLE_CREDENTIALS_PATH}! Using this...")
            try:
                flow = InstalledAppFlow.from_client_secrets_file(GOOGLE_CREDENTIALS_PATH, SCOPES)
                creds = flow.run_local_server(port=0)
            except Exception as e:
                print(f"[!] Failed to process local credentials from file: {e}")
        else:
            print(f"[!] ERROR: No client secrets found in GOOGLE_CREDENTIALS_JSON or {GOOGLE_CREDENTIALS_PATH}.")
            print("Please ensure you have configured your Google Client Secrets.")
            return

    if creds and creds.valid:
        print("\n==================================")
        print("SUCCESS! Here is your new Token:")
        print("==================================\n")
        print("Copy the following JSON string and replace the old GOOGLE_TOKEN_JSON value in backend/.env:")
        print("\nGOOGLE_TOKEN_JSON='" + creds.to_json() + "'\n")

        with open(GOOGLE_TOKEN_PATH, 'w') as f:
            f.write(creds.to_json())
        print(f"Token also saved locally to {GOOGLE_TOKEN_PATH}")
        print("\nDon't forget to restart your docker containers (docker-compose down && docker-compose up -d) so they pick up the new token!")
    else:
        print("\n[!] Authentication failed.")


if __name__ == '__main__':
    generate_token()
