
from dotenv import load_dotenv
import logging
from ollama import generate
import os

# Set up logging configuration
logging.basicConfig(
    # Set the logging level to INFO, you can change it to DEBUG for more detailed information
    level=logging.INFO,
    # Log file name
    filename='script_log.txt',
    # Log message format
    format='%(asctime)s - %(levelname)s - %(message)s',
)

# Load environment variables from the .env file
load_dotenv()

# NOTE: ollama must be running for this to work,
# start the ollama app or run `ollama serve`
model = os.getenv('OLLAMA_MODEL')


def agent_generate(_image, _gen_info):
    with open(_image, "rb") as image_file:
        image_data = image_file.read()
        # This is the prompt for your article
        article_prompt = f"""
            Craft an engaging short story inspired by this image.

            Create a narrative that captures the scene, characters, or emotions depicted.
            Adopt a tone that is witty and fun.
            Always keep your output to a maximum of 500 words.

            You may use the following data to help inspire your writing,
            as it pertains to how the image was generated with AI, but do not rely on it, use your creativity:

            {_gen_info}
        """
        # Generate your article
        article = generate(
            model=model,
            prompt=article_prompt,
            images=[image_data],
            stream=False
        )
        logging.info(article['response'].replace('"', '').strip())

    article_story = article['response']
    # This is the prompt for your titles
    article_title = f"""
        This is the story for the image: {article_story}

        Craft an engaging short Twitter title for the story and the image I've uploaded.
        Always keep the title to less than 140 characters.
        Aim to create a caption that will make users stop scrolling and want to engage with the post.
        The caption should intrigue viewers, complement the image, and encourage likes, comments, or shares.
    """
    # Generate your title
    title = generate(
        model=model,
        prompt=article_title,
        images=[image_data],
        stream=False
    )
    logging.info(title['response'].replace('"','').strip())
    # Return a nice dictionary to the main script
    # Strip out any type of quotes
    article_dict = {
        "title": title['response'][:140].replace('"', '').replace("`","").strip(),
        "article": article['response']
    }
    return article_dict
