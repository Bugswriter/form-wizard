import os
import json
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import ChatPromptTemplate

with open('prompts/SYSTEM_PROMPT', 'r') as f:
    SYSTEM_PROMPT = f.read()
with open('configs/hogwarts_form.json', 'r') as f:
    FORM_CONFIG = json.load(f)

class ChatProcessor:
    def __init__(self):
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-1.5-flash-latest",
            api_key=os.getenv("GOOGLE_API_KEY"),
            temperature=0.1,
            # This is crucial for forcing a JSON response
            response_mime_type="application/json"
        )
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", SYSTEM_PROMPT),
            ("human", """
Here is the information for this turn:

<form_config>
{form_config}
</form_config>

<current_data>
{current_data}
</current_data>

<user_input>
{user_input}
</user_input>
            """),
        ])
        self.chain = self.prompt | self.llm

    def get_initial_state(self):
        initial_data = {field["key"]: None for field in FORM_CONFIG["fields"]}
        first_question = ""
        for field in FORM_CONFIG["fields"]:
            if field["required"]:
                first_question = field["question"]
                break
        return initial_data, first_question

    def process_message(self, user_input, current_data_state):
        try:
            response = self.chain.invoke({
                "form_config": json.dumps(FORM_CONFIG, indent=2),
                "current_data": json.dumps(current_data_state, indent=2),
                "user_input": user_input
            })
            # The response.content from the model should already be a JSON string
            return json.loads(response.content)
        except (json.JSONDecodeError, TypeError) as e:
            # This is a fallback in case the API violates its contract
            raise ValueError(f"AI response was not valid JSON. Details: {e}")
        except Exception as e:
            raise
