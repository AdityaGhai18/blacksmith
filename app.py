import time
import requests
from blacksmith.parse import Prompt, MlModel
from blacksmith.scrape import Scraper

host = "https://4017-2001-5a8-450b-4900-9555-6b3a-f17f-92e.ngrok-free.app"

x = requests.post(host + "/request_model/", params={"request": "Make a model that will speak like Sherlock Holmes"})

print("Prompt: ", x.text)

for i in range(100):
    time.sleep(3)

    y = requests.get("https://4017-2001-5a8-450b-4900-9555-6b3a-f17f-92e.ngrok-free.app/request_stage/")

    print(y.text)
