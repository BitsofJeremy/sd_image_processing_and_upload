import os
from PIL import Image, ImageFilter
from nsfw_detector_pytorch import main as nsfw_detect
from ghost_posting import upload_image_to_ghost, post_to_ghost
from agents.agent_ollama import agent_ollama
from datetime import datetime, timezone

# Add this to your environment variables or configuration
NSFW_WATERMARK_PATH = os.path.abspath(os.getenv('NSFW_WATERMARK_PATH', 'NSFW.png'))


def check_nsfw(image_path):
    """Check if an image is NSFW using the best 3 out of 5 approach."""
    print(image_path)
    nsfw_count = 0
    total_nsfw_score = 0
    for _ in range(6):
        result = nsfw_detect(image_path)
        print(result)
        if result['is_nsfw']:
            nsfw_count += 1
        total_nsfw_score += result['nsfw_score']
    print(total_nsfw_score)
    is_nsfw = nsfw_count >= 3
    avg_nsfw_score = total_nsfw_score / 6
    return is_nsfw, avg_nsfw_score


def apply_blur(image, nsfw_score):
    """Apply a blur effect to the image based on the NSFW score."""
    max_blur = 20  # Maximum blur radius
    blur_amount = int(nsfw_score * max_blur)
    return image.filter(ImageFilter.GaussianBlur(radius=blur_amount))


def apply_nsfw_watermark(image):
    """Apply NSFW watermark to the image."""
    if not os.path.exists(NSFW_WATERMARK_PATH):
        raise FileNotFoundError(f"NSFW watermark not found at {NSFW_WATERMARK_PATH}")

    watermark = Image.open(NSFW_WATERMARK_PATH).convert("RGBA")

    # Resize watermark to fit the image (e.g., 1/4 of the image size)
    watermark_size = (image.width // 4, image.height // 4)
    watermark = watermark.resize(watermark_size, Image.LANCZOS)

    # Create a new transparent layer for the watermark
    watermark_layer = Image.new('RGBA', image.size, (0, 0, 0, 0))

    # Calculate position (centered)
    position = ((image.width - watermark.width) // 2,
                (image.height - watermark.height) // 2)

    # Paste the watermark onto the layer
    watermark_layer.paste(watermark, position, watermark)

    # Composite the watermark layer with the image
    return Image.alpha_composite(image.convert('RGBA'), watermark_layer)


def process_nsfw_image(image_path, output_dir, watermark_path):
    """Process NSFW image and return paths to processed images."""
    original_image = Image.open(image_path).convert("RGBA")
    watermark = Image.open(watermark_path).resize((120, 120))
    watermark_layer = Image.new("RGBA", original_image.size, (0, 0, 0, 0))
    watermark_layer.paste(watermark, (original_image.width - 120, original_image.height - 120), mask=watermark)
    watermarked_image = Image.alpha_composite(original_image, watermark_layer)

    # Save non-blurred version
    non_blurred_path = os.path.join(output_dir, f"non_blurred_{os.path.basename(image_path)}")
    watermarked_image.convert("RGB").save(non_blurred_path, "JPEG")

    # Apply blur
    _, nsfw_score = check_nsfw(image_path)
    blurred_image = apply_blur(watermarked_image, nsfw_score)

    # Apply NSFW watermark
    blurred_image_with_watermark = apply_nsfw_watermark(blurred_image)

    # Save blurred version with NSFW watermark
    blurred_path = os.path.join(output_dir, f"blurred_{os.path.basename(image_path)}")
    blurred_image_with_watermark.convert("RGB").save(blurred_path, "JPEG")

    return non_blurred_path, blurred_path


def generate_content_nsfw(image_path, generation_data):
    """Generate content for NSFW image using local LLM."""
    return agent_ollama(image_path, generation_data, os.getenv('OLLAMA_MODEL'))


def post_nsfw_content(image_path, output_dir, watermark_path, generation_data):
    """Process NSFW image and post to Ghost."""
    non_blurred_path, blurred_path = process_nsfw_image(image_path, output_dir, watermark_path)

    # Upload both images to Ghost
    non_blurred_url = upload_image_to_ghost(non_blurred_path)
    blurred_url = upload_image_to_ghost(blurred_path)

    # Generate content
    content = generate_content_nsfw(image_path, generation_data)

    # Prepare post data
    post_data = {
        "title": content['title'],
        "tags": ["ai_art", "nsfw"],
        "html": f"{content['article']}<br/><br/>"
                f'<img src="{non_blurred_url}" alt="Original non-blurred image" /><br/><br/>'
                f"<p>This image was created with Stable Diffusion and processed for content moderation.</p>"
                f"<p>Content generated using local LLM.</p>",
        "feature_image": blurred_url,
        "published_at": datetime.now(timezone.utc).isoformat()
    }

    # Post to Ghost
    post_to_ghost(post_data)

    # Cleanup temporary files
    os.remove(non_blurred_path)
    os.remove(blurred_path)