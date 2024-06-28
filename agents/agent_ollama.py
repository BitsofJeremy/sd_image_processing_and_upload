"""
Agent Ollama Module

This module provides functionality to generate stories and titles based on
input images using the Ollama local language model.
"""

import logging
from ollama import generate

# Set up logging
logger = logging.getLogger(__name__)


def agent_ollama(_image, _gen_info, _model):
    """
    Generate a story and title based on the input image using the Ollama local LLM.

    Args:
        _image (str): Path to the input image file.
        _gen_info (str): Additional generation information.
        _model (str): Name of the Ollama model to use.

    Returns:
        dict: A dictionary containing the generated title and article.
    """
    logger.info(f"Using Ollama with model: {_model}")

    with open(_image, "rb") as image_file:
        image_data = image_file.read()

        # Generate the article
        article_prompt = f"""
            Craft an engaging short story inspired by this image.

            Create a narrative that captures the scene, characters, or emotions depicted.
            Adopt a tone that is witty and fun.
            Always keep your output to a maximum of 500 words.

            You may use the following data to help inspire your writing,
            as it pertains to how the image was generated with AI, but do not rely on it, use your creativity:

            {_gen_info}
        """
        article_response = generate(
            model=_model,
            prompt=article_prompt,
            images=[image_data],
            stream=False
        )
        article_story = article_response['response']
        logger.info("Generated article from Ollama")
        logger.debug(f"Generated article: {article_story.strip()}")

        # Generate the title
        title_prompt = f"""
            This is the story for the image: {article_story}

            Craft an engaging short Twitter title for the story and the image I've uploaded.
            Always keep the title to less than 140 characters.
            Aim to create a caption that will make users stop scrolling and want to engage with the post.
            The caption should intrigue viewers, complement the image, and encourage likes, comments, or shares.
        """
        title_response = generate(
            model=_model,
            prompt=title_prompt,
            images=[image_data],
            stream=False
        )
        title = title_response['response']
        logger.info("Generated title from Ollama")
        logger.debug(f"Generated title: {title.strip()}")

    # Return a dictionary with the blog title and article
    return {
        "title": title.replace('"', '').replace("`", "").strip(),
        "article": article_story
    }