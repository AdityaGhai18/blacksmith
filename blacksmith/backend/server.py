from ..parse import PromptParser, Prompt, MlModel
from ..scrape import Scraper, AutomationState
from ..train import SmithModel

import asyncio
from typing import Literal
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI()

origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

stage: Literal["parsing", "scraping", "finetuning", "deploying", "not_ready"] = "not_ready"
scraper = Scraper()
model = SmithModel("gpt")

@app.post("/request_model/")
async def request_model(request: str):
    print(request)
    prompt_parser = PromptParser()
    prompt = prompt_parser.analyze_request(request)

    asyncio.create_task(handle_model_request(request, prompt))

    return prompt.to_json()

@app.get("/request_stage/")
async def request_stage():
    if not scraper.complete: 
        stage = "scraping"
        summary = await scraper.state.summarize()
    elif not model.complete:
        stage = "finetuning"
        summary = await model.summarize()
    else:
        stage = "deploying"
        summary = "Deploying model..."
    return {"stage": stage, "summary": summary}

async def handle_model_request(request: str, prompt: Prompt):
    print("Handling model request")
    data = await scrape_data(prompt)
    model = await finetune_model(request, prompt.webscraping_prompt, data)
    return model

async def scrape_data(prompt: Prompt) -> AutomationState:
    print("Scraping data")
    await scraper.scrape_content(prompt)
    print("Scraping complete")
    return scraper.state

async def finetune_model(model_query: str, data_query: str, data: str):
    await model.finetune_text_model(model_query, data_query, data)
