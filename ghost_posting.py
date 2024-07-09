import os
import requests
import jwt
from datetime import datetime as date
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

API_TOKEN = os.getenv('GHOST_ADMIN_API_KEY')
BLOG_DOMAIN = os.getenv('GHOST_BLOG_URL')
API_URL = f"https://{BLOG_DOMAIN}/ghost/api/v3/admin"

def get_jwt():
    """Generate JWT token for Ghost API authentication."""
    id, secret = API_TOKEN.split(':')
    iat = int(date.now().timestamp())
    header = {'alg': 'HS256', 'typ': 'JWT', 'kid': id}
    payload = {
        'iat': iat,
        'exp': iat + 5 * 60,
        'aud': '/v3/admin/'
    }
    token = jwt.encode(payload, bytes.fromhex(secret), algorithm='HS256', headers=header)
    return token

def upload_image_to_ghost(image_path):
    """Upload an image to Ghost and return the URL."""
    with open(image_path, 'rb') as img_file:
        files = {'file': (os.path.basename(image_path), img_file, 'image/jpeg')}
        jwt_token = get_jwt()
        headers = {"Authorization": f"Ghost {jwt_token}", "Accept-Version": "v3.0"}
        upload_url = f"{API_URL}/images/upload/"
        response = requests.post(upload_url, headers=headers, files=files)
        if response.status_code == 201:
            return response.json()["images"][0]["url"]
        else:
            raise Exception(f"Failed to upload image: {response.text}")

def post_to_ghost(post_data):
    """Post data to Ghost blog admin API."""
    jwt_token = get_jwt()
    post_json = {
        "posts": [{
            "title": post_data['title'],
            "tags": post_data['tags'],
            "html": post_data["html"],
            "feature_image": post_data["feature_image"],
            "status": "published",
            "visibility": "members",
            "published_at": post_data['published_at']
        }]
    }
    url = f'{API_URL}/posts/?source=html'
    headers = {
        'Authorization': f'Ghost {jwt_token}',
        "Accept-Version": "v3.0"
    }
    response = requests.post(url, json=post_json, headers=headers)
    if response.status_code == 201:
        return True
    else:
        raise Exception(f"Failed to post article: {response.text}")