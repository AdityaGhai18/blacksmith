# blacksmith - Stanford TreeHacks 2025 Hackathon Project!

## What it does
Blacksmith is a no-code, text-only ML training and deployment automation platform. Buzzwords aside, all this means is you put in text, you get out ML models :) With just simple prompts like “Create an ML model based on George Washington”, you’ll get a personalized, historically accurate agent for the first president. Not only do you immediately have access to the chatbot just 10 minutes after you request your model, you also have an API endpoint that can then be as part of your larger multi-agent workflow.

Traditionally, this process is extremely tedious and impossible for someone who is just getting into machine learning. For finetuning models, data has to be manually scraped and collected, converted into a Q/A format, labeled, uploaded, and finetuned. For training models from scratch, it’s even worse! You need to set up the machine learning codebase yourself and be very very careful when training these sensitive models. We want machine learning to be accessible to everyone, with the power of personalized agents in every person and organization’s hands.

Blacksmith makes this possible. Given the text prompt, it first figures out the type of model and data that should be used. Then we use our extremely fast, custom, multi-agent Computer Use system to jump through webpages and extract raw data for our model. The data is automatically organized and labeled, then GPT and/or Mistral is used for the finetuning process.

Once the model is fully trained, you have access to the API endpoint and the chatbot, making the world your oyster!

Demo: https://www.youtube.com/watch?v=d9Wftder1oU

## How we built it
How we built it To create an end-to-end process that transforms a simple user prompt into a fully functional ML model, we developed a sophisticated multi-agent workflow system operating in three distinct phases:

Phase 1: Prompt Analysis Agent: Our initial agent performs deep analysis of the user's prompt through analysing three key aspects of what is required next in the workflow.

Model type selection: This agent determines whether to use OpenAI or Mistral's base models based on the specific use case requirements and performance characteristics. We use NLP techniques to parse user intent and map it to specific model architectures. For instance, if a user wants to create a customer service bot, the first thing this agent decides is its model.

Data type requirements: Simple selection of what needs datatypes need to be collected in order to train/finetune a machine learning model that suits our users needs; especially useful as we plan to incorporate vision and audio in future in addition to text

Web scraping prompt formulation: Transforms user requirements into sophisticated search strategies that combine domain-specific keywords with contextual parameters. For example, "customer service interactions" might be expanded to include "support tickets", "FAQ responses", and "resolution examples".

Phase 2: Intelligent Web Scraping Agents - Our dual-LLM architecture orchestrates sophisticated web scraping:

Thinking LLM: Functions as a strategic orchestrator for the scraping, maintaining a comprehensive understanding of the scraping mission's progress and goals. Continuously evaluating webpage content against the target data requirements, making real-time decisions about which content to extract and where to navigate next with state management. Incorporating learned patterns from successful data extraction attempts and adapting to different website structures.

Selenium Commander LLM: Translates high-level directives from the thinking LLM into precise, executable Selenium commands, handling complex scenarios, and optimizing scraping execution speed. These commands are directly executed using Seleniums computer use and are used to navigate the web and scrape useful data.

Phase 3: Model Fine-tuning & Deployment Agent

Data Processing & Formatting: Implements cleaning algorithms that normalize the scraped content, remove irrelevant information, and ensure consistency across different sources. Generates high-quality question-answer pairs from raw scraped data, ensuring each pair contributes meaningful finetuning signals to the model.

Model Training Integration: Manages the entire fine-tuning pipeline through direct integration with OpenAI and Mistral's APIs, handling authentication, data upload, and training monitoring.

Deployment Architecture: Implements a responsive chat interface that handles real-time model inference while maintaining low latency and high availability.

The result is a fully automated pipeline that transforms a simple user prompt into a production-ready, domain-specialized LLM, making advanced AI development accessible to non-technical users while maintaining enterprise-grade quality and reliability.
