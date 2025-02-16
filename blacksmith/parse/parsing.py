from dataclasses import dataclass
from enum import Enum
import json
from openai import OpenAI

class MlModel(Enum):
    Gpt = "gpt4o-mini"
    Mistral = "mistral"

@dataclass
class Prompt:
    model_type: MlModel
    data_type: str
    webscraping_prompt: str

    def to_json(self):
        return json.dumps({
            "model_type": self.model_type.value,
            "data_type": self.data_type,
            "webscraping_prompt": self.webscraping_prompt
        })

class PromptParser:
    def __init__(self):
        self.client = OpenAI()
        self.system_prompt = """You are a model selection assistant. Your ONLY job is to output a JSON object that selects the right model and data collection strategy.

STRICT RULES:
1. For model_type:
   - Use "gpt4o-mini" for: text analysis, sentiment, classification tasks
   - Use "mistral" for: code generation, structured data tasks

2. For data_type:
   - Use "text" for: documents, reviews, articles, social media
   - Use "image" for: visual recognition, image classification

3. For webscraping_prompt:
   - Focus on collecting decent amounts of raw text data suitable for model training
   - Ask for data from Wikipedia
   - Request full text content, not just summaries or metadata
   - Include specific instructions about data format and structure
   - Target authoritative sources in the domain
   - Specify maximum amount of data needed (e.g., "a maximum of 10 examples")
   - In general be a bit limited dont make the prompt too difficult or complex for the scraper. get relevant yet constrained amount of data

Limit the webscraping_prompt to 2 sentences.

EXAMPLE INPUTS AND OUTPUTS:

Input: "I want to build a chatbot that can respond to me about patent law"
{
    "model_type": "gpt4o-mini",
    "data_type": "text",
    "webscraping_prompt": "Collect comprehensive patent law content from Wikipedia. Focus on recent content (last 5 years) but include seminal older cases and materials."
}"""

        self.tools = [
            {
                "type": "function",
                "function": {
                    "name": "parse_ml_request",
                    "description": "selects the right model and data collection strategy",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "model_type": {
                                "type": "string",
                                "enum": [model.value for model in MlModel]
                            },
                            "data_type": {
                                "type": "string",
                                "enum": ["text", "image", "audio"]
                            },
                            "webscraping_prompt": {
                                "type": "string"
                            }
                        },
                        "required": ["model_type", "data_type", "webscraping_prompt"],
                        "additionalProperties": False
                    }
                }
            }
        ]

    def analyze_request(self, user_input: str) -> Prompt:
        prompt = f"{self.system_prompt}\n\nUser Request: {user_input}"
        response = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "user", "content": prompt},
            ],
            tools=self.tools,
        )
        for tool_call in response.choices[0].message.tool_calls:
            kwargs = eval(tool_call.function.arguments)

            return Prompt(
                model_type=MlModel(kwargs["model_type"]),
                data_type=kwargs["data_type"],
                webscraping_prompt=kwargs["webscraping_prompt"]
            )

if __name__ == "__main__":
    analyzer = PromptParser()
    user_request = "Create a character-based LLM model that is based on Dumbledore from Harry Potter"
    result = analyzer.analyze_request(user_request)
    print(result.to_json())
