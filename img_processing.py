from datetime import datetime, timezone
import os
from PIL import Image
from ghost_posting import upload_image_to_ghost, post_to_ghost
from agents.agent_ollama import agent_ollama
from agents.agent_claude import agent_claude
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

LLM_SOURCE = os.getenv('LLM_SOURCE')
ANTHROPIC_MODEL = os.getenv('ANTHROPIC_MODEL')
OLLAMA_MODEL = os.getenv('OLLAMA_MODEL')


def process_sfw_image(image_path, output_dir, watermark_path):
    """Process safe image and return path to processed image."""
    original_image = Image.open(image_path).convert("RGBA")
    watermark = Image.open(watermark_path).resize((120, 120))
    watermark_layer = Image.new("RGBA", original_image.size, (0, 0, 0, 0))
    watermark_layer.paste(watermark, (original_image.width - 120, original_image.height - 120), mask=watermark)
    watermarked_image = Image.alpha_composite(original_image, watermark_layer)

    processed_path = os.path.join(output_dir, f"processed_{os.path.basename(image_path)}")
    watermarked_image.convert("RGB").save(processed_path, "JPEG")

    return processed_path


def generate_content_sfw(image_path, generation_data):
    """Generate content for safe image using specified LLM."""
    if LLM_SOURCE == 'remote':
        return agent_claude(image_path, generation_data)
    else:
        return agent_ollama(image_path, generation_data, OLLAMA_MODEL)


def post_sfw_content(image_path, output_dir, watermark_path, generation_data):
    """Process safe image and post to Ghost."""
    processed_path = process_sfw_image(image_path, output_dir, watermark_path)

    # Upload image to Ghost
    image_url = upload_image_to_ghost(processed_path)

    # Generate content
    content = generate_content_sfw(image_path, generation_data)

    # Prepare post data
    post_data = {
        "title": content['title'],
        "tags": ["ai_art"],
        "html": f"{content['article']}<br/><br/>"
                f"<p>This image was created with Stable Diffusion.</p>"
                f"<p>Content generated using {'remote' if LLM_SOURCE == 'remote' else 'local'} LLM.</p>",
        "feature_image": image_url,
        "published_at": datetime.now(timezone.utc).isoformat()
    }

    # Post to Ghost
    post_to_ghost(post_data)

    # Cleanup temporary file
    os.remove(processed_path)
