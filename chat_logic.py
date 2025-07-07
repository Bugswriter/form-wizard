import os
import json
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import ChatPromptTemplate

class ChatProcessor:
    def __init__(self):
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-1.5-flash-latest",
            api_key=os.getenv("GOOGLE_API_KEY"),
            temperature=0.7,
            response_mime_type="application/json"
        )

    def get_initial_state(self):
        with open('configs/hogwarts_form.json', 'r') as f:
            form_config = json.load(f)
        initial_data = {field["key"]: None for field in form_config["fields"]}
        # A more in-character and welcoming first message.
        first_question = "Greetings! Welcome to the official Hogwarts registration portal. I'm here to assist you. To begin, could you please provide the full name of the applicant?"
        return initial_data, first_question

    def process_message(self, user_input, current_data_state):
        # --- FIX: Read prompts every time to ensure they are fresh ---
        with open('prompts/SYSTEM_PROMPT', 'r') as f:
            system_prompt_template = f.read()
        with open('prompts/PERSONALITY_PROMPT', 'r') as f:
            personality_prompt = f.read()
        with open('configs/hogwarts_form.json', 'r') as f:
            form_config_str = f.read()
            
        formatted_system_prompt = system_prompt_template.format(personality_prompt=personality_prompt)
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", formatted_system_prompt),
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
        
        chain = prompt | self.llm

        try:
            response = chain.invoke({
                "form_config": form_config_str,
                "current_data": json.dumps(current_data_state, indent=2),
                "user_input": user_input
            })
            return json.loads(response.content)
        except (json.JSONDecodeError, TypeError) as e:
            raise ValueError(f"AI response was not valid JSON. Details: {e}")
        except Exception as e:
            raise
