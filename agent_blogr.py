
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
            You are EphergentOne the Ephemeral Emergent Artist.
            Write a short post about this image.
            Keep your output to a maximum of 250 words.
            You may use this data to help guide your writing as that is how the image was generated: {_gen_info} 
           """
        # Generate your article
        article = generate(
            model=model,
            prompt=article_prompt,
            images=[image_data],
            stream=False
        )
        logging.info(article['response'].replace('"', '').strip())
    # This is the prompt for your titles
    article_title = f"""
           write a short Instagram caption for this image.
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
    # Strip out quotes and keep the title to 180 characters
    # Sometimes the LLM hallucinates, and you get an essay on turtles.
    article_dict = {
        "title": title['response'][:180].replace('"', '').replace("`","").strip(),
        "article": article['response']
    }
    return article_dict
