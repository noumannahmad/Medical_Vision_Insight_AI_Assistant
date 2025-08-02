import base64
import requests
import io
from PIL import Image
from dotenv import load_dotenv
import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if not GROQ_API_KEY:
    raise ValueError("GROQ API KEY is not set in the .env file")

def process_image(image_path, query):
    try:
        with open(image_path, "rb") as image_file:
            image_content = image_file.read()
            encoded_image = base64.b64encode(image_content).decode("utf-8")
        try:
            img = Image.open(io.BytesIO(image_content))
            img.verify()
        except Exception as e:
            logger.error(f"Invalid image format: {str(e)}")
            return {"error": f"Invalid image format: {str(e)}"}
        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": query},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{encoded_image}"}}
                ]
            }
        ]
        def make_api_request(model):
            response = requests.post(
                GROQ_API_URL, 
                json={
                    "model": model, 
                    "messages": messages, 
                    "max_tokens": 1000
                },
                headers = {
                    "Authorization": f"Bearer {GROQ_API_KEY}",
                    "Content-Type": "application/json"
                },
                timeout = 30
            )
            return response
        
        llama_1_response = make_api_request("meta-llama/llama-4-scout-17b-16e-instruct")
        llama_2_response = make_api_request("meta-llama/llama-4-maverick-17b-128e-instruct")

        responses = {}
        for model, response in [("llama1", llama_1_response), ("llama2", llama_2_response)]:
            if response.status_code == 200:
                result = response.json()
                answer = result["choices"][0]["message"]["content"]
                logger.info(f"Processed response from {model} API : {answer}")
                responses[model] = answer
            else:
                logger.error(f"Error from {model} API : {response.status_code} - {response.text}")
                responses[model] = f"Error from {model} API : {response.status_code}"
        
        return responses

    except Exception as e:
        logger.error(f"An unexpected error occurred : {str(e)}")
        return {"error": f"An unexpected error occurred : {str(e)}"}

if __name__ == "__main__":
    image_path = "test1.png"
    query = "what are the encoders in this picture?"
    result = process_image(image_path, query)
    print(result)



