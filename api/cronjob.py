import requests
import json
import os
import logging

CLIENT_ID = os.getenv('CLIENT_ID')
CLIENT_SECRET = os.getenv('CLIENT_SECRET')
TOKEN_FILE = 'zoom_tokens.json'

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_tokens():
    if os.path.exists(TOKEN_FILE):
        try:
            with open(TOKEN_FILE, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error("Failed to load tokens from file: %s", e)
            return {}
    else:
        logger.warning("Token file not found.")
        return {}

def refresh_tokens(refresh_token):
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    data = {
        'grant_type': 'refresh_token',
        'refresh_token': refresh_token,
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET
    }
    response = requests.post('https://zoom.us/oauth/token', headers=headers, data=data)
    if response.status_code == 200:
        tokens = response.json()
        with open(TOKEN_FILE, 'w') as f:
            json.dump(tokens, f)
        return tokens
    else:
        logger.error("Failed to refresh tokens. Status code: %s", response.status_code)
        return None

def schedule_meeting():
    tokens = load_tokens()
    access_token = tokens.get('access_token')
    refresh_token = tokens.get('refresh_token')

    if not access_token or not refresh_token:
        logger.error("No access token or refresh token found. Make sure to obtain one.")
        return {"error": "No access token or refresh token found. Make sure to obtain one."}

    meeting_start_time_utc = '2024-06-11T14:30:00Z'  # 8:00 PM IST = 2:30 PM UTC
    join_url = schedule_meeting_request(access_token, meeting_start_time_utc)
    
    if join_url:
        logger.info("Meeting scheduled successfully!")
        logger.info("Join URL: %s", join_url)
        return {"message": "Meeting scheduled successfully!", "join_url": join_url}
    else:
        logger.error("Failed to schedule meeting. Please try again later.")
        tokens = refresh_tokens(refresh_token)
        if tokens:
            access_token = tokens.get('access_token')
            join_url = schedule_meeting_request(access_token, meeting_start_time_utc)
            if join_url:
                logger.info("Meeting scheduled successfully after token refresh!")
                logger.info("Join URL: %s", join_url)
                return {"message": "Meeting scheduled successfully after token refresh!", "join_url": join_url}
            else:
                logger.error("Failed to schedule meeting after token refresh.")
                return {"error": "Failed to schedule meeting after token refresh."}
        else:
            logger.error("Failed to refresh tokens.")
            return {"error": "Failed to refresh tokens."}

def schedule_meeting_request(access_token, start_time):
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }
    
    meeting_details = {
        "topic": "Automated Meeting",
        "type": 2,
        "start_time": start_time,
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
        logger.error("Failed to schedule meeting. Status code: %s", response.status_code)
        return None

# Vercel serverless function handler
def handler(event, context):
    if event.get('httpMethod') == 'POST':
        return {
            'statusCode': 200,
            'body': json.dumps(schedule_meeting())
        }
    else:
        logger.error("Unsupported HTTP method: %s", event.get('httpMethod'))
        return {
            'statusCode': 400,
            'body': json.dumps({"error": "Only POST requests are supported."})
        }
