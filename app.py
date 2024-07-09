import os
import shutil
from dotenv import load_dotenv
from nsfw_detector_pytorch import main as nsfw_detect
from nsfw_processing import post_nsfw_content, check_nsfw
from sfw_processing import post_sfw_content

# Load environment variables
load_dotenv()

INPUT_DIR = os.path.abspath(os.getenv('INPUT_DIR'))
OUTPUT_DIR = os.path.abspath(os.getenv('OUTPUT_DIR'))
ARCHIVE_DIR = os.path.abspath(os.getenv('ARCHIVE_DIR'))
WATERMARK_PATH = os.path.abspath(os.getenv('WATERMARK_PATH'))


def is_nsfw(image_path):
    """Determine if an image is NSFW using the robust checking method."""
    is_nsfw, avg_nsfw_score = check_nsfw(image_path)
    print(f"Is NSFW: {is_nsfw}, Average NSFW Score: {avg_nsfw_score}")
    return is_nsfw, avg_nsfw_score


def process_image(filename):
    """Process a single image."""
    image_path = os.path.join(INPUT_DIR, filename)

    # Read associated text file if exists
    txt_path = os.path.join(INPUT_DIR, os.path.splitext(filename)[0] + ".txt")
    generation_data = ""
    if os.path.exists(txt_path):
        with open(txt_path, 'r') as txt_file:
            generation_data = txt_file.read()

    # Check if the image is NSFW
    nsfw, nsfw_score = is_nsfw(image_path)
    if nsfw:
        post_nsfw_content(image_path, OUTPUT_DIR, WATERMARK_PATH, generation_data, nsfw_score)
    else:
        post_sfw_content(image_path, OUTPUT_DIR, WATERMARK_PATH, generation_data)

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