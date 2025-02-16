from ..parse import Prompt

from typing import Literal, Optional, List
from dataclasses import dataclass
from openai import AsyncOpenAI
from selenium import webdriver
from bs4 import BeautifulSoup
import time
from datetime import datetime

class AutomationState:
    def __init__(self):
        self.client = AsyncOpenAI()
        self.last_error: Optional[str] = None
        self.page_source: Optional[str] = None
        self.current_url: Optional[str] = None
        self.header_content: Optional[str] = None
        self.body_content: Optional[str] = None

    async def summarize(self):
        prompt = """
You will be provided an AutomationState object that keeps track of the current state of a 
web scraping process collecting data to automatically build an ML model. You will be
given the following information:
1. current_url: The URL of the current page
2. header_content: The headers of the current page
3. body_content: The main content of the current page

Your job is to summarize this information in a way that is easy to understand the stage
of the web scraping process. The summary should be only 1 sentence long.

Example input:
    current_url: "https://en.wikipedia.org/wiki/Python_(programming_language)"
    header_content: ["Introduction", "History", "Features"]
    body_content: "Python is a high-level programming language known for its simplicity and readability."

Example output:
    Scraping Wikipedia page on Python programming language, found information about a high-level programming language, simplicity, and readability.

Here is the current state of the AutomationState object:
"""
        
        prompt_info = f"""
current_url: {self.current_url}
header_content: {self.header_content}
body_content: {self.body_content}
"""

        summary = await self.client.chat.completions.create(
            model="gpt-4o-mini-2024-07-18",
            messages=[{"role": "user", "content": prompt + prompt_info}]
        )
        summary = summary.choices[0].message.content.strip()

        if self.body_content is None:
            return "Extracting content..."
        return summary
@dataclass
class ThinkingStep:
    next_step: Literal["DONE", "NOT_DONE"]
    context: Optional[str] = None

    def __init__(self, response: str):
        response = response.strip()
        if response.startswith("DONE"):
            self.next_step = "DONE"
            self.context = response.replace("DONE:", "")
        elif response.startswith("NOT_DONE"):
            self.next_step = "NOT_DONE"
            self.context = response.replace("NOT_DONE:", "")

class Thinker:
    def __init__(self):
        self.client = AsyncOpenAI()

    def is_relevant(self, state: AutomationState, prompt: Prompt) -> bool:
        irrelevant_substrings = ["https://www.google", "https://www.bing"]
        for substring in irrelevant_substrings:
            if substring in state.current_url:
                return False
        return True

    async def think(self, state: AutomationState, prompt: Prompt) -> ThinkingStep:
        content_for_review = state.header_content
        if hasattr(state, 'detailed_content') and state.body_content:
            content_for_review = state.body_content

        thinking_prompt = f"""
        You are a web automation strategist. Analyze current state and decide next step.
        
        TASK: {prompt.webscraping_prompt}
        CURRENT URL: {state.current_url}
        CONTENT: {content_for_review}
        LAST ERROR: {state.last_error}
        PAGE CONTENT: {state.header_content}


        If this page has relevant information:
        1. Assess ALL available content in one go
        2. Determine if this satisfies the task completely
        3. Identify any missing information
        
        Respond with one of:
        DONE: [reached a page with all necessary information for the prompt]
        NOT_DONE: [provide information on what's missing and where to go next]
        """

        response = await self.client.chat.completions.create(
            model="gpt-4o-mini-2024-07-18",
            messages=[{"role": "system", "content": thinking_prompt}]
        )

        return ThinkingStep(response=response.choices[0].message.content.strip())

@dataclass
class ActionStep:
    action: str

    def __init__(self, action: str):
        self.action = self.clean_selenium_command(action)

    def clean_selenium_command(self, action):
        # Remove code block markers and whitespace
        cleaned = action.strip()
        cleaned = cleaned.replace('python', '')
        return cleaned.strip()

@dataclass
class Header:
    url: str
    headers: List[str]

@dataclass
class Body:
    url: str
    title: str
    main_text: str
    timestamp: str

