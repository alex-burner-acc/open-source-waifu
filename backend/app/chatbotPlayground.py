import os
import json
from openai import OpenAI
from dotenv import load_dotenv
from datetime import datetime, timedelta
from app.ai_waifu_prompt import AI_WAIFU_PROMPT
import uuid

# Load environment variables from .env file OL
load_dotenv()

# Set up OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def load_memories():
    try:
        with open('memories.json', 'r') as f:
            memories = json.load(f)
        # Add timestamps and IDs to existing memories if missing
        current_time = datetime.now().isoformat()
        for memory in memories:
            if 'timestamp' not in memory:
                memory['timestamp'] = current_time
            if 'id' not in memory:
                memory['id'] = str(uuid.uuid4())
        return prune_expired_memories(memories)
    except FileNotFoundError:
        return []

def save_memories(memories):
    existing_memories = load_memories()
    new_memories = [m for m in memories if not any(em['content'] == m['content'] for em in existing_memories)]
    updated_memories = existing_memories + new_memories
    with open('memories.json', 'w') as f:
        json.dump(updated_memories, f, default=str)

def prune_expired_memories(memories):
    current_time = datetime.now()
    return [
        memory for memory in memories
        if not is_memory_expired(memory, current_time)
    ]

def is_memory_expired(memory, current_time):
    timestamp = datetime.fromisoformat(memory['timestamp'])
    timeframe = memory['timeframe']
    
    if timeframe == 'day':
        return current_time - timestamp > timedelta(days=1)
    elif timeframe == 'week':
        return current_time - timestamp > timedelta(weeks=1)
    elif timeframe == 'indefinitely':
        return False
    else:
        return True  # Invalid timeframe, consider it expired

def chat_with_gpt():
    print("Welcome to the AI Waifu Assistant Terminal Interface! 💖")
    print("Type 'exit' to end the conversation.")
    
    memories = load_memories()
    new_memories = []
    conversation_history = [
        {"role": "system", "content": AI_WAIFU_PROMPT}
    ]
    
    while True:
        user_input = input("You: ")
        
        if user_input.lower() == 'exit':
            print("Sayonara, my love! 💕")
            save_memories(new_memories)
            break
        
        conversation_history.append({"role": "user", "content": user_input})
        
        try:
            response = client.chat.completions.create(
                model="gpt-4",
                messages=conversation_history + [{"role": "system", "content": f"Current memories: {[m['content'] for m in memories]}"}]
            )
            
            assistant_reply = response.choices[0].message.content
            
            # Check for memory commands
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
                    # Print the updated memories for debugging
                    print("DEBUG - New memory:", new_memory)
            
            print("AI Waifu:", assistant_reply)
            
            conversation_history.append({"role": "assistant", "content": assistant_reply})
            
        except Exception as e:
            print(f"Gomen nasai! An error occurred: {str(e)} 😢")

if __name__ == "__main__":
    chat_with_gpt()