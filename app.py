# app.py - DEEPAK'S SOCIAL MEDIA AI ASSISTANT (RENDER.COM PRODUCTION READY)
import os
import json
import uuid
from datetime import datetime
import requests
from flask import Flask, render_template, request, jsonify, Response, session
from flask_cors import CORS
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize Flask app - PRODUCTION SETUP
app = Flask(__name__, 
            template_folder='templates',  # templates folder specify karna jaruri hai
            static_folder='static')       # static files ke liye
app.secret_key = os.urandom(24)
CORS(app)

class DeepakSocialAI:
    def __init__(self):
        # Get API key from environment - Render.com ke liye
        self.api_key = os.getenv("GROQ_API_KEY") or os.environ.get("GROQ_API_KEY")
        
        if not self.api_key:
            raise ValueError("❌ GROQ_API_KEY not found in environment variables")
        
        # Configuration
        self.app_name = "Deepak's Social Media AI"
        self.developer = "Deepak"
        self.version = "3.0.0"
        
        # Available models
        self.models = {
            "Deepak Fast": "llama-3.1-8b-instant",
            "Deepak Smart": "llama-3.1-70b-versatile",
            "Deepak Multi": "mixtral-8x7b-32768",
        }
        
        # Default model
        self.current_model = self.models["Deepak Fast"]
        
        # Store chat history with dates
        self.sessions = {}
        
        print(f"✅ {self.app_name} initialized!")
        print(f"👨‍💻 Developer: {self.developer}")
        print(f"⚡ Default Model: {self.current_model}")
    
    def detect_social_media_request(self, message):
        """Improved social media detection"""
        message_lower = message.lower()
        
        social_keywords = {
            'twitter': ['twitter', 'tweet', 'x.com', 'x post', 'on twitter', 'viral tweet'],
            'linkedin': ['linkedin', 'linked in', 'professional post', 'on linkedin', 'linkedin post'],
            'instagram': ['instagram', 'insta', 'ig post', 'reel', 'on instagram', 'instagram post']
        }
        
        detected_platforms = []
        for platform, keywords in social_keywords.items():
            for keyword in keywords:
                if keyword in message_lower:
                    detected_platforms.append(platform)
                    break
        
        return list(set(detected_platforms))
    
    def format_for_social_media(self, content, platform):
        """Format content for specific social media platform"""
        if platform == 'twitter':
            if len(content) > 275:
                content = content[:272] + "..."
            hashtags = " #AI #Tech #DeepakAI"
            return content + hashtags
            
        elif platform == 'linkedin':
            hashtags = " #ArtificialIntelligence #Technology #Innovation #Career"
            return f"{content}\n\n🔹 Powered by Deepak's AI Assistant{hashtags}"
            
        elif platform == 'instagram':
            hashtags = " #AI #Tech #Innovation #Future #DeepakAI"
            return f"✨ {content} ✨\n\n👇 Comment your thoughts below!{hashtags}"
        
        return content
    
    def chat(self, message, session_id="default", stream=False):
        """Send message to Groq API"""
        try:
            # Get or create session
            if session_id not in self.sessions:
                self.sessions[session_id] = {
                    'chats': [],
                    'created_at': datetime.now().isoformat()
                }
            
            session_data = self.sessions[session_id]
            chat_history = session_data['chats']
            
            # Detect social media request
            platforms = self.detect_social_media_request(message)
            
            # Prepare system message
            current_year = datetime.now().year
            current_date = datetime.now().strftime("%B %d, %Y")
            
            if platforms:
                platform_text = ', '.join(platforms)
                system_message = f"""You are {self.app_name}. Current date: {current_date}, Year: {current_year}.
                
User wants content for {platform_text}. Create engaging, viral content suitable for these platforms. 
Provide 3 separate posts, each clearly numbered (1., 2., 3.). 
Each post should be self-contained, under 250 characters, and ready to post.
Make content current and relevant to {current_year} trends.
Format each post exactly like this:
1. [First tweet/post]
2. [Second tweet/post] 
3. [Third tweet/post]"""
            else:
                system_message = f"""You are {self.app_name}, created by {self.developer}. 
Current date: {current_date}, Year: {current_year}.
You are helpful, intelligent, and provide accurate, up-to-date information.
Be concise and clear in your responses."""
            
            # Prepare messages
            messages = [{"role": "system", "content": system_message}]
            
            # Add history
            for h in chat_history[-10:]:
                messages.append({"role": h["role"], "content": h["content"]})
            
            # Add current message
            messages.append({"role": "user", "content": message})
            
            # Prepare API request
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            data = {
                "model": self.current_model,
                "messages": messages,
                "max_tokens": 1500,
                "temperature": 0.8 if platforms else 0.7,
                "stream": stream
            }
            
            if stream:
                # Streaming response
                response = requests.post(
                    "https://api.groq.com/openai/v1/chat/completions",
                    headers=headers,
                    json=data,
                    stream=True,
                    timeout=60
                )
                
                def generate():
                    full_response = ""
                    try:
                        for line in response.iter_lines():
                            if line:
                                line_str = line.decode('utf-8')
                                if line_str.startswith('data: '):
                                    if line_str.strip() == 'data: [DONE]':
                                        break
                                    
                                    try:
                                        json_str = line_str[6:]
                                        if json_str.strip():
                                            chunk = json.loads(json_str)
                                            if 'choices' in chunk and chunk['choices']:
                                                content = chunk['choices'][0].get('delta', {}).get('content', '')
                                                if content:
                                                    full_response += content
                                                    yield content
                                    except json.JSONDecodeError:
                                        continue
                    
                    except Exception as e:
                        print(f"Streaming error: {e}")
                    
                    finally:
                        # Save to history
                        chat_history.append({
                            "role": "user", 
                            "content": message,
                            "timestamp": datetime.now().isoformat(),
                            "platforms": platforms
                        })
                        
                        chat_history.append({
                            "role": "assistant", 
                            "content": full_response,
                            "timestamp": datetime.now().isoformat(),
                            "platforms": platforms,
                            "message_id": str(uuid.uuid4())
                        })
                        
                        if len(chat_history) > 50:
                            chat_history = chat_history[-50:]
                        
                        session_data['chats'] = chat_history
                        self.sessions[session_id] = session_data
                
                return {
                    "success": True,
                    "stream": True, 
                    "generator": generate(),
                    "platforms": platforms,
                    "is_social_request": len(platforms) > 0
                }
            
            else:
                # Non-streaming response
                response = requests.post(
                    "https://api.groq.com/openai/v1/chat/completions",
                    headers=headers,
                    json=data,
                    timeout=60
                )
                
                if response.status_code == 200:
                    result = response.json()
                    
                    if 'choices' in result and result['choices']:
                        full_response = result['choices'][0]['message']['content']
                        
                        # Save to history
                        chat_history.append({
                            "role": "user", 
                            "content": message,
                            "timestamp": datetime.now().isoformat(),
                            "platforms": platforms
                        })
                        
                        chat_history.append({
                            "role": "assistant", 
                            "content": full_response,
                            "timestamp": datetime.now().isoformat(),
                            "platforms": platforms,
                            "message_id": str(uuid.uuid4())
                        })
                        
                        if len(chat_history) > 50:
                            chat_history = chat_history[-50:]
                        
                        session_data['chats'] = chat_history
                        self.sessions[session_id] = session_data
                        
                        return {
                            "success": True,
                            "response": full_response,
                            "platforms": platforms,
                            "is_social_request": len(platforms) > 0,
                            "message_id": str(uuid.uuid4())
                        }
                    else:
                        return {"success": False, "error": "No response from AI model"}
                else:
                    return {"success": False, "error": f"API Error: {response.status_code}"}
        
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def get_chat_history(self, session_id="default"):
        """Get formatted chat history"""
        if session_id in self.sessions:
            session_data = self.sessions[session_id]
            chats = session_data['chats']
            
            grouped_chats = {}
            for chat in chats:
                if 'timestamp' in chat:
                    date = chat['timestamp'][:10]
                    if date not in grouped_chats:
                        grouped_chats[date] = []
                    grouped_chats[date].append(chat)
            
            return {
                "success": True,
                "chats": chats,
                "grouped_chats": grouped_chats,
                "total_chats": len(chats),
                "session_created": session_data.get('created_at', '')
            }
        
        return {"success": False, "error": "Session not found"}
    
    def edit_message(self, session_id, message_id, new_content):
        """Edit a message in chat history"""
        if session_id in self.sessions:
            chats = self.sessions[session_id]['chats']
            
            for i, chat in enumerate(chats):
                if chat.get('message_id') == message_id:
                    chats[i]['content'] = new_content
                    chats[i]['edited'] = True
                    chats[i]['edited_at'] = datetime.now().isoformat()
                    
                    self.sessions[session_id]['chats'] = chats
                    return {"success": True, "message": "Message updated"}
            
            return {"success": False, "error": "Message not found"}
        
        return {"success": False, "error": "Session not found"}
    
    def switch_model(self, model_key):
        """Switch to different model"""
        if model_key in self.models:
            self.current_model = self.models[model_key]
            print(f"🔄 Model switched to {self.current_model}")
            return True
        return False
    
    def clear_history(self, session_id):
        """Clear chat history"""
        if session_id in self.sessions:
            self.sessions[session_id]['chats'] = []
            return True
        return False