class ContentExtractor:
    def extract_headers(self, state: AutomationState, page_url: str, page_source: str) -> Header:
        """Initial quick scan of page - just headers and basic content"""

        state.current_url = page_url

        soup = BeautifulSoup(page_source, 'html.parser')
        headers = [h.text for h in soup.find_all(['h1', 'h2', 'h3'])]
        
        return Header(url=page_url, headers=headers)

    def extract_body(self, page_url: str, page_source: str, prompt: Prompt) -> Body:
        soup = BeautifulSoup(page_source, 'html.parser')
        title = soup.find(id="firstHeading").text if soup.find(id="firstHeading") else ""

        # Get main content
        content_div = soup.find(id="mw-content-text")
        if content_div:
            # Find the first few paragraphs of actual content
            main_paragraphs = []
            for p in content_div.find_all('p', recursive=True):
                if p.text.strip() and not p.find_parent(class_='infobox'):
                    main_paragraphs.append(p.text.strip())
                if len(main_paragraphs) >= 3:  # Get first 3 substantive paragraphs
                    break

            main_text = '\n\n'.join(main_paragraphs)

            return Body(url=page_url, 
                        title=title, 
                        main_text=main_text, 
                        timestamp=datetime.now().strftime("%Y%m%d_%H%M%S"))

class Worker:
    def __init__(self):
        options = webdriver.ChromeOptions()
        options.add_argument("--start-maximized")
        self.driver = webdriver.Chrome(options=options)
        self.client = AsyncOpenAI()

    def current_url(self):
        return self.driver.current_url

    def page_source(self):
        return self.driver.page_source

    async def get_action(self, step: ThinkingStep, state: AutomationState, prompt: Prompt) -> ActionStep:
        action_prompt = f"""
        Convert step into Selenium command. Consider last error to avoid same issue.
        
        Step: {step.next_step}
        Context: {step.context}
        Current URL: {state.current_url}
        Last Error: {state.last_error}

        Return only the Selenium command, no explanations.
        Example: driver.get("https://www.google.com")

        Fixes to deprecated commands if they are used:
        - Use driver.find_element("name", "q") NOT find_element_by_name
        - Use driver.find_element("id", "search") NOT find_element_by_id
        - Use driver.find_element("xpath", "//div") NOT find_element_by_xpath
        """

        response = await self.client.chat.completions.create(
            model="gpt-4o-mini-2024-07-18",
            messages=[{"role": "system", "content": action_prompt}]
        )

        command = response.choices[0].message.content.strip()
        command = "self.worker." + command

        return ActionStep(command)

class Scraper:
    def __init__(self, max_attempts: int = 7):
        self.state = AutomationState()
        self.max_attempts = max_attempts
        self.thinker = Thinker()
        self.content_extractor = ContentExtractor()
        self.worker = None
        self.complete = False

    async def step(self, prompt) -> ThinkingStep | ActionStep:
        print("Updating state")
        self.state.current_url =  self.worker.current_url()
        self.state.page_source = self.worker.page_source()
        self.state.header_content = self.content_extractor.extract_headers(self.state,
            self.state.current_url, self.state.page_source)

        print("Header content:", self.state.header_content)
        if self.thinker.is_relevant(self.state, prompt):
            print("Relevant content found, extracting body")
            self.state.body_content = self.content_extractor.extract_body(self.state.current_url, 
                self.state.page_source, prompt)
        thinking_step: ThinkingStep = await self.thinker.think(self.state, prompt)
        if thinking_step.next_step == "DONE":
            return thinking_step
        else:
            print("Thinking step:", thinking_step)
            action_step: ActionStep = await self.worker.get_action(thinking_step, self.state, prompt)
            return action_step

    async def scrape_content(self, prompt: Prompt):
        self.worker = Worker()
        print("Starting scraping process")
        attempt = 0
        self.worker.driver.get("https://www.google.com")
        time.sleep(1)

        while attempt < self.max_attempts:
            print(f"Attempt {attempt + 1}")
            step = await self.step(prompt)
            if isinstance(step, ThinkingStep):
                print("Thinking step:", step.next_step)
                return
            elif isinstance(step, ActionStep):
                print("Action step:", step.action)
                try:
                    exec(step.action)
                except Exception as e:
                    print(e)
                    self.state.last_error = str(e)
                time.sleep(1)
            attempt += 1

        if attempt >= self.max_attempts:
            print("Maximum attempts reached without completing task")

        self.complete = True
        self.close()

    def close(self):
        if self.worker:
            self.worker.driver.quit()

if __name__ == "__main__":
    prompt = Prompt(webscraping_prompt="Extract the main content from the Wikipedia page on 'Python (programming language)'")
    scraper = Scraper()
    scraper.scrape_content(prompt)
    print(scraper.state.body_content)
    scraper.close()
