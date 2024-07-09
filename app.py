import os
import shutil
from dotenv import load_dotenv
from img_processing import process_and_post_image

# Load environment variables
load_dotenv()

INPUT_DIR = os.path.abspath(os.getenv('INPUT_DIR'))
OUTPUT_DIR = os.path.abspath(os.getenv('OUTPUT_DIR'))
ARCHIVE_DIR = os.path.abspath(os.getenv('ARCHIVE_DIR'))
WATERMARK_PATH = os.path.abspath(os.getenv('WATERMARK_PATH'))


def process_image(filename):
    """Process a single image."""
    image_path = os.path.join(INPUT_DIR, filename)

    # Read associated text file if exists
    txt_path = os.path.join(INPUT_DIR, os.path.splitext(filename)[0] + ".txt")
    generation_data = ""
    if os.path.exists(txt_path):
        with open(txt_path, 'r') as txt_file:
            generation_data = txt_file.read()

    # Process and post the image
    process_and_post_image(image_path, OUTPUT_DIR, WATERMARK_PATH, generation_data)

    # Archive processed files
    shutil.move(image_path, os.path.join(ARCHIVE_DIR, filename))
    if os.path.exists(txt_path):
        shutil.move(txt_path, os.path.join(ARCHIVE_DIR, os.path.basename(txt_path)))


def main():
    """Main function to process images and generate blog posts."""
    # Ensure required directories exist
    for directory in [OUTPUT_DIR, ARCHIVE_DIR]:
        if not os.path.exists(directory):
            os.makedirs(directory)

    # Process images
    for filename in os.listdir(INPUT_DIR):
        if filename.endswith('.png'):
            process_image(filename)


if __name__ == "__main__":
    main()