from datetime import datetime as date
from dotenv import load_dotenv
import jwt
import logging
import os
from PIL import Image
import requests
import shutil

# Local Imports
from agent_blogr import agent_generate

# Set up logging configuration
logging.basicConfig(
    level=logging.INFO,
    filename='script_log.txt',
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
                "visibility": "members",
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


def process_image(filename):
    """Process a single image."""
    if filename.endswith(".png"):
        # Get the last modification time of the original PNG file
        image_path = os.path.join(input_directory, filename)
        image_datestamp = os.path.getmtime(image_path)
        # Convert Unix timestamp to datetime string in the required format
        image_datestamp = date.utcfromtimestamp(image_datestamp).strftime('%Y-%m-%dT%H:%M:%S.000Z')

        # Convert PNG to JPG
        # Extract the first 16 characters as post title
        post_title = os.path.splitext(filename)[0][:16]
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

        # Rename and copy associated TXT file to the output directory
        txt_filename = f"{base_filename}.txt"
        txt_path = os.path.join(input_directory, os.path.splitext(filename)[0] + ".txt")
        if os.path.exists(txt_path):
            shutil.copy(txt_path, os.path.join(output_directory, txt_filename))

        # Upload image to Ghost API
        files = {'file': (jpg_filename, open(jpg_path, 'rb'), 'image/jpeg')}
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

        # Generic Article Template:
        article_end = """
            <p>This image was created with Stable Diffusion.</p>
            <p>If you have any questions, feel free to reach out to us on 
            <a href="https://twitter.com/ephergent">X</a>.</p>    
            <p><i>Should there be generation details tied to the image, 
            they will be presented below for your reference. </i></p>
            <p>Have fun.</p>        
            """
        # Generate a title local AI
        ai_data_return = agent_generate(
            _image=image_path,
            _gen_info=generation_data
        )
        article = ai_data_return['article']
        logging.info(ai_data_return)
        tags = ["ai_art"]
        tag_line = os.getenv('TAGLINE')
        # Create Ghost post JSON
        post_data = {
            "title": ai_data_return['title'],
            "tags": tags,
            "html": f"{article}<br/><br/>"
                    f"{article_end}<br/>"
                    f"<p><code>{generation_data}</code></p><br/>"
                    f"<p>{tag_line}</p>",
            "feature_image": image_url,
            "published_at": image_datestamp
        }
        # Send it
        posted = add_post(_post_data=post_data)
        if posted:
            logging.info(f"POSTED ARTICLE: {post_title}")
        else:
            logging.info("POST FAILED, SORRY!!")

        # ARCHIVE AND CLEANUP

        # Move PNG and TXT files to the archive directory
        src_path_png = os.path.join(input_directory, filename)
        dst_path_png = os.path.join(archive_directory, filename)
        shutil.move(src_path_png, dst_path_png)
        logging.info(f"Files moved to archive directory: {filename}")

        # Move associated TXT file to the archive directory
        src_path_txt = os.path.join(input_directory, os.path.splitext(filename)[0] + ".txt")
        dst_path_txt = os.path.join(archive_directory, os.path.splitext(filename)[0] + ".txt")
        if os.path.exists(src_path_txt):
            shutil.move(src_path_txt, dst_path_txt)
            logging.info(f"Associated TXT file moved to archive directory: {txt_filename}")

        # Cleanup: Remove remaining files in output_directory
        try:
            if os.path.isfile(jpg_path) or os.path.islink(jpg_path):
                os.unlink(jpg_path)
            elif os.path.isdir(jpg_path):
                os.rmdir(jpg_path)
        except Exception as e:
            logging.info(f"Error cleaning up file or directory {jpg_path}: {e}")

        tmp_txt = os.path.join(output_directory, os.path.splitext(base_filename)[0] + ".txt")
        try:
            if os.path.isfile(tmp_txt) or os.path.islink(tmp_txt):
                os.unlink(tmp_txt)
            elif os.path.isdir(tmp_txt):
                os.rmdir(tmp_txt)
        except Exception as e:
            logging.info(f"Error cleaning up file or directory {tmp_txt}: {e}")
        # On to the next post
        logging.info(f"Finished with image: {filename}")
    else:
        logging.warning(f"Skipping file {filename}. Not a PNG file.")


def main():
    # Check if the output directory exists, create if not
    if not os.path.exists(output_directory):
        os.makedirs(output_directory)

    # Check if the archive directory exists, create if not
    if not os.path.exists(archive_directory):
        os.makedirs(archive_directory)

    # Loop through PNG images in the input directory
    for filename in os.listdir(input_directory):
        process_image(filename)

    logging.info("Finished Running Script.")


if __name__ == "__main__":
    # Load environment variables from the .env file
    load_dotenv()
    main()
