import logging
import os
from flask import Blueprint, Flask, abort, jsonify, request
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
from openai import OpenAI

from app.chatbotPlayground import load_memories, save_memories, prune_expired_memories
from . import chat_api_bp  # Import the Blueprint
from app.ai_waifu_prompt import AI_WAIFU_PROMPT
import uuid
from datetime import datetime

logging.basicConfig(level=logging.INFO)

# Load environment variables and set up OpenAI client
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

@chat_api_bp.route('/chat', methods=['POST'])
def chat():
    data = request.json
    user_input = data.get('message')
    conversation_history = data.get('conversation_history', [])

    if not user_input:
        return jsonify({"error": "No message provided"}), 400

    memories = load_memories()
    simplified_memories = [f"{m['timestamp'].split('T')[0]}: {m['content']}" for m in memories]
    
    conversation_history.append({"role": "user", "content": user_input})
    
    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": AI_WAIFU_PROMPT},
                {"role": "system", "content": f"Current memories: {simplified_memories}"}
            ] + conversation_history
        )
        
        assistant_reply = response.choices[0].message.content
        
        new_memories = []
        if "<REMEMBER THIS FOR" in assistant_reply:
            memory_parts = assistant_reply.split("<REMEMBER THIS FOR ", 1)[1].split(">", 1)
            if len(memory_parts) == 2:
                timeframe, content = memory_parts[0].split(":", 1)
                new_memory = {
                    "id": str(uuid.uuid4()),
                    "timeframe": timeframe.strip(),
                    "content": content.strip(),
                    "timestamp": datetime.now().isoformat()
                }
                new_memories.append(new_memory)
                assistant_reply = memory_parts[1].strip()
                logging.info(f"New memory created: {new_memory}")

        # Save new memories
        if new_memories:
            save_memories(new_memories)

        # Log the user input and assistant reply
        logging.info(f"User input: {user_input}")
        logging.info(f"Assistant reply: {assistant_reply}")
        logging.info(f"Conversation history: {conversation_history}")

        conversation_history.append({"role": "assistant", "content": assistant_reply})

        return jsonify({
            "reply": assistant_reply,
            "conversation_history": conversation_history
        })

    except Exception as e:
        logging.error(f"An error occurred: {str(e)}")
        return jsonify({"error": "An error occurred during the chat"}), 500

@chat_api_bp.route('/memories', methods=['GET'])
def get_memories():
    memories = load_memories()
    return jsonify(memories)