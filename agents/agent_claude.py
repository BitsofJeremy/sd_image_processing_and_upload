"""
Agent Claude Module

This module provides functionality to generate stories and titles based on
input images using the Anthropic API with Claude model.
"""

import logging
import base64
import os
from dotenv import load_dotenv
from anthropic import Anthropic

# Set up logging
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()


def agent_claude(_image, _gen_info):
    """
    Generate a story and title based on the input image using the Anthropic API.

    Args:
        _image (str): Path to the input image file.
        _gen_info (str): Additional generation information.

    Returns:
        dict: A dictionary containing the generated title and article.
    """
    logger.info("Using Anthropic API with Claude")

    # Initialize the Anthropic client
    client = Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

    # Read and encode the image
    with open(_image, "rb") as image_file:
        image_data = base64.b64encode(image_file.read()).decode("utf-8")

    # Determine the media type based on the file extension
    file_extension = os.path.splitext(_image)[1].lower()
    if file_extension in ('.jpg', '.jpeg'):
        image_media_type = "image/jpeg"
    elif file_extension == '.png':
        image_media_type = "image/png"
    else:
        raise ValueError(f"Unsupported image format: {file_extension}")

    # Generate the story
    story_prompt = f"""
    Craft an engaging short story inspired by this image.

    Create a narrative that captures the scene, characters, or emotions depicted.
    Adopt a tone that is witty and fun.
    ALWAYS keep your output to a maximum of 500 words.
    ALWAYS output in HTML.

    You may use the following data to help inspire your writing,
    as it pertains to how the image was generated with Stable Diffusion, but do NOT rely on it solely, 
    use your creativity:

    {_gen_info}
    """

    story_message = client.messages.create(
        model="claude-3-5-sonnet-20240620",
        max_tokens=1024,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": image_media_type,
                            "data": image_data,
                        },
                    },
                    {
                        "type": "text",
                        "text": story_prompt
                    }
                ],
            }
        ],
    )
    logger.info("Generated story from Claude")
    story = story_message.content[0].text
    logger.debug(f"Generated story: {story.strip()}")

    # Generate the title
    title_prompt = f"""
    This is the story for the image: {story}

    Craft an engaging short Twitter title for the story and the image I've uploaded.
    ALWAYS keep the title to less than 140 characters.
    ONLY return the title you came up with and nothing else.
    Aim to create a caption that will make users stop scrolling and want to engage with the post.
    The caption should intrigue viewers, complement the image, and encourage likes, comments, or shares.
    """

    title_message = client.messages.create(
        model="claude-3-5-sonnet-20240620",
        max_tokens=1024,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": image_media_type,
                            "data": image_data,
                        },
                    },
                    {
                        "type": "text",
                        "text": title_prompt
                    }
                ],
            }
        ],
    )
    logger.info("Generated title from Claude")
    title = title_message.content[0].text
    logger.debug(f"Generated title: {title.strip()}")

    # Return a dictionary with the blog title and article
    return {
        "title": title,
        "article": story
    }