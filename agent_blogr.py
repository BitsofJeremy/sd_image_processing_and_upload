
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

    article_prompt = f"""
        write a short engaging blog post about this picture.
        You can use the following generation data for your reference on how the image was created.
        {_gen_info}
        The blog post must be unique and not cliche. 
        Output to HTML tags, but limited to only using p, b, h1, and h2.
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

    article_dict = {
        "title": title['response'][:180].replace('"', '').replace("`","").strip(),
        "article": article['response'].lstrip()
    }
    return article_dict
