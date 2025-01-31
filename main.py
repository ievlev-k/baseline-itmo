import re
import time
from typing import List
from openai import OpenAI
from fastapi import FastAPI, HTTPException, Request, Response
from pydantic import HttpUrl
from schemas.request import PredictionRequest, PredictionResponse
from utils.logger import setup_logger
import requests
import os
from dotenv import load_dotenv, find_dotenv
# Initialize
app = FastAPI()
logger = None

client = OpenAI(
    base_url='http://host.docker.internal:11434/v1',
    api_key='ollama',
)


load_dotenv(find_dotenv())
google_key = os.getenv('GOOGLE_TOKEN')
cx_key = os.getenv('CS_KEY')

@app.on_event("startup")
async def startup_event():
    global logger
    logger = await setup_logger()


@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()

    body = await request.body()
    await logger.info(
        f"Incoming request: {request.method} {request.url}\n"
        f"Request body: {body.decode()}"
    )

    response = await call_next(request)
    process_time = time.time() - start_time

    response_body = b""
    async for chunk in response.body_iterator:
        response_body += chunk

    await logger.info(
        f"Request completed: {request.method} {request.url}\n"
        f"Status: {response.status_code}\n"
        f"Response body: {response_body.decode()}\n"
        f"Duration: {process_time:.3f}s"
    )

    return Response(
        content=response_body,
        status_code=response.status_code,
        headers=dict(response.headers),
        media_type=response.media_type,
    )


@app.post("/api/request", response_model=PredictionResponse)
async def predict(body: PredictionRequest):
    try:
        await logger.info(f"Processing prediction request with id: {body.id}")

        request = (f" Дай пояснение 1-3 предложениями."
                   f" После выведи 'ANSWER: номер правильного ответа'. "
                   f" Вопрос: {body.query} \n"
                   f" Ответь на русской языке. В ответе не должно быть китайский символов."
                   )


        query = body.query.splitlines()[0]

        if len(body.query.splitlines()) > 1:
            is_ans_choose = True
        else:
            is_ans_choose = False

        await logger.info(request)
        answer_text, answer_num = get_answer(request, is_ans_choose)

        await logger.info(f"Пояснение: {answer_text}")
        await logger.info(f"Ответ: {answer_num}")

        sources = get_links(query, is_ans_choose)


        response = PredictionResponse(
            id=body.id,
            answer=answer_num,
            reasoning=answer_text,
            sources=sources,
        )
        await logger.info(f"Successfully processed request {body.id}")
        return response
    except ValueError as e:
        error_msg = str(e)
        await logger.error(f"Validation error for request {body.id}: {error_msg}")
        raise HTTPException(status_code=400, detail=error_msg)
    except Exception as e:
        await logger.error(f"Internal error processing request {body.id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


def get_answer(req, is_ans_choose):
    response_ans = client.chat.completions.create(
        model="qwen2.5:7b",
        messages=[{"role": "user", "content": req}]
    )
    answer = response_ans.choices[0].message.content
    logger.info(f"Ответ от генератора: {answer}")
    match = re.search(r"ANSWER:\s*(\d+)", answer)
    if match and is_ans_choose:
        answer_num = match.group(1)
        answer_text = re.sub(r"ANSWER:\s*\d+", "", answer)

    else:
        answer_text = re.sub(r"ANSWER:\s*\d+", "", answer)
        answer_num = None
    return answer_text.strip(), answer_num



def get_links(query, is_ans_choose):
    url = f'https://www.googleapis.com/customsearch/v1?q={query}&key={google_key}&cx={cx_key}&num=10'
    response = requests.get(url)
    data = response.json()
    for item in data.get('items', []):
        cur_link = item['link']
        if "news.itmo.ru" in cur_link and "news" in cur_link and not is_ans_choose:
            current_sources: List[HttpUrl] = [
                HttpUrl(cur_link),
            ]
            return current_sources

    current_sources: List[HttpUrl] = [
        HttpUrl(data.get('items', [])[0]['link']),
        HttpUrl(data.get('items', [])[1]['link']),
        HttpUrl(data.get('items', [])[2]['link']),
    ]
    return current_sources
