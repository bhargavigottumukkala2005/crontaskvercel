import requests
import json
import base64
import os
from flask import Flask
 
app = Flask(__name__)

CLIENT_ID = 'iZ6BVr8SIeWdQPNE9bz9Q'
CLIENT_SECRET = 'k6OPn14WekgEvyZS8bkz4kO3O0Tv23G9'
REDIRECT_URI = 'http://localhost:3000/callback'

TOKEN_FILE = 'zoom_tokens.json'

def load_tokens():
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_tokens(tokens):
    with open(TOKEN_FILE, 'w') as f:
        json.dump(tokens, f)
def refresh_access_token(refresh_token):
    token_url = "https://zoom.us/oauth/token"
    headers = {
        "Authorization": f"Basic {base64.b64encode((CLIENT_ID + ':' + CLIENT_SECRET).encode()).decode()}",
        "Content-Type": "application/x-www-form-urlencoded"
    }
    payload = {
        "grant_type": "refresh_token",
        "refresh_token": refresh_token
    }
    response = requests.post(token_url, headers=headers, data=payload)
    response_data = response.json()
    if 'access_token' in response_data:
        save_tokens(response_data)  
        return response_data.get("access_token")
    else:
        
        print("Failed to refresh access token.")
        return None

def schedule_meeting(access_token):
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }
    
    meeting_details = {
        "topic": "Automated Meeting",
        "type": 2,  
        "start_time": "2024-06-04T7:20:00Z",  
        "duration": 60,  
        "timezone": "UTC",
        "agenda": "This is an automated meeting",
        "settings": {
            "host_video": True,
            "participant_video": True,
            "join_before_host": False,
            "mute_upon_entry": True,
            "watermark": True,
            "use_pmi": False,
            "approval_type": 0,  
            "registration_type": 1, 
            "audio": "both",  
            "auto_recording": "cloud"
        }
    }
    
    user_id = 'me'  
    response = requests.post(f'https://api.zoom.us/v2/users/{user_id}/meetings', headers=headers, json=meeting_details)
    
    if response.status_code == 201:
        meeting = response.json()
        join_url = meeting.get('join_url')
        return join_url
    else:
        return None

if __name__ == "__main__":
    tokens = load_tokens()
    
    if 'access_token' in tokens:
        access_token = tokens['access_token']
        join_url = schedule_meeting(access_token)
        if join_url:
            print("Meeting scheduled successfully!")
            print("Join URL:", join_url)
        else:
            print("Failed to schedule meeting.")
    else:
        print("No access token found. Make sure to obtain one.")
        
        

       
