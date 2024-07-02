# AI Image Processing and Blog Post Generation

This Python application automates the process of generating blog posts from Stable Diffusion images using AI. It monitors a directory for new PNG images, uses a Language Model (LLM) to create a story and title based on the image, processes the image (resizing and adding a watermark), and then uploads it to a Ghost blog as a new post.

For more details, read the original blog post here:
[Adding AI to my AI Art Workflow with Ollama and a Multimodal LLM](https://bits.jeremyschroeder.net/adding-ai-to-my-ai-art-worklfow-with-ollama-and-a-multimodal-llm/)

Read the new updates here [adding Anthropic Claude to the workflow]:
[AI-Powered Blog Post Generator: Turning Pixels into Prose with Ollama and Claude](https://bits.jeremyschroeder.net/ai-powered-blog-post-generator-turning-pixels-into-prose-with-ollama-and-claude/)

## Features

- Monitors a directory for new PNG images from Stable Diffusion
- Uses either a local LLM (llava-llama3 via Ollama) or a remote LLM (Claude via Anthropic API) to generate story content and titles
- Processes images: converts PNG to JPEG, resizes, and adds a watermark
- Uploads processed images and generated content to a Ghost blog
- Archives processed images and associated files
- Fallback mechanism: if the remote LLM fails, it falls back to the local LLM
- Transparency: includes information about which LLM model was used in the blog post

## Prerequisites

- Python 3.7+
- Ghost blog instance
- Ollama with llava-llama3 model installed (for local LLM)
- Anthropic API key (for Claude, if using remote LLM option)

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/BitsofJeremy/sd_image_processing_and_upload.git
   cd sd_image_processing_and_upload
   ```

2. Create a virtual environment and activate it:
   ```bash
   virtualenv -p python3 venv
   source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
   ```

3. Install the required packages:
   ```bash
   pip install -r requirements.txt
   ```

4. Copy the `.env-example` file to `.env` and fill in your configuration details:
   ```bash
   cp .env-example .env
   ```

5. Install Ollama and the llava-llama3 model:
   ```bash
   # Install Ollama (if not already installed)
   curl https://ollama.ai/install.sh | sh
   
   # Pull the llava-llama3 model
   ollama pull llava-llama3
   ```

## Configuration

Edit the `.env` file with your specific settings. Here's an example of what it should look like:

```
# Local Directory
INPUT_DIR='Where A1111 Saves files'
OUTPUT_DIR='Temp directory for working with images'
ARCHIVE_DIR='A place for your archived images to end up'
WATERMARK_PATH='Add a transparent PNG for a watermark'

# Sometimes you need a tag line for the end of your posts
TAGLINE="I Like Turtles"

# LLM Source [local or remote]
LLM_SOURCE='local'

# Anthropic Key and Model (for remote option)
ANTHROPIC_API_KEY="Your Anthropic Key"
ANTHROPIC_MODEL="claude-3-5-sonnet-20240620"

# Ollama Model to use for agent
OLLAMA_MODEL='llava-llama3'

# Your Ghost Blog
GHOST_BLOG_URL='https://example-blog.com'
GHOST_ADMIN_API_KEY='super secret'
GHOST_API_KEY='super secret'
```

## Usage

Run the script with:

```bash
sh run_app.sh
```

The script will continuously monitor the input directory for new PNG files, process them, generate blog posts, and upload them to your Ghost blog.

## Logging

The script logs its activities to `script_log.txt` in the same directory as the script. You can monitor this file for information about the script's operations and any errors that occur.

## Bonus Script

There is a bonus script for removing ALL blog posts from your Ghost installation. Use with caution, as it was primarily used for testing:

```bash
python remove_posts.py
```

## Tools Used

- [Ollama](https://ollama.ai/)
- [llava-llama3](https://ollama.com/library/llava-llama3): A LLaVA model fine-tuned from Llama 3 Instruct with better scores in several benchmarks
- [Ollama Python Client](https://github.com/jmorganca/ollama-python)
- [Anthropic's Claude API](https://www.anthropic.com) (for remote LLM option)

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.