# Create assistant instance
assistant = DeepakSocialAI()

# ========== FLASK ROUTES ==========

@app.route('/')
def home():
    """Main page - Render.com production ready"""
    try:
        return render_template('index.html')
    except Exception as e:
        print(f"Template error: {e}")
        # Fallback HTML agar template na mile
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Deepak's Social AI</title>
            <style>
                body { background: #0f172a; color: white; font-family: Arial; 
                       display: flex; justify-content: center; align-items: center; height: 100vh; }
                .container { text-align: center; }
                h1 { color: #60a5fa; }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>Deepak's Social Media AI Assistant</h1>
                <p>Loading application...</p>
                <script>setTimeout(() => location.reload(), 2000);</script>
            </div>
        </body>
        </html>
        """

@app.route('/api/chat', methods=['POST'])
def chat_api():
    """Handle chat requests"""
    try:
        data = request.get_json()
        message = data.get('message', '').strip()
        
        if not message:
            return jsonify({"success": False, "error": "Message is empty"})
        
        session_id = session.get('session_id', str(uuid.uuid4()))
        session['session_id'] = session_id
        
        stream = data.get('stream', False)
        result = assistant.chat(message, session_id, stream)
        
        if stream and 'generator' in result:
            def generate():
                platforms = result.get("platforms", [])
                yield f'data: {json.dumps({"type": "start", "platforms": platforms})}\n\n'
                
                for chunk in result['generator']:
                    if chunk:
                        yield f'data: {json.dumps({"type": "chunk", "content": chunk})}\n\n'
                
                yield f'data: {json.dumps({"type": "end", "platforms": platforms})}\n\n'
            
            return Response(generate(), mimetype='text/event-stream')
        else:
            return jsonify(result)
    
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route('/api/history', methods=['GET'])
def get_history():
    """Get chat history"""
    try:
        session_id = session.get('session_id', 'default')
        history = assistant.get_chat_history(session_id)
        return jsonify(history)
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route('/api/models', methods=['GET'])
def get_models():
    """Get available models"""
    models_list = [{"id": key, "name": key, "value": value} 
                   for key, value in assistant.models.items()]
    
    current_model_name = next((k for k, v in assistant.models.items() if v == assistant.current_model), "Unknown")
    
    return jsonify({
        "success": True,
        "app_name": assistant.app_name,
        "developer": assistant.developer,
        "models": models_list,
        "current_model": assistant.current_model,
        "current_model_name": current_model_name
    })

@app.route('/api/switch-model', methods=['POST'])
def switch_model_api():
    """Switch model"""
    try:
        data = request.get_json()
        model_key = data.get('model')
        
        if not model_key:
            return jsonify({"success": False, "error": "Model key required"})
        
        success = assistant.switch_model(model_key)
        
        if success:
            current_model_name = next((k for k, v in assistant.models.items() if v == assistant.current_model), "Unknown")
            return jsonify({
                "success": True,
                "message": f"Switched to {model_key} model",
                "current_model": assistant.current_model,
                "current_model_name": current_model_name
            })
        else:
            return jsonify({"success": False, "error": "Model not found"})
    
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route('/api/clear', methods=['POST'])
def clear_history_api():
    """Clear chat history"""
    try:
        session_id = session.get('session_id', 'default')
        success = assistant.clear_history(session_id)
        
        if success:
            return jsonify({"success": True, "message": "Chat history cleared"})
        else:
            return jsonify({"success": False, "error": "Failed to clear history"})
    
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route('/api/edit', methods=['POST'])
def edit_message():
    """Edit a message"""
    try:
        data = request.get_json()
        message_id = data.get('message_id')
        new_content = data.get('content', '').strip()
        
        if not message_id or not new_content:
            return jsonify({"success": False, "error": "Missing parameters"})
        
        session_id = session.get('session_id', 'default')
        result = assistant.edit_message(session_id, message_id, new_content)
        return jsonify(result)
    
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route('/health')
def health_check():
    """Health check for Render.com"""
    return jsonify({
        "status": "healthy",
        "service": assistant.app_name,
        "developer": assistant.developer,
        "version": assistant.version,
        "timestamp": datetime.now().isoformat()
    })

# ========== MAIN ==========

if __name__ == '__main__':
    print("=" * 60)
    print(f"🚀 {assistant.app_name} v{assistant.version}")
    print("=" * 60)
    print(f"👨‍💻 Developer: {assistant.developer}")
    print(f"⚡ Default Model: {assistant.current_model}")
    print("=" * 60)
    
    # Production settings for Render.com
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV') == 'development'
    app.run(host='0.0.0.0', port=port, debug=debug)
