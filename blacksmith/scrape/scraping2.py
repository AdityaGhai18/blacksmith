from openai import OpenAI

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import time

# Set up Selenium WebDriver
options = webdriver.ChromeOptions()
options.add_argument("--start-maximized")
driver = webdriver.Chrome(options=options)

# OpenAI API Key (Replace with your actual key)
OPENAI_API_KEY = ""

client = OpenAI(organization="", api_key=OPENAI_API_KEY)



def clean_selenium_command(command):
    # Remove code block markers and whitespace
    cleaned = command.strip()
    cleaned = cleaned.removeprefix('```')
    cleaned = cleaned.removesuffix('\n```')
    return cleaned.strip()

# Function to get action from LLM
def get_llm_action(user_input, page_source):
    prompt = f"""
    You are an automation assistant controlling a web browser via Selenium.
    The user provides commands, and you generate Python Selenium actions.
    
    Current page source:
    {page_source[:5000]}  # Limit characters to avoid overload

    User input: "{user_input}"

    Respond with the Python Selenium command only, without explanation. DO NOT prefix with python.
    """

    response = client.chat.completions.create(
        model="gpt-4o-mini-2024-07-18",
        messages=[{"role": "system", "content": prompt}],
        # api_key=OPENAI_API_KEY,
    )

    # return response["choices"][0]["message"]["content"]
    print(response.choices[0].message.content)
    print(response)
    # return response.choices[0].message.content
    response_string = response.choices[0].message.content
    cleaned_command = clean_selenium_command(response_string)
    return cleaned_command    

# Interactive loop
try:
    driver.get("https://www.example.com")  # Change this to your desired URL
    time.sleep(2)  # Wait for the page to load

    while True:
        user_command = input("Enter your command (or 'exit' to quit): ").strip().lower()
        if user_command == "exit":
            break

        page_source = driver.page_source  # Get current page HTML
        selenium_command = get_llm_action(user_command, page_source)

        try:
            print(selenium_command)

            exec(selenium_command)  # Execute the generated Selenium command
        except Exception as e:
            print(f"Error executing command: {e}")

except Exception as e:
    print(f"An error occurred: {e}")

finally:
    driver.quit()