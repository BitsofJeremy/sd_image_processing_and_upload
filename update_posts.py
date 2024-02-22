# Nifty little script to update all posts from public to members only

from datetime import datetime
from dotenv import load_dotenv
import jwt
import logging
import os
import requests

load_dotenv()
# Set up logging configuration
logging.basicConfig(
    # Set the logging level to INFO, you can change it to DEBUG for more detailed information
    level=logging.INFO,
    # Log file name
    filename='script_log.txt',
    # Log message format
    format='%(asctime)s - %(levelname)s - %(message)s',
)
# Ghost API information
admin_api_key = os.getenv('GHOST_ADMIN_API_KEY')
api_token = os.getenv('GHOST_API_KEY')
blog_domain = os.getenv('GHOST_BLOG_URL')
api_url = f"https://{blog_domain}/ghost/api/v3/admin"


def get_jwt():
    """ Get JWT from API based on admin key """
    # Split the key into ID and SECRET
    id, secret = admin_api_key.split(':')
    # Prepare header and payload
    iat = int(datetime.now().timestamp())
    header = {'alg': 'HS256', 'typ': 'JWT', 'kid': id}
    payload = {
        'iat': iat,
        'exp': iat + 5 * 60,
        'aud': '/v3/admin/'
    }
    # Create the token (including decoding secret)
    token = jwt.encode(
        payload,
        bytes.fromhex(secret),
        algorithm='HS256',
        headers=header
    )
    # print(token)
    return token


def update_blog_post(post_id, updated_at):
    jwt_token = get_jwt()
    url = f'https://{blog_domain}/ghost/api/v3/admin/posts/{post_id}/?source=html'
    body = {
        "posts": [{
            "updated_at": updated_at,
            "visibility": "members"
        }]
    }
    headers = {'Authorization': f'Ghost {jwt_token}'}
    try:
        res = requests.put(url, json=body, headers=headers)
        response = res.json()
        # print(response)
        return True
    # TODO figure out exceptions
    except Exception as e:
        # print(e)
        return False


def get_all_posts():
    # Get all current posts
    url = f"https://{blog_domain}/ghost/api/v3/content/posts/"
    querystring = {
        "key": api_token,
        "limit": "all",
        "order": "published_at asc",
        "include": "tags"
    }
    headers = {"Content-Type": "application/json"}
    response = requests.get(url, headers=headers, params=querystring)
    logging.info(response.json())
    data = response.json()
    return data['posts']


all_posts = get_all_posts()
for post in all_posts:
    print(post['title'])
    updated = update_blog_post(post_id=post['id'], updated_at=post['updated_at'])
    if updated:
        print("Updated")
    else:
        print("Not Updated")
