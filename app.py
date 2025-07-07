import os
import uuid
import json
from flask import Flask, request, jsonify
from dotenv import load_dotenv
from sqlalchemy.orm import Session
from db import init_db, get_db, ChatSession
from chat_logic import ChatProcessor

load_dotenv()

app = Flask(__name__)
MAX_LIMIT = int(os.getenv("MAX_USER_PROMPT_LIMIT", 300))
chat_processor = ChatProcessor()

with app.app_context():
    init_db()

@app.route('/chat/start', methods=['POST'])
def start_chat():
    db: Session = next(get_db())
    session_id = str(uuid.uuid4())
    
    initial_data, first_question = chat_processor.get_initial_state()
    
    new_session = ChatSession(
        id=session_id,
        form_data=json.dumps(initial_data)
    )
    db.add(new_session)
    db.commit()
    db.close()
    
    return jsonify({
        "session_id": session_id,
        "message": "Session started.",
        "question": first_question
    }), 201

@app.route('/chat/<string:session_id>', methods=['POST'])
def chat(session_id):
    db: Session = next(get_db())
    session = db.query(ChatSession).filter(ChatSession.id == session_id).first()

    if not session:
        return jsonify({"error": "Session not found"}), 404
    
    if session.is_completed:
        return jsonify({"error": "This chat session is already complete."}), 400

    data = request.json
    if not data or 'message' not in data:
        return jsonify({"error": "Message not provided"}), 400

    user_message = data['message']

    if len(user_message) > MAX_LIMIT:
        return jsonify({"error": f"Message exceeds max length of {MAX_LIMIT} characters."}), 413
    
    current_data_state = json.loads(session.form_data)
    
    try:
        ai_response = chat_processor.process_message(user_message, current_data_state)
    except Exception as e:
        app.logger.error(f"Error processing message for session {session_id}: {e}")
        return jsonify({"error": "Failed to process message with AI.", "details": str(e)}), 500

    session.form_data = json.dumps(ai_response.get("updated_data", current_data_state))
    
    if ai_response.get("is_complete"):
        session.is_completed = True
        response_payload = {
            "status": "completed",
            "response": ai_response.get("next_question", "Thank you! Registration is complete.")
        }
    else:
        response_payload = {
            "status": "in_progress",
            "response": ai_response.get("next_question", "Sorry, I am unsure how to proceed. Could you rephrase?")
        }

    db.commit()
    db.close()
    return jsonify(response_payload)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)
