from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from langchain_core.messages import HumanMessage
import sqlite3
from graph import graph_app

app = FastAPI(title="GigaCorp Multi-Agent Scheduler")

def init_db():
    conn = sqlite3.connect("appointments.db")
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS bookings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT,
            time TEXT,
            email TEXT
        )
    ''')
    conn.commit()
    conn.close()

init_db()

class ChatRequest(BaseModel):
    message: str
    thread_id: str

@app.post("/api/chat")
async def chat_endpoint(request: ChatRequest):
    config = {"configurable": {"thread_id": request.thread_id}}
    result = graph_app.invoke(
        {"messages": [HumanMessage(content=request.message)]}, 
        config=config
    )
    final_message = result["messages"][-1].content
    return {"reply": final_message}

@app.get("/")
async def get_ui():
    html_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>GigaCorp Assistant</title>
        <style>
            /* ChatGPT Style Full Screen CSS */
            body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #343541; color: #ececf1; margin: 0; padding: 0; display: flex; flex-direction: column; height: 100vh; }
            #header { background-color: #202123; padding: 15px; text-align: center; font-size: 1.2rem; font-weight: bold; border-bottom: 1px solid #444; }
            #chat-container { flex: 1; display: flex; flex-direction: column; overflow: hidden; width: 100%; }
            #chat-box { flex: 1; padding: 20px; overflow-y: auto; display: flex; flex-direction: column; gap: 20px; align-items: center; }
            
            /* Message Wrappers */
            .message-wrapper { width: 100%; max-width: 800px; display: flex; flex-direction: column; }
            .user-wrapper { align-items: flex-end; }
            .bot-wrapper { align-items: flex-start; }
            
            /* Chat Bubbles */
            .message { max-width: 80%; padding: 12px 18px; border-radius: 8px; line-height: 1.6; word-wrap: break-word; font-size: 1rem; }
            .user-msg { background-color: #10a37f; color: white; border-bottom-right-radius: 2px; }
            .bot-msg { background-color: #444654; color: #ececf1; border-bottom-left-radius: 2px; }
            
            /* Timestamp */
            .timestamp { font-size: 0.75rem; color: #8e8ea0; margin-top: 5px; }
            
            /* Input Area */
            #input-area { background-color: #343541; padding: 20px; border-top: 1px solid #565869; display: flex; justify-content: center; }
            .input-wrapper { display: flex; width: 100%; max-width: 800px; gap: 10px; }
            #user-input { flex: 1; padding: 15px; border: 1px solid #565869; background-color: #40414f; color: white; border-radius: 8px; outline: none; font-size: 1rem; }
            #user-input::placeholder { color: #8e8ea0; }
            #send-btn { background-color: #10a37f; color: white; border: none; padding: 15px 25px; border-radius: 8px; cursor: pointer; font-size: 1rem; transition: background 0.2s; font-weight: bold; }
            #send-btn:hover { background-color: #0b8c6d; }
        </style>
    </head>
    <body>
        <div id="header">GigaCorp Multi-Agent Assistant</div>
        <div id="chat-container">
            <div id="chat-box"></div>
            <div id="input-area">
                <div class="input-wrapper">
                    <input type="text" id="user-input" placeholder="Type your message here..." onkeypress="handleKeyPress(event)">
                    <button id="send-btn" onclick="sendMessage()">Send</button>
                </div>
            </div>
        </div>

        <script>
            const threadId = "user_" + Math.floor(Math.random() * 10000);
            const chatBox = document.getElementById('chat-box');
            const userInput = document.getElementById('user-input');

            // Naya function jisme time bhi add ho raha hai
            function appendMessage(sender, text, msgClass, wrapperClass) {
                const now = new Date();
                const timeString = now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

                const wrapper = document.createElement('div');
                wrapper.className = 'message-wrapper ' + wrapperClass;

                const div = document.createElement('div');
                div.className = 'message ' + msgClass;
                div.textContent = text;

                const timeDiv = document.createElement('div');
                timeDiv.className = 'timestamp';
                timeDiv.textContent = (sender === 'You' ? 'You • ' : 'Agent • ') + timeString;

                wrapper.appendChild(div);
                wrapper.appendChild(timeDiv);
                
                chatBox.appendChild(wrapper);
                chatBox.scrollTop = chatBox.scrollHeight;
            }

            async function sendMessage() {
                const text = userInput.value.trim();
                if (!text) return;

                appendMessage('You', text, 'user-msg', 'user-wrapper');
                userInput.value = '';
                
                // Loading state
                const tempId = Date.now();
                appendMessage('System', '...', 'bot-msg', 'bot-wrapper'); 
                chatBox.lastChild.id = tempId;

                try {
                    const response = await fetch('/api/chat', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ message: text, thread_id: threadId })
                    });
                    
                    const data = await response.json();
                    
                    // Remove loading bubble and add real response
                    document.getElementById(tempId).remove();
                    appendMessage('Agent', data.reply, 'bot-msg', 'bot-wrapper');
                } catch (error) {
                    document.getElementById(tempId).remove();
                    appendMessage('System', 'Error connecting to the agent.', 'bot-msg', 'bot-wrapper');
                }
            }

            function handleKeyPress(e) {
                if (e.key === 'Enter') sendMessage();
            }
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)