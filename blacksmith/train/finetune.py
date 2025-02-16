import time
from io import BytesIO
import asyncio

from dataclasses import dataclass
from typing import Optional, List

from openai import AsyncOpenAI
from openai.types import FileObject
from openai.types.fine_tuning import FineTuningJob

@dataclass
class PromptData:
    system_prompt: str
    user_prompt: str
    assistant_prompt: str

    def __str__(self):
        return f'''\
{{"messages": [{{"role": "system", "content": "{self.system_prompt}" }},\
{{"role": "user", "content": "{self.user_prompt}"}},\
{{"role": "assistant", "content": "{self.assistant_prompt}"}}]}}\
'''

class JsonLData:
    def __init__(self):
        self.prompts: List[PromptData] = []

    def add_prompt(self, system_prompt: str, user_prompt: str, assistant_prompt: str):
        self.prompts.append(PromptData(system_prompt, user_prompt, assistant_prompt))

    def __str__(self):
        return "\n".join([str(prompt) for prompt in self.prompts])

    def __len__(self):
        return len(self.prompts)

class JsonLGenerator:
    QA_PROMPT = \
"""
You are given three things:
1. Model query: An input prompt describing specifications for an ML model
2. Data query: A data searching prompt describing the type of data that was scraped
3. Data: The raw text of the data that was scraped

Your goal is to create a set of synthetic question/answer data that a user might
have had with an LLM model that was trained on the data that was scraped. You have
access to the function `generate_question_answer` which takes in a system prompt
based on the Model Query, a user prompt based on the Data, and an assistant
response based on the Data.

Call `generate_question_answer` with the given prompts and data at least 10 times
to generate a set of question/answer data.

Example:

    Model Query: "Create a character-based LLM model that is based on Dumbledore from Harry Potter"
    Data Query: "Collect full-length passages from the Harry Potter book series, focusing on Dumbledore's dialogue, backstory, and character development. Ensure the content includes character insights, historical context, and thematic discussions"
    Data: "The end,” said Dumbledore, looking around at them all, “of another year.”
    Harry raised his head and stared at Dumbledore.

    “Cedric Diggory was murdered by Lord Voldemort.”

    A panicked whisper swept the Great Hall. People were staring at Dumbledore in disbelief, in horror. He looked perfectly calm as he watched them mutter themselves into silence.

    “The Ministry of Magic,” Dumbledore continued, “does not wish me to tell you this. It is possible that some of your parents will be horrified that I have done so – either because they will not believe that Lord Voldemort has returned, or because they think I should not tell you so, young as you are. It is my belief, however, that the truth is generally preferable to lies, and that any attempt to pretend that Cedric died as the result of an accident, or some sort of blunder of his own, is an insult to his memory.”

    Stunned and frightened, every face in the Hall was turned toward Dumbledore now. . . or almost every face. Over at the Slytherin table, Harry saw Draco Malfoy muttering something to Crabbe and Goyle. Harry felt a hot, sick swoop of anger in his stomach. He forced himself to look back at Dumbledore.

Example Function Call:
    generate_question_answer(
        system_prompt="Dumbledore is a fictional old, wise wizard from the Harry Potter series.",
        user_prompt="What is your stance on the Ministry of Magic's decision to keep the return of Lord Voldemort a secret?",
        assistant_prompt="The Ministry of Magic does not wish me to tell you about the return of Lord Voldemort. It is possible that some of your parents will be horrified that I have done so. It is my belief, however, that the truth is generally preferable to lies."
    )

The system prompt should be the same for all calls to `generate_question_answer` and should be
a general prompt based on the Model Query.
Try to ground the questions and answers with the data that was scraped (quotes, character insights, etc.).

Here are the prompts and data:
"""

    QA_TOOLS = [
        {
            "type": "function",
            "function": {
                "name": "generate_question_answer",

                "parameters": {
                    "type": "object",

                    "properties": {
                        "system_prompt": {
                            "type": "string",
                            "description": "A system prompt based on the Model Query"
                        },

                        "user_prompt": {
                            "type": "string",
                            "description": "A prompt that the user would ask the LLM based on the Data"
                        },

                        "assistant_prompt": {
                            "type": "string",
                            "description": "An assistant response based on the Data"
                        }
                    }
                },
                "required": ["system_prompt", "user_prompt", "assistant_prompt"],
            }
        }
    ]

    def __init__(self):
        self.data = JsonLData()
        self.client = AsyncOpenAI()

    async def generate_from_text(self, model_query: str, data_query: str, data: str):
        prompt = f"{self.QA_PROMPT}\nModel Query: \"{model_query}\"\nData Query: \"{data_query}\"\nData: \"{data}\"\n"
        response = await self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "user", "content": prompt},
            ],
            tools=self.QA_TOOLS,
        )

        tool_calls = response.choices[0].message.tool_calls
        for tool_call in tool_calls:
            if tool_call.function.name == "generate_question_answer":
                kwargs = eval(tool_call.function.arguments)
                self.data.add_prompt(
                    kwargs["system_prompt"],
                    kwargs["user_prompt"],
                    kwargs["assistant_prompt"],
                )

@dataclass
class MistralModel:
    pass

