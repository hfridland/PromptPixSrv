import os

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

models = client.models.list()

for model in models.data:
    if "image" in model.id or "dall-e" in model.id:
        print(model.id)

