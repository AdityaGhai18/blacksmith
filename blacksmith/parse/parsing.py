from enum import Enum
from typing import List, Dict, Optional
from together import Together
import json

#possible model choices
class MlModel(Enum):
    Gpt = "gpt4o-mini"
    Mistral = "mistral"

#possible data types and dat
class DataType(Enum):
    TEXT = "text"
    IMAGE = "image"

class PromptParser:
    def __init__(self, api_key=""):
        self.client = Together(api_key=api_key) 
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
   - Specify multiple diverse sources to scrape from (2-3 sources)
   - Request full text content, not just summaries or metadata
   - Include specific instructions about data format and structure
   - Target authoritative sources in the domain
   - Specify maximum amount of data needed (e.g., "a maximum of 10 examples")
   - In general be a bit liimited dont make the prompt too difficult or complex for the scraper. get relevant yet constrained amount of data


EXAMPLE INPUTS AND OUTPUTS:

Input: "I need a sentiment analysis model for customer reviews"
{
    "model_type": "gpt4o-mini",
    "data_type": "text",
    "webscraping_prompt": "Collect a maximum of 50 full-length customer reviews from major e-commerce platforms (Amazon, Best Buy, Walmart). For each review, capture: complete review text, star rating, product category, and verified purchase status. Focus on reviews longer than 50 words to ensure sufficient training content."
}

Input: "I want to build a chatbot that can respond to me about patent law"
{
    "model_type": "gpt4o-mini",
    "data_type": "text",
    "webscraping_prompt": "Collect comprehensive patent law content from: 1) Full text of patent law articles from law journals and legal blogs (LexisNexis, Westlaw, IPWatchdog), 2) Complete patent court decisions and legal opinions from USPTO and WIPO databases, 3) Patent law educational materials from top law schools, 4) Patent attorney forum discussions and Q&As. Gather at least 10 documents with full text content. Each document should include the complete text, not just summaries. Focus on recent content (last 5 years) but include seminal older cases and materials."
}

RESPOND WITH ONLY THE JSON OBJECT. NO OTHER TEXT."""
        
# """You are a model selection assistant. Your ONLY job is to output a JSON object that selects the right model and data collection strategy.

# STRICT RULES:
# 1. For model_type:
#    - Use "gpt4o-mini" for: text analysis, sentiment, classification tasks
#    - Use "mistral" for: code generation, structured data tasks

# 2. For data_type:
#    - Use "text" for: documents, reviews, articles, social media
#    - Use "image" for: visual recognition, image classification

# 3. For webscraping_prompt:
#    - Be specific about data sources
#    - Include data format requirements
#    - Specify any labels/annotations needed

# EXAMPLE INPUTS AND OUTPUTS:

# Input: "I need a sentiment analysis model for customer reviews"
# {
#     "model_type": "gpt4o-mini",
#     "data_type": "text",
#     "webscraping_prompt": "Collect customer reviews from e-commerce sites (Amazon, Yelp). Each review should include: text content, star rating (1-5), and timestamp"
# }

# Input: "Build me an image classifier for identifying cars"
# {
#     "model_type": "mistral",
#     "data_type": "image",
#     "webscraping_prompt": "Collect car images from automotive websites and dealerships. Each image should include: make, model, year, and viewing angle"
# }

# RESPOND WITH ONLY THE JSON OBJECT. NO OTHER TEXT."""

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

    def analyse_request(self, user_input: str) -> Dict:
        prompt = f"{self.system_prompt}\n\nUser Request: {user_input}"
        response = self.client.completions.create(
            model="meta-llama/Llama-3.3-70B-Instruct-Turbo",
            prompt=prompt,
            tools=self.tools,
            temperature=0.7,
            tool_choice="auto"
        )
        print(response)
        #print(json.dumps(response.choices[0].message.model_dump()['tool_calls'], indent=2))
        
        raw_text = response.choices[0].text
        # print(f"Raw response text: {raw_text}")
        
        try:
            import re
            json_pattern = r'\{[^{]*\}'  # Match first complete JSON object found in the shitstorm
            match = re.search(json_pattern, raw_text)
            if match:
                extracted_json = match.group()
                print(f"\nExtracted JSON string that will be parsed:\n{extracted_json}") 
                return json.loads(match.group())
            raise json.JSONDecodeError("No JSON found", raw_text, 0)
        except json.JSONDecodeError as e:
            print(f"JSON parsing error: {e}")
            return {
                "model_type": "wtf is this",
                "data_type": "i wanna die",
                "webscraping_prompt": "llms just arent fucking real cunt"
            }
        
if __name__ == "__main__":
    model = MlModel.Gpt
    print(model.value)
    api_key = '' 
    analyzer = PromptParser(api_key)
    user_request = "Create a character-based LLM model that is based on Dumbledore from Harry Potter"
    result = analyzer.analyse_request(user_request)
    print(json.dumps(result, indent=2))

    