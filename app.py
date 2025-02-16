import asyncio
import time
import requests
from blacksmith.parse import Prompt, MlModel
from blacksmith.scrape import Scraper

# host = "https://4017-2001-5a8-450b-4900-9555-6b3a-f17f-92e.ngrok-free.app"
# 
# x = requests.post(host + "/request_model/", params={"request": "Make a model that will speak like Sherlock Holmes"})
# 
# print("Prompt: ", x.text)
# 
# for i in range(100):
#     time.sleep(3)
# 
#     y = requests.get("https://4017-2001-5a8-450b-4900-9555-6b3a-f17f-92e.ngrok-free.app/request_stage/")
# 
#     print(y.text)

#$ async def main():
#$     prompt = Prompt(webscraping_prompt="Extract source code for the language Zig", model_type="gpt-4o-mini-2024-07-18", data_type="text")
#$     scraper = Scraper()
#$     await scraper.scrape_content(prompt)
#$     print(scraper.state.body_content)
#$     scraper.close()
#$ 
#$ asyncio.run(main())

host = "https://4017-2001-5a8-450b-4900-9555-6b3a-f17f-92e.ngrok-free.app"

x = requests.post(host + "/completions/", params={"request": "Who are you?"})

print("Prompt: ", x.text)
