import requests
import sys

def main():
    base_url = input("Enter the API base URL (e.g., http://127.0.0.1:5001): ").strip()
    if not base_url:
        print("Base URL cannot be empty.")
        sys.exit(1)

    try:
        response = requests.post(f"{base_url}/chat/start")
        response.raise_for_status()
        data = response.json()
        session_id = data.get("session_id")
        first_question = data.get("question")
        
        print(f"\nNew chat session started. Session ID: {session_id}")
        print("The agent will ask questions to complete the registration.")
        print("Type 'quit' to exit at any time.")
        print("-" * 30)
        print(f"Agent: {first_question}")

    except requests.exceptions.RequestException as e:
        print(f"Error starting chat session: {e}")
        sys.exit(1)

    while True:
        user_input = input("You: ")
        if user_input.lower() == 'quit':
            print("Exiting chat.")
            break

        try:
            chat_url = f"{base_url}/chat/{session_id}"
            payload = {"message": user_input}
            response = requests.post(chat_url, json=payload)
            response.raise_for_status()

            response_data = response.json()
            ai_message = response_data.get("response")

            print(f"Agent: {ai_message}")

            if response_data.get("status") == "completed":
                break

        except requests.exceptions.RequestException as e:
            print(f"An error occurred: {e}")
            if e.response:
                try:
                    print(f"Error details: {e.response.json()}")
                except ValueError:
                    print(f"Error details: {e.response.text}")
            break

if __name__ == "__main__":
    main()
