
from datetime import datetime as date
from dotenv import load_dotenv
import jwt
import logging
import os
from PIL import Image, ImageDraw, ImageOps
import requests
import shutil
# Local Imports
from agent_blogr import agent_generate

# Set up logging configuration
logging.basicConfig(
    # Set the logging level to INFO, you can change it to DEBUG for more detailed information
    level=logging.INFO,
    # Log file name
    filename='script_log.txt',
    # Log message format
    format='%(asctime)s - %(levelname)s - %(message)s',
)

# ###### CONFIG ######
# Input and output directories
# Get absolute paths for input and output directories
input_directory = os.path.abspath(os.getenv('INPUT_DIR'))
output_directory = os.path.abspath(os.getenv('OUTPUT_DIR'))
archive_directory = os.path.abspath(os.getenv('ARCHIVE_DIR'))
# Watermark image path
watermark_path = os.path.abspath(os.getenv('WATERMARK_PATH'))
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
                "status": "published",
                "published_at": _post_data['published_at']
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
    logging.info(f"POSTED ARTICLE: {_post_data['title']}")
    if res.status_code == 201:
        return True
    else:
        return False


def main():
    # Step 1: Convert PNG to JPG and Move Associated Text Files
    # Check if the output directory exists, create if not
    if not os.path.exists(output_directory):
        os.makedirs(output_directory)

    # Loop through PNG images in the input directory
    for filename in os.listdir(input_directory):
        if filename.endswith(".png"):
            # Get the last modification time of the original PNG file
            image_path = os.path.join(input_directory, filename)
            image_datestamp = os.path.getmtime(image_path)
            # Convert Unix timestamp to datetime string in the required format
            image_datestamp = date.utcfromtimestamp(image_datestamp).strftime('%Y-%m-%dT%H:%M:%S.000Z')

            # Convert PNG to JPG
            post_title = os.path.splitext(filename)[0][:16]  # Extract the first 16 characters as post title
            base_filename = f"{post_title}"

            # JPG filename and path
            jpg_filename = f"{base_filename}.jpeg"
            jpg_path = os.path.join(output_directory, jpg_filename)

            # Open the image and convert to RGBA
            original_image = Image.open(image_path).convert("RGBA")

            # Resize the watermark to 120x120 pixels
            watermark = Image.open(watermark_path).resize((120, 120))

            # Create a transparent layer for the watermark
            watermark_layer = Image.new("RGBA", original_image.size, (0, 0, 0, 0))

            # Paste the watermark onto the transparent layer in the bottom right
            watermark_layer.paste(watermark, (original_image.width - 120, original_image.height - 120), mask=watermark)

            # Convert the original image to RGBA mode
            original_image = original_image.convert("RGBA")

            # Composite the original image and the watermark layer
            watermarked_image = Image.alpha_composite(original_image, watermark_layer)

            # Convert the image back to RGB mode before saving as JPEG
            watermarked_image = watermarked_image.convert("RGB")

            # Save the result as a JPG
            watermarked_image.save(jpg_path, "JPEG")

            # Copy associated TXT file to the output directory
            txt_filename = f"{base_filename}.txt"
            txt_path = os.path.join(input_directory, os.path.splitext(filename)[0] + ".txt")
            if os.path.exists(txt_path):
                shutil.copy(txt_path, os.path.join(output_directory, txt_filename))

            # Upload image to Ghost API
            files = {'file': (jpg_filename, open(jpg_path, 'rb'), 'image/jpeg')}
            # Change version to your correct Ghost install version
            jwt_token = get_jwt()
            headers = {
                "Authorization": f"Ghost {jwt_token}",
                "Accept-Version": "v3.0"
            }
            upload_url = f"{api_url}/images/upload/"
            response = requests.post(upload_url, headers=headers, files=files)
            image_url = response.json()["images"][0]["url"]

            # Read text data from associated text file
            txt_path = os.path.join(output_directory, os.path.splitext(jpg_filename)[0] + ".txt")
            if os.path.exists(txt_path):
                with open(txt_path, 'r') as txt_file:
                    generation_data = txt_file.read()
            else:
                generation_data = ""

            # Create a post with local AI
            post_dict = agent_generate(_image=image_path, _gen_info=generation_data)
            logging.info(post_dict)
            tags = ["ai_art"]
            # tags.extend(post_dict['tags'])
            # Create Ghost post JSON
            tag_line = os.getenv('TAGLINE')
            post_data = {
                "title": post_dict['title'],
                "tags": tags,
                "html": f"{post_dict['article']}<br/><br/>"
                        f"<p><code>{generation_data}</code></p><br/>"
                        f"<p>{tag_line}</p>",
                "feature_image": image_url,
                "published_at": image_datestamp
            }
            posted = add_post(_post_data=post_data)
            if posted:
                logging.info(f"POSTED ARTICLE: {post_title}")
            else:
                logging.info("POST FAILED, SORRY!!")

    # Check if the archive directory exists, create if not
    if not os.path.exists(archive_directory):
        os.makedirs(archive_directory)

    # Move PNG and TXT files to the archive directory
    for filename in os.listdir(input_directory):
        if filename.endswith((".png", ".txt")):
            src_path = os.path.join(input_directory, filename)
            dst_path = os.path.join(archive_directory, filename)
            shutil.move(src_path, dst_path)

    logging.info("Files moved to archive directory.")

    # Cleanup: Remove remaining files in output_directory
    for filename in os.listdir(output_directory):
        file_path = os.path.join(output_directory, filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                os.rmdir(file_path)
        except Exception as e:
            logging.info(f"Error cleaning up file or directory {file_path}: {e}")
    logging.info("Finished")


if __name__ == "__main__":
    # Load environment variables from the .env file
    load_dotenv()
    main()