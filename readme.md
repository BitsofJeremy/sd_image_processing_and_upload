# sd_image_processing_and_upload

My Stable Diffusion image save/archive processing workflow.

Read my blog post here for more details:

https://bits.jeremyschroeder.net/adding-ai-to-my-ai-art-worklfow-with-ollama-and-a-multimodal-llm/

## Install

Pull down the repo, create a virtualenv, activate and install requirements

```bash
git clone https://github.com/BitsofJeremy/sd_image_processing_and_upload.git
cd sd_image_processing_and_upload
virtualenv -p python3 venv
source venv/bin/activate
pip install -r requirements.txt
```

### Run it

Copy the env-example to .env and edit the file with your details

```bash
sh run_app.sh
```

#### Bonus script

There is a bonus script for removing ALL blog posts from your Ghost install. 
I used it for testing, and just left it in the repo as a bonus.

```bash
python remove_posts.py
```

### Tools Used: 
- https://ollama.ai/ 
- https://ollama.ai/library/llava
- https://github.com/jmorganca/ollama-python


