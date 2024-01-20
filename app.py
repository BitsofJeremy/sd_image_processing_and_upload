
from datetime import datetime as date
from dotenv import load_dotenv
import jwt
import os
import requests
from PIL import Image
# TODO Add logging

# Load environment variables from the .env file
load_dotenv()

# ###### CONFIG ######
# Input and output directories
input_directory = os.getenv('INPUT_DIR')
output_directory = os.getenv('OUTPUT_DIR')
# Ghost API information
api_token = os.getenv('GHOST_ADMIN_API_KEY')
blog_domain = os.getenv('GHOST_BLOG_URL')
api_url = f"https://{blog_domain}/ghost/api/v3/admin"


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


def add_post(_post_data):
    """ Post dict to blog admin API """
    jwt_token = get_jwt()
    post_json = {
        "posts": [
            {
                "title": _post_data['title'],
                "tags": _post_data['tags'],
                "html": _post_data["html"],
                "feature_image": _post_data["feature_image"],
                "status": "published"
            }
        ]
    }
    url = f'{api_url}/posts/?source=html'
    headers = {
        'Authorization': f'Ghost {jwt_token}',
        "Accept-Version": "v3.0"
    }
    res = requests.post(url, json=post_json, headers=headers)
    # response = res.json()
    print(f"POSTED ARTICLE: {_post_data['title']}")
    if res.status_code == 201:
        return True
    else:
        return False


# TODO Put all this in a main function

# Step 1: Convert PNG to JPG and Move Associated Text Files
# Check if the output directory exists, create if not
if not os.path.exists(output_directory):
    os.makedirs(output_directory)

# Loop through PNG images in the input directory
for filename in os.listdir(input_directory):
    if filename.endswith(".png"):
        # Convert PNG to JPG
        post_title = os.path.splitext(filename)[0][:16]  # Extract the first 16 characters as post title
        base_filename = f"{post_title}"

        # JPG filename and path
        jpg_filename = f"{base_filename}.jpeg"
        jpg_path = os.path.join(output_directory, jpg_filename)
        Image.open(os.path.join(input_directory, filename)).convert("RGB").save(jpg_path)

        # Text filename and path
        txt_filename = f"{base_filename}.txt"
        txt_path = os.path.join(input_directory, os.path.splitext(filename)[0] + ".txt")
        if os.path.exists(txt_path):
            os.rename(txt_path, os.path.join(output_directory, txt_filename))

# Step 2: Upload JPG images to Ghost Blog API and Create Blog Posts

# Loop through JPG images in the output directory
for filename in os.listdir(output_directory):
    if filename.endswith(".jpeg"):
        post_title = os.path.splitext(filename)[0][:16]  # Extract the first 16 characters as post title
        base_filename = f"{post_title}"
        # JPG filename and path
        jpg_filename = f"{base_filename}.jpeg"
        # Upload image to Ghost API
        image_path = os.path.join(output_directory, filename)
        files = {'file': (jpg_filename, open(image_path, 'rb'), 'image/jpeg')}
        # Change version to your. correct Ghost install version
        jwt_token = get_jwt()
        headers = {
            "Authorization": f"Ghost {jwt_token}",
            "Accept-Version": "v3.0"
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
        post_data = {
            "title": post_title,
            "tags": ["ai_art"],
            "html": f"<p>{filename}</p><br/><br/><p><code>{generation_data}</code></p>",
            "feature_image": image_url,
        }
        # TODO add try/except for posting articles
        posted = add_post(_post_data=post_data)

print("Finished")
