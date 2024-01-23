# ****************************************
# WARNING THIS REMOVES ALL POSTS FROM BLOG
# ****************************************
# This is just a bonus clean up script written for removing all posts.
# This was used during testing to remove all posts as I tested
# different prompts

from datetime import datetime as date
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
    iat = int(date.now().timestamp())
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


def delete_post(_id):
    """ Remove a post from the blog by post ID """
    jwt_token = get_jwt()
    url = f'{api_url}/posts/{_id}'
    headers = {
        'Authorization': f'Ghost {jwt_token}',
        "Accept-Version": "v3.0"
    }
    res = requests.delete(url, headers=headers)
    if res.status_code == 204:
        logging.info(f"Post Removed: {_id}")
        return True
    else:
        logging.info(f"FAILED NOT REMOVED: {_id}")
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
    delete_post(post['id'])
