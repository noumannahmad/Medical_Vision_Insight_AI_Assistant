# from fastapi import FastAPI, File, UploadFile, Form, Request, HTTPException
# from fastapi.templating import Jinja2Templates
# from fastapi.staticfiles import StaticFiles
# from fastapi.responses import HTMLResponse, JSONResponse
# import base64
# import requests
# import io
# from PIL import Image
# from dotenv import load_dotenv
# import os
# import logging


# logging.basicConfig(level=logging.INFO)
# logger = logging.getLogger(__name__)


# load_dotenv()

# app = FastAPI()

# templates = Jinja2Templates(directory="templates")

# GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
# GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# if not GROQ_API_KEY:
#     raise ValueError("GROQ_API_KEY is not set in the .env file")

# @app.get("/", response_class=HTMLResponse)
# async def read_root(request: Request):
#     return templates.TemplateResponse("index.html", {"request": request})

# @app.post("/upload_and_query")
# async def upload_and_query(image: UploadFile = File(...), query: str = Form(...)):
#     try:
#         image_content = await image.read()
#         if not image_content:
#             raise HTTPException(status_code=400, detail="Empty file")
        
#         encoded_image = base64.b64encode(image_content).decode("utf-8")

#         try:
#             img = Image.open(io.BytesIO(image_content))
#             img.verify()
#         except Exception as e:
#             logger.error(f"Invalid image format: {str(e)}")
#             raise HTTPException(status_code=400, detail=f"Invalid image format: {str(e)}")


#         messages = [
#             {
#                 "role": "user",
#                 "content": [
#                     {"type": "text", "text": query},
#                     {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{encoded_image}"}}
#                 ]
#             }
#         ]

#         def make_api_request(model):
#             response = requests.post(
#                 GROQ_API_URL,
#                 json={
#                     "model": model,
#                     "messages": messages,
#                     "max_tokens": 1000
#                 },
#                 headers={
#                     "Authorization": f"Bearer {GROQ_API_KEY}",
#                     "Content-Type": "application/json"
#                 },
#                 timeout=30
#             )
#             return response

#         # Make requests to both models
#         llama1_response = make_api_request("meta-llama/llama-4-scout-17b-16e-instruct")
#         llama2_response = make_api_request("meta-llama/llama-4-maverick-17b-128e-instruct")

#         # Process responses
#         responses = {}
#         for model, response in [("llama1", llama1_response), ("llama2", llama2_response)]:
#             if response.status_code == 200:
#                 result = response.json()
#                 answer = result["choices"][0]["message"]["content"]
#                 logger.info(f"Processed response from {model} API: {answer[:100]}...")
#                 responses[model] = answer
#             else:
#                 logger.error(f"Error from {model} API: {response.status_code} - {response.text}")
#                 responses[model] = f"Error from {model} API: {response.status_code}"

#         return JSONResponse(status_code=200, content=responses)

#     except HTTPException as he:
#         logger.error(f"HTTP Exception: {str(he)}")
#         raise he
#     except Exception as e:
#         logger.error(f"An unexpected error occurred: {str(e)}")
#         raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")

# if __name__ == "__main__":
#     import uvicorn
#     uvicorn.run(app, port=8000)



from fastapi import FastAPI, File, UploadFile, Form, Request, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
from PIL import Image
import base64
import requests
import io
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# FastAPI app initialization
app = FastAPI(title="Image Upload & Query API", description="Upload an image and query AI models for responses.")

# Template directory for rendering HTML
templates = Jinja2Templates(directory="templates")

# API configuration
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if not GROQ_API_KEY:
    raise ValueError("Missing GROQ_API_KEY in .env file")

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request) -> HTMLResponse:
    """
    Render the homepage with the image upload form.
    
    Args:
        request (Request): The incoming HTTP request object.

    Returns:
        HTMLResponse: Rendered HTML page with the upload form.
    """
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/upload_and_query", response_class=JSONResponse)
async def upload_and_query(image: UploadFile = File(...), query: str = Form(...)) -> JSONResponse:
    """
    Handles image upload and text query, sends data to AI models, and returns their responses.

    Args:
        image (UploadFile): The uploaded image file.
        query (str): The text query to process along with the image.

    Returns:
        JSONResponse: Responses from the AI models or error messages.
    """
    try:
        # Read uploaded image content
        image_content = await image.read()
        if not image_content:
            raise HTTPException(status_code=400, detail="Uploaded file is empty")

        # Validate the image format
        try:
            img = Image.open(io.BytesIO(image_content))
            img.verify()
        except Exception as e:
            logger.error(f"Invalid image format: {str(e)}")
            raise HTTPException(status_code=400, detail=f"Invalid image format: {str(e)}")

        # Encode image as Base64
        encoded_image = base64.b64encode(image_content).decode("utf-8")

        # Prepare message payload
        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": query},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{encoded_image}"}}
                ]
            }
        ]

        def make_api_request(model: str) -> requests.Response:
            """
            Sends a request to the GROQ API for a specific model.

            Args:
                model (str): The model name.

            Returns:
                requests.Response: The API response object.
            """
            try:
                response = requests.post(
                    GROQ_API_URL,
                    json={"model": model, "messages": messages, "max_tokens": 1000},
                    headers={
                        "Authorization": f"Bearer {GROQ_API_KEY}",
                        "Content-Type": "application/json"
                    },
                    timeout=30
                )
                return response
            except requests.exceptions.RequestException as e:
                logger.error(f"Error making API request for {model}: {str(e)}")
                raise HTTPException(status_code=502, detail=f"API request failed for {model}")

        # Models to query
        models = {
            "llama1": "meta-llama/llama-4-scout-17b-16e-instruct",
            "llama2": "meta-llama/llama-4-maverick-17b-128e-instruct"
        }

        # Process responses from both models
        responses = {}
        for model_key, model_name in models.items():
            response = make_api_request(model_name)
            if response.status_code == 200:
                try:
                    result = response.json()
                    answer = result["choices"][0]["message"]["content"]
                    logger.info(f"Processed response from {model_key}: {answer[:100]}...")
                    responses[model_key] = answer
                except (KeyError, IndexError) as e:
                    logger.error(f"Malformed API response for {model_key}: {str(e)}")
                    responses[model_key] = "Malformed API response"
            else:
                logger.error(f"Error from {model_key}: {response.status_code} - {response.text}")
                responses[model_key] = f"API error: {response.status_code}"

        return JSONResponse(status_code=200, content=responses)

    except HTTPException as http_err:
        logger.error(f"HTTP Exception: {str(http_err)}")
        raise http_err
    except Exception as e:
        logger.exception("Unexpected error occurred")
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
