
from datetime import datetime as date
import dotenv
import json
import jwt
import os
import requests
from PIL import Image

dotenv = DotEnv()

# ###### CONFIG ######
# Input and output directories
input_directory = dotenv.get('INPUT_DIR')
output_directory = dotenv.get('OUTPUT_DIR')
# Ghost API information
api_token = dotenv.get('GHOST_ADMIN_API_KEY')
blog_domain = dotenv.get('GHOST_BLOG_URL')
api_url = f"https://{blog_domain}/ghost/api/admin"


def get_jwt():
    """ Get JWT from API based on admin key """
    # Split the key into ID and SECRET
    id, secret = api_token.split(':')

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


def add_post(post_data):
    jwt_token = get_jwt()
    post_json = {
        "posts": [
            {
                "title": post_data['title'],
                "slug": post_data["slug"],
                "html": post_data["html"],
                "feature_image": post_data["feature_image"],
                "published_at": post_data["published_at"],
                "status": "draft"
            }
        ]
    }
    url = f'https://{GHOST_DOMAIN}/ghost/api/v3/admin/posts/?source=html'
    headers = {'Authorization': f'Ghost {jwt_token}'}
    res = requests.post(url, json=post_json, headers=headers)
    response = res.json()
    print(res.status_code)
    print("DONE")

# Step 1: Convert PNG to JPG and Move Associated Text Files

# Check if the output directory exists, create if not
if not os.path.exists(output_directory):
    os.makedirs(output_directory)

# Loop through PNG images in the input directory
for filename in os.listdir(input_directory):
    if filename.endswith(".png"):
        # Convert PNG to JPG
        png_path = os.path.join(input_directory, filename)
        jpg_path = os.path.join(output_directory, os.path.splitext(filename)[0] + ".jpg")
        Image.open(png_path).convert("RGB").save(jpg_path)

        # Move associated text file to the output directory
        txt_path = os.path.join(input_directory, os.path.splitext(filename)[0] + ".txt")
        if os.path.exists(txt_path):
            os.rename(txt_path, os.path.join(output_directory, os.path.basename(txt_path)))

# Step 2: Upload JPG images to Ghost Blog API and Create Blog Posts

# Loop through JPG images in the output directory
for filename in os.listdir(output_directory):
    if filename.endswith(".jpg"):
        # Upload image to Ghost API
        image_path = os.path.join(output_directory, filename)
        files = {'file': (filename, open(image_path, 'rb'))}
        # Change version to your. correct install version
        headers = {
            "Authorization": f"Ghost {api_token}",
            "Accept-Version": "v3"
        }
        upload_url = f"{api_url}/images/upload/"
        response = requests.post(upload_url, headers=headers, files=files)
        image_url = response.json()["images"][0]["url"]

        # Read text data from associated text file
        txt_path = os.path.join(output_directory, os.path.splitext(filename)[0] + ".txt")
        if os.path.exists(txt_path):
            with open(txt_path, 'r') as txt_file:
                generation_data = txt_file.read()
        else:
            generation_data = ""

        # Create Ghost post JSON
        post_title = os.path.splitext(filename)[0][:16]
        # Update Post with your custom settings
        # set to 'published' in production
        post_data = {
            "posts": [
                {
                    "title": post_title,
                    "tags": ["ai_art"],
                    "html": f"<p>{filename}</p><br/><br/><p>{generation_data}</p>",
                    "status": "draft",
                    "feature_image": image_url,
                }
            ]
        }

        # POST JSON to create a new post
        post_url = f"{api_url}/posts/?source=html"
        response = requests.post(post_url, headers=headers, json=post_data)
        print(f"Server Response: {response.text}")
print("Finished")
