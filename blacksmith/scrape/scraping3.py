from openai import OpenAI
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from bs4 import BeautifulSoup
import time
import json
from datetime import datetime

class AutomationState:
    def __init__(self):
        self.last_error = None                 
        self.page_source = None                 
        self.current_url = None                 
        self.extracted_content = None
        self.detailed_content = None           
        self.saved_content = []

def clean_selenium_command(command):
    # Remove code block markers and whitespace
    cleaned = command.strip()
    cleaned = cleaned.replace('python', '')
    return cleaned.strip()

def quick_extract_content(driver):
    """Initial quick scan of page - just headers and basic content"""
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    headers = [h.text for h in soup.find_all(['h1', 'h2', 'h3'])]
    
    return {
        'headers': headers[:5],
        'url': driver.current_url
    }

def detailed_extract_content(driver, task):
    driver.switch_to.window(driver.window_handles[-1])
    print(driver.page_source)
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    try:
        title = soup.find(id="firstHeading").text if soup.find(id="firstHeading") else ""
        
        # Get main content
        content_div = soup.find(id="mw-content-text")
        if content_div:
            # Find the first few paragraphs of actual content
            main_paragraphs = []
            for p in content_div.find_all('p', recursive=True):
                print(p)
                if p.text.strip() and not p.find_parent(class_='infobox'):
                    main_paragraphs.append(p.text.strip())
                if len(main_paragraphs) >= 3:  # Get first 3 substantive paragraphs
                    break
                    
            main_text = '\n\n'.join(main_paragraphs)
            
            return {
                'url': driver.current_url,
                'title': title,
                'main_text': main_text,
                'timestamp': datetime.now().isoformat()
            }
    except Exception as e:
        print(f"Extraction error: {e}")
        return None

def thinking_llm(task, state, client):
    # If we have detailed content, include it in the assessment
    content_for_review = state.extracted_content
    if hasattr(state, 'detailed_content') and state.detailed_content:
        content_for_review = state.detailed_content

    thinking_prompt = f"""
    You are a web automation strategist. Analyze current state and decide next step.
    
    TASK: {task}
    CURRENT URL: {state.current_url}
    CONTENT: {content_for_review}
    LAST ERROR: {state.last_error}
    PAGE CONTENT: {state.extracted_content}


    If this page has relevant information:
    1. Assess ALL available content in one go
    2. Determine if this satisfies the task completely
    3. Identify any missing information
    
    Respond with one of:
    FOUND_COMPLETE: [summary of found information]
    FOUND_PARTIAL: [what we have and what's missing]
    CONTINUE: [next step needed]
    """
    
    response = client.chat.completions.create(
        model="gpt-4o-mini-2024-07-18",
        messages=[{"role": "system", "content": thinking_prompt}]
    )
    return response.choices[0].message.content.strip()

def get_llm_action(step, state, client):
    action_prompt = f"""
    Convert step into Selenium command. Consider last error to avoid same issue.
    
    Step: {step}
    Current URL: {state.current_url}
    Last Error: {state.last_error}

    Return only the Selenium command, no explanations.
    Example: driver.get("https://www.google.com")

    Fixes to deprecated commands if they are used:
    - Use driver.find_element("name", "q") NOT find_element_by_name
    - Use driver.find_element("id", "search") NOT find_element_by_id
    - Use driver.find_element("xpath", "//div") NOT find_element_by_xpath
    """
    
    response = client.chat.completions.create(
        model="gpt-4o-mini-2024-07-18",
        messages=[{"role": "system", "content": action_prompt}]
    )
    
    clean_command = clean_selenium_command(response.choices[0].message.content.strip())

    return clean_command

def save_content(state, task):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"scraped_content_{timestamp}.json"
    
    output = {
        "task": task,
        "timestamp": timestamp,
        "content": state.saved_content
    }
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=4, ensure_ascii=False)
    
    print(f"Content saved to {filename}")

def main():
    options = webdriver.ChromeOptions()
    options.add_argument("--start-maximized")
    driver = webdriver.Chrome(options=options)
    
    OPENAI_API_KEY = ""
    client = OpenAI(organization="", api_key=OPENAI_API_KEY)
    
    state = AutomationState()
    
    try:
        task = input("Enter your task: ")
        max_attempts = 7
        attempt = 0
        
        driver.get("https://www.google.com")
        time.sleep(2)
        
        while attempt < max_attempts:
            try:
                # Initial quick scan
                state.current_url = driver.current_url
                print(state.current_url)
                state.extracted_content = quick_extract_content(driver)
                if "https://www.google" not in state.current_url and "https://www.bing" not in state.current_url:
                    print("Extracted content:", str(state.extracted_content))
                    # If content looks promising, do detailed extraction immediately
                    # if any(keyword in str(state.extracted_content).lower() for keyword in task.lower().split()):
                    print(state.extracted_content["headers"])
                    print(task.lower().split())
                    # if any(header.lower() in task.lower().split() for header in state.extracted_content["headers"]):
                    if "https://en.wikipedia" in state.current_url or "https://github.com" in state.current_url:
                        print("found detailed content, getting extracted stuff")
                        detailed_content = detailed_extract_content(driver, task)
                        if detailed_content:
                            state.detailed_content = detailed_content
                
                llm_response = thinking_llm(task, state, client)
                print(f"\nThinking LLM Response: {llm_response}")
                
                if llm_response.startswith("FOUND_COMPLETE:"):
                    state.saved_content.append(state.detailed_content)
                    print(f"Task completed! Saving content.")
                    save_content(state, task)
                    break
                    
                if llm_response.startswith("FOUND_PARTIAL:"):
                    state.saved_content.append(state.detailed_content)
                    print(f"Partial content found. Continuing search.")
                
                # Only get next action if we haven't found complete content
                if not llm_response.startswith("FOUND_COMPLETE:"):
                    selenium_command = get_llm_action(llm_response, state, client)
                    print(f"Executing: {selenium_command}")
                    
                    exec(selenium_command)
                    time.sleep(2)
                
            except Exception as e:
                print(f"Error: {e}")
                state.last_error = str(e)
                time.sleep(1)
            
            attempt += 1
            
        if attempt >= max_attempts:
            print("Maximum attempts reached without completing task")
            if state.saved_content:
                save_content(state, task)
            
    except Exception as e:
        print(f"Fatal error occurred: {e}")
        
    finally:
        driver.quit()

if __name__ == "__main__":
    main()
