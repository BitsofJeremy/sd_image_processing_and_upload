
from dotenv import load_dotenv
import json
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

SYSTEM_PROMPT = """MISSION:
    You specialize in creating engaging blog posts on art.
    Your content should primarily provide detailed, informative insights, enriched with a touch of humor.
    Your expertise in the English language, copywriting, SEO, and social media should shine through in each post.
    Your goal is to make balancing in-depth knowledge with witty humor.
    
    RULES:
    - Focus on delivering detailed information, complemented by humor.
    - Expertise in English, copywriting, SEO, and social media.
    - Writing style: Informative with a humorous twist.
"""


def agent_generate(_image, _gen_info):
    with open(_image, "rb") as image_file:
        image_data = image_file.read()

    article_prompt = f"""
        {SYSTEM_PROMPT}
        TASK:
        Use the following image generation data for your reference on how the image was created with Stable Diffusion.
        {_gen_info}
        write a short engaging blog post about this picture.
        The blog post must be unique and not cliche. 
        OUTPUT:
        text with HTML tags, but limited to only using the <p>, <b>, <h1>, and <h2> tags.
    """
    article = generate(
        model=model,
        prompt=article_prompt,
        images=[image_data],
        stream=False
    )
    logging.info(article['response'].lstrip())
    article_title = f"""
           write a short engaging Instagram caption for this image.
       """
    title = generate(
        model=model,
        prompt=article_title,
        images=[image_data],
        stream=False
    )
    logging.info(title['response'].replace('"','').strip())
    # TODO Get a consistent answer from the LLM
    # article_tags = """
    #            Create five tags for this image
    #            OUTPUT:
    #            {'tags': ['ai', 'art']}
    #        """
    # tags = generate(
    #     model=model,
    #     prompt=article_tags,
    #     images=[image_data],
    #     stream=False
    # )
    # logging.info(tags['response'])
    # try:
    #     tags_formatted = json.loads(tags['response'].lower().replace('\n', '').strip())
    # except json.decoder.JSONDecodeError as e:
    #     logging.info(f"Tags FAILED to format {e}")
    #     tags_formatted = {'tags': []}
    article_dict = {
        "title": title['response'][:180].replace('"', '').replace("`","").strip(),
        "article": article['response'].lstrip(),
        # "tags": tags_formatted['tags']
    }
    return article_dict
