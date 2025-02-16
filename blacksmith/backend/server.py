from ..parse import PromptParser, Prompt, MlModel
from ..scrape import Scraper, AutomationState
from ..train import SmithModel

import asyncio
from typing import Literal
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from openai import AsyncOpenAI

app = FastAPI()

origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

stage: Literal["parsing", "scraping", "finetuning", "deploying", "not_ready", "deployed"] = "not_ready"
scraper = Scraper()
model = SmithModel("gpt")
ft_model = "ft:gpt-4o-mini-2024-07-18:monet::B1IBTo3q"

@app.post("/request_model/")
async def request_model(request: str):
    print(request)
    prompt_parser = PromptParser()
    prompt = prompt_parser.analyze_request(request)

    asyncio.create_task(handle_model_request(request, prompt))

    return prompt.to_json()

@app.post("/completions/")
async def completions(request: str):
    print(request)
    print(model.system_prompt)
    client = AsyncOpenAI()
    if model.system_prompt is None:
        model.system_prompt = "You are Sherlock Holmes."
    response = await client.chat.completions.create(
            model=ft_model,
            messages=[
                {"role": "system", "content": model.system_prompt},
                {"role": "user", "content": request},
            ])
    return response.choices[0].message.content


@app.get("/request_stage/")
async def request_stage():
    global ft_model
    if not scraper.complete: 
        stage = "scraping"
        summary = await scraper.state.summarize()
    elif not model.complete:
        stage = "finetuning"
        summary = await model.summarize()
    else:
        stage = "deployed"
        summary = "Deployed with name: " + model.model.ft_name
        ft_model = model.model.ft_name
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
