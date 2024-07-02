"""
AI Image Processing and Blog Post Generation

This script automates the process of generating blog posts from images using AI.
It monitors a directory for new PNG images, uses a Language Model (LLM) to create
a story and title based on the image, processes the image (resizing and adding
a watermark), and then uploads it to a Ghost blog as a new post.
"""

import logging
from datetime import datetime as date
from dotenv import load_dotenv
import jwt
import os
from PIL import Image
import requests
import shutil

# Local Imports
from agents.agent_ollama import agent_ollama
from agents.agent_claude import agent_claude

# Set up logging configuration
logging.basicConfig(
    level=logging.INFO,
    filename='script_log.txt',
    format='%(asctime)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Configuration
INPUT_DIR = os.path.abspath(os.getenv('INPUT_DIR'))
OUTPUT_DIR = os.path.abspath(os.getenv('OUTPUT_DIR'))
ARCHIVE_DIR = os.path.abspath(os.getenv('ARCHIVE_DIR'))
WATERMARK_PATH = os.path.abspath(os.getenv('WATERMARK_PATH'))
API_TOKEN = os.getenv('GHOST_ADMIN_API_KEY')
BLOG_DOMAIN = os.getenv('GHOST_BLOG_URL')
API_URL = f"https://{BLOG_DOMAIN}/ghost/api/v3/admin"
LLM_SOURCE = os.getenv('LLM_SOURCE')
TAGLINE = os.getenv('TAGLINE')
ANTHROPIC_MODEL = os.getenv('ANTHROPIC_MODEL')
OLLAMA_MODEL = os.getenv('OLLAMA_MODEL')


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


def add_post(post_data):
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
    logger.info(f"API Response: {response.status_code}")
    if response.status_code == 201:
        logger.info(f"POSTED ARTICLE: {post_data['title']}")
        return True
    else:
        logger.error(f"Failed to post article: {post_data['title']}")
        return False


def generate_content_with_fallback(image_path, generation_data):
    """
    Generate content using the specified LLM with a fallback mechanism.
    Returns a tuple of (ai_data_return, model_used)
    """
    try:
        if LLM_SOURCE == 'remote':
            logger.info(f"Attempting to use remote LLM: {ANTHROPIC_MODEL}")
            ai_data_return = agent_claude(image_path, generation_data)
            return ai_data_return, ANTHROPIC_MODEL
        elif LLM_SOURCE == 'local':
            logger.info(f"Using local LLM: {OLLAMA_MODEL}")
            ai_data_return = agent_ollama(image_path, generation_data, OLLAMA_MODEL)
            return ai_data_return, OLLAMA_MODEL
        else:
            raise ValueError(f"Invalid LLM_SOURCE: {LLM_SOURCE}")
    except Exception as e:
        logger.error(f"Error with primary LLM ({LLM_SOURCE}): {str(e)}")

        # Fallback to local Ollama if remote fails
        if LLM_SOURCE == 'remote':
            logger.info(f"Falling back to local Ollama LLM: {OLLAMA_MODEL}")
            ai_data_return = agent_ollama(image_path, generation_data, OLLAMA_MODEL)
            return ai_data_return, OLLAMA_MODEL
        else:
            # If local was the primary and it failed, we don't have another fallback
            logger.error("Both remote and local LLMs failed. Unable to generate content.")
            raise


def process_image(filename):
    """Process a single image."""
    logger.info(f"Processing image: {filename}")
    if not filename.endswith(".png"):
        logger.warning(f"Skipping file {filename}. Not a PNG file.")
        return

    # Get image details
    image_path = os.path.join(INPUT_DIR, filename)
    image_datestamp = date.utcfromtimestamp(os.path.getmtime(image_path)).strftime('%Y-%m-%dT%H:%M:%S.000Z')
    post_title = os.path.splitext(filename)[0][:16]
    base_filename = f"{post_title}"
    jpg_filename = f"{base_filename}.jpeg"
    jpg_path = os.path.join(OUTPUT_DIR, jpg_filename)

    # Process image
    original_image = Image.open(image_path).convert("RGBA")
    watermark = Image.open(WATERMARK_PATH).resize((120, 120))
    watermark_layer = Image.new("RGBA", original_image.size, (0, 0, 0, 0))
    watermark_layer.paste(watermark, (original_image.width - 120, original_image.height - 120), mask=watermark)
    watermarked_image = Image.alpha_composite(original_image, watermark_layer)
    watermarked_image.convert("RGB").save(jpg_path, "JPEG")
    logger.info(f"Processed image: {jpg_filename}")

    # Copy associated text file
    txt_filename = f"{base_filename}.txt"
    txt_path = os.path.join(INPUT_DIR, os.path.splitext(filename)[0] + ".txt")
    if os.path.exists(txt_path):
        shutil.copy(txt_path, os.path.join(OUTPUT_DIR, txt_filename))
        logger.info(f"Copied associated text file: {txt_filename}")

    # Upload image to Ghost API
    with open(jpg_path, 'rb') as img_file:
        files = {'file': (jpg_filename, img_file, 'image/jpeg')}
        jwt_token = get_jwt()
        headers = {"Authorization": f"Ghost {jwt_token}", "Accept-Version": "v3.0"}
        upload_url = f"{API_URL}/images/upload/"
        response = requests.post(upload_url, headers=headers, files=files)
        image_url = response.json()["images"][0]["url"]
        logger.info(f"Uploaded image to Ghost API: {image_url}")

    # Read generation data
    generation_data = ""
    txt_path = os.path.join(OUTPUT_DIR, os.path.splitext(jpg_filename)[0] + ".txt")
    if os.path.exists(txt_path):
        with open(txt_path, 'r') as txt_file:
            generation_data = txt_file.read()

    # Generate content using LLM with fallback
    try:
        ai_data_return, model_used = generate_content_with_fallback(image_path, generation_data)
        logger.info(f"Successfully generated title and article using model: {model_used}")
        logger.debug(f"Raw LLM output: {ai_data_return}")
    except Exception as e:
        logger.error(f"Failed to generate content: {str(e)}")
        return

    # Prepare post data
    article = ai_data_return['article'].replace('\n\n', '<br/><br/>')
    article_end = f"""
        <p>This image was created with Stable Diffusion.</p>
        <p>The text above was generated by a large language model with vision capabilities.</p>
        <p>The LLM model used for this story generation was: <strong>{model_used}</strong></p>
        <p>If you have any questions, feel free to reach out to us on 
        <a href="https://twitter.com/ephergent">X</a>.</p>    
        <p><i>Should there be generation details tied to the image, 
        they will be presented below for your reference.</i></p>
        <p>Have fun.</p>
        """

    # Strip any leading/trailing whitespace and quotes from the title
    cleaned_title = ai_data_return['title'].strip().strip('"')

    tags = ["ai_art"]
    post_data = {
        "title": cleaned_title,
        "tags": tags,
        "html": f"{article}<br/><br/>"
                f"<p>******</p>"
                f"{article_end}<br/>"
                f"<p>{TAGLINE}</p>"
                f"<p>******</p>"
                f"<p><code>{generation_data}</code></p><br/>",
        "feature_image": image_url,
        "published_at": image_datestamp
    }

    # Post to Ghost
    posted = add_post(post_data)
    if posted:
        logger.info(f"Successfully posted article: {post_title}")
    else:
        logger.error(f"Failed to post article: {post_title}")

    # Archive and cleanup
    src_path_png = os.path.join(INPUT_DIR, filename)
    dst_path_png = os.path.join(ARCHIVE_DIR, filename)
    shutil.move(src_path_png, dst_path_png)
    logger.info(f"Archived original PNG: {filename}")

    src_path_txt = os.path.join(INPUT_DIR, os.path.splitext(filename)[0] + ".txt")
    dst_path_txt = os.path.join(ARCHIVE_DIR, os.path.splitext(filename)[0] + ".txt")
    if os.path.exists(src_path_txt):
        shutil.move(src_path_txt, dst_path_txt)
        logger.info(f"Archived associated TXT file: {os.path.basename(src_path_txt)}")

    # Cleanup temporary files
    for temp_file in [jpg_path, os.path.join(OUTPUT_DIR, txt_filename)]:
        try:
            os.remove(temp_file)
            logger.info(f"Removed temporary file: {os.path.basename(temp_file)}")
        except Exception as e:
            logger.error(f"Error removing temporary file {temp_file}: {e}")

    logger.info(f"Finished processing image: {filename}")


def main():
    """Main function to process images and generate blog posts."""
    logger.info("Starting image processing and upload script")

    # Ensure required directories exist
    for directory in [OUTPUT_DIR, ARCHIVE_DIR]:
        if not os.path.exists(directory):
            os.makedirs(directory)
            logger.info(f"Created directory: {directory}")

    if LLM_SOURCE not in ['local', 'remote']:
        logger.error(f"Invalid LLM_SOURCE: {LLM_SOURCE}. Please set it to 'local' or 'remote'.")
        return

    logger.info(f"Using LLM source: {LLM_SOURCE}")

    # Process images
    for filename in os.listdir(INPUT_DIR):
        if filename.endswith('.png'):
            process_image(filename)

    logger.info("Finished running script")


if __name__ == "__main__":
    main()