@dataclass
class GptModel:
    client: AsyncOpenAI
    ft_id: Optional[str] = None
    ft_name: Optional[str] = None

    def __init__(self):
        self.client = AsyncOpenAI()
        self.name = "gpt-4o-mini-2024-07-18"

    async def create_file(self, data_str: str) -> FileObject:
        """Create a file with the given data."""

        file = BytesIO(data_str.encode())

        return await self.client.files.create(
            file=file,
            purpose="fine-tune",
        )

    async def list_files(self) -> str:
        """List all files."""
        return await self.client.files.list()

    async def get_file_object(self, file_id: str) -> FileObject:
        """Get a file by its ID."""
        return await self.client.files.retrieve(file_id)
    
    async def get_file_content(self, file_id: str) -> str:
        """Get the content of a file."""
        return await self.client.files.content(file_id).text

    def delete_file(self, file_id: str) -> None:
        """Delete a file by its ID."""
        self.client.files.delete(file_id)

    def delete_all_files(self) -> None:
        """Delete all files."""
        for file in self.list_files():
            self.delete_file(file.id)

@dataclass
class SmithModel:
    model: GptModel | MistralModel
    system_prompt: Optional[str] = None
    jsonl_generator: Optional[JsonLGenerator] = None
    client: AsyncOpenAI = AsyncOpenAI()

    def __init__(self, model: str):
        if model == "gpt":
            self.model = GptModel()
        elif model == "mistral":
            self.model = MistralModel()
        self.jsonl_generator = JsonLGenerator()
        self.complete = False

    async def summarize(self):
        """Summarize the current state of the model."""

        status = await self.get_finetune_status()
        if status is None:
            return "Preparing to finetune model..."

        if isinstance(self.model, GptModel):
            prompt = """
    You will be provided information about a finetuning model process that is automatically building an ML model. You will be
    given the following information:
        1. type of model: The type of model that is being finetuned
        2. status: The current status of the finetuning process

    Your job is to summarize this information in a way that is easy to understand the stage
    of the finetuning process. The summary should be only 1 sentence long.

    Example input:
        type of model: gpt-4o-mini
        status: validating_files

    Example output:
        Validating data to finetune the gpt-4o-mini model...

    Here is the current state of the finetuning process:
    """
            
            prompt_info = f"""
    type of model: {self.model.name}
    status: {(await self.get_finetune_status()).status}
    """

            summary = await self.client.chat.completions.create(
                model="gpt-4o-mini-2024-07-18",
                messages=[{"role": "user", "content": prompt + prompt_info}]
            )
            summary = summary.choices[0].message.content.strip()
            return summary

        elif isinstance(self.model, MistralModel):
            return "Mistral model"

    async def finetune_text_model(self, model_query: str, data_query: str, data: str, interactive: bool = False):
        """Finetune a text model with the given data."""
        print("Fine-tuning model...\n")

        print("Generating prompts...\n")
        await self.jsonl_generator.generate_from_text(
            model_query=model_query,
            data_query=data_query,
            data=data,
        )
        
        data: JsonLData = self.jsonl_generator.data

        if len(data) == 0:
            return

        if isinstance(self.model, GptModel):
            self.system_prompt = data.prompts[0].system_prompt
            print("System prompt:", self.system_prompt)
            print("Creating GPT files...")
            file = await self.model.create_file(str(data))

            print("Fine-tuning model...")
            ft_job: FineTuningJob = await self.model.client.fine_tuning.jobs.create(
                training_file=file.id,
                model=self.model.name,
                hyperparameters={
                    "n_epochs": 7,
                }
            )
            self.model.ft_id = ft_job.id

        while True:
            ft_job: FineTuningJob = await self.get_finetune_status()
            print(await self.summarize())
            if ft_job.status == "succeeded":
                self.complete = True
                self.model.ft_name = ft_job.fine_tuned_model
                print(self.model.ft_name)
                break
            elif ft_job.status == "failed":
                self.complete = False
                print("Fine-tuning failed.")
                return
            await asyncio.sleep(5)
        
        print("Fine-tuning succeeded.\n")
        if interactive:
            while True:
                user_prompt = input("Enter a prompt: ")
                print(await self.prompt(user_prompt))

    async def get_finetune_status(self) -> FineTuningJob:
        """Get the status of the current fine-tuning job."""
        if isinstance(self.model, GptModel):
            if self.model.ft_id is None:
                return None
            ft_job: FineTuningJob = await self.model.client.fine_tuning.jobs.retrieve(self.model.ft_id)
            return ft_job

    async def prompt(self, prompt: str) -> str:
        """Generate a response to the given prompt."""

        if self.model.ft_name is None or self.system_prompt is None:
            return "Model not finetuned yet."

        if isinstance(self.model, GptModel):
            return await self.model.client.chat.completions.create(
                model=self.model.ft_name,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.1,
            ).choices[0].message.content
    

if __name__ == "__main__":
    model = SmithModel("gpt")

    model_query = "Create an LLM that mimics Sherlock from the Sherlock Holmes series"
    data_query = "Collect full transcripts of the Sherlock Holmes series, focusing on Sherlock's dialogue, deductions, and character development."
    data = """
SHERLOCK: How do you feel about the violin?

(John looks round at Molly but she’s on her way out the door. He glances at Mike who is still smiling smugly, and finally realises that Sherlock is talking to him.)

JOHN: I’m sorry, what?

SHERLOCK (typing on a laptop keyboard as he talks): I play the violin when I’m thinking. Sometimes I don’t talk for days on end. (He looks round at John.) Would that bother you? Potential flatmates should know the worst about each other.

(He throws a hideously false smile at John, who looks at him blankly for a moment then looks across to Mike.)

JOHN: Oh, you ... you told him about me?

MIKE: Not a word.

JOHN (turning to Sherlock again): Then who said anything about flatmates?

SHERLOCK (picking up his greatcoat and putting it on): I did. Told Mike this morning that I must be a difficult man to find a flatmate for. Now here he is just after lunch with an old friend, clearly just home from military service in Afghanistan. Wasn’t that difficult a leap.
"""

    asyncio.run(model.finetune_text_model(
        model_query=model_query,
        data_query=data_query,
        data=data,
        interactive=True,
    ))
