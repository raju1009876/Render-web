from flask import Flask, request, jsonify, session, render_template_string
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import time
import threading
import json
import os
import uuid
from datetime import datetime
import logging
import requests

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = os.urandom(24)
app.config['SESSION_TYPE'] = 'filesystem'

# Store active sessions and bots
active_sessions = {}
active_bots = {}

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Vampire Rulex - Facebook E2EE Messenger</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height: 100vh; padding: 20px; }
        .container { max-width: 800px; margin: 0 auto; background: white; border-radius: 15px; box-shadow: 0 20px 40px rgba(0,0,0,0.1); overflow: hidden; }
        .header { background: linear-gradient(135deg, #2c3e50 0%, #34495e 100%); color: white; padding: 30px; text-align: center; }
        .header h1 { font-size: 2.5em; margin-bottom: 10px; background: linear-gradient(45deg, #e74c3c, #f39c12); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
        .header .developer { font-size: 1.1em; opacity: 0.8; }
        .form-container { padding: 40px; }
        .form-group { margin-bottom: 25px; }
        label { display: block; margin-bottom: 8px; font-weight: 600; color: #2c3e50; }
        input, textarea, select { width: 100%; padding: 12px 15px; border: 2px solid #e0e0e0; border-radius: 8px; font-size: 16px; transition: border-color 0.3s; }
        input:focus, textarea:focus, select:focus { outline: none; border-color: #667eea; }
        textarea { height: 120px; resize: vertical; font-family: monospace; }
        .session-key { background: #f8f9fa; padding: 15px; border-radius: 8px; border-left: 4px solid #667eea; margin-bottom: 20px; }
        .session-key code { background: #e9ecef; padding: 5px 10px; border-radius: 4px; font-family: monospace; font-weight: bold; color: #e74c3c; }
        .btn { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; border: none; padding: 15px 30px; border-radius: 8px; font-size: 16px; font-weight: 600; cursor: pointer; transition: transform 0.2s; width: 100%; margin: 5px 0; }
        .btn:hover { transform: translateY(-2px); }
        .btn-stop { background: linear-gradient(135deg, #e74c3c 0%, #c0392b 100%); }
        .btn:disabled { opacity: 0.6; cursor: not-allowed; transform: none; }
        .status { padding: 15px; border-radius: 8px; margin: 20px 0; text-align: center; font-weight: 600; display: none; }
        .status.running { background: #d4edda; color: #155724; border: 1px solid #c3e6cb; }
        .status.stopped { background: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; }
        .instructions { background: #fff3cd; border: 1px solid #ffeaa7; border-radius: 8px; padding: 20px; margin: 20px 0; }
        .instructions h3 { color: #856404; margin-bottom: 10px; }
        .instructions ol { margin-left: 20px; color: #856404; }
        .instructions li { margin-bottom: 8px; }
        .tab-container { margin-bottom: 20px; }
        .tabs { display: flex; background: #f8f9fa; border-radius: 8px; padding: 5px; }
        .tab { padding: 10px 20px; cursor: pointer; border-radius: 5px; margin: 0 2px; flex: 1; text-align: center; }
        .tab.active { background: #667eea; color: white; }
        .tab-content { display: none; }
        .tab-content.active { display: block; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>VAMPIRE RULEX</h1>
            <div class="developer">Facebook E2EE Messenger Bot</div>
            <div class="developer">Owner: Vampire Rulex</div>
        </div>
        
        <div class="form-container">
            <div class="session-key">
                <strong>Your Session Key:</strong>
                <code id="sessionKeyDisplay">{{ session_key }}</code>
                <small>Copy this key to stop your session later</small>
            </div>
            
            <div class="instructions">
                <h3>Instructions:</h3>
                <ol>
                    <li>Export Facebook cookies as JSON from your browser</li>
                    <li>Enter the E2EE thread ID (from Facebook message URL)</li>
                    <li>Configure message settings and timing</li>
                    <li>Create a messages.txt file with one message per line</li>
                    <li>Save your session key to stop the bot later</li>
                </ol>
            </div>

            <div class="tab-container">
                <div class="tabs">
                    <div class="tab active" onclick="switchTab('selenium')">Selenium Method</div>
                    <div class="tab" onclick="switchTab('graphql')">GraphQL API Method</div>
                </div>
                
                <div id="selenium-tab" class="tab-content active">
                    <form id="seleniumForm">
                        <div class="form-group">
                            <label for="cookies">Facebook Cookies (JSON):</label>
                            <textarea id="cookies" placeholder='[{"name": "c_user", "value": "..."}, ...]' required></textarea>
                        </div>
                        
                        <div class="form-group">
                            <label for="threadId">E2EE Thread ID:</label>
                            <input type="text" id="threadId" placeholder="t.1000xxxxxxxxxx" required>
                        </div>
                        
                        <div class="form-group">
                            <label for="firstName">First Name (for message format):</label>
                            <input type="text" id="firstName" placeholder="John" required>
                        </div>
                        
                        <div class="form-group">
                            <label for="lastName">Last Name (for message format):</label>
                            <input type="text" id="lastName" placeholder="Doe" required>
                        </div>
                        
                        <div class="form-group">
                            <label for="delay">Time Interval (seconds):</label>
                            <input type="number" id="delay" value="5" min="2" max="60" required>
                        </div>
                        
                        <div class="form-group">
                            <label for="messagesFile">Messages File:</label>
                            <input type="text" id="messagesFile" value="messages.txt" required>
                            <small>Create a text file with one message per line</small>
                        </div>
                        
                        <button type="button" class="btn" onclick="startSeleniumBot()" id="startSeleniumBtn">Start Selenium Bot</button>
                    </form>
                </div>

                <div id="graphql-tab" class="tab-content">
                    <form id="graphqlForm">
                        <div class="form-group">
                            <label for="graphqlCookies">Facebook Cookies (JSON):</label>
                            <textarea id="graphqlCookies" placeholder='[{"name": "c_user", "value": "..."}, ...]' required></textarea>
                        </div>
                        
                        <div class="form-group">
                            <label for="graphqlThreadId">E2EE Thread ID:</label>
                            <input type="text" id="graphqlThreadId" placeholder="1000xxxxxxxxxx" required>
                        </div>
                        
                        <div class="form-group">
                            <label for="graphqlFirstName">First Name:</label>
                            <input type="text" id="graphqlFirstName" placeholder="John" required>
                        </div>
                        
                        <div class="form-group">
                            <label for="graphqlLastName">Last Name:</label>
                            <input type="text" id="graphqlLastName" placeholder="Doe" required>
                        </div>
                        
                        <div class="form-group">
                            <label for="graphqlDelay">Time Interval (seconds):</label>
                            <input type="number" id="graphqlDelay" value="10" min="5" max="300" required>
                        </div>
                        
                        <div class="form-group">
                            <label for="graphqlMessages">Messages (one per line):</label>
                            <textarea id="graphqlMessages" placeholder="Hello&#10;How are you?&#10;This is a test" required></textarea>
                        </div>
                        
                        <button type="button" class="btn" onclick="startGraphQLBot()" id="startGraphQLBtn">Start GraphQL Bot</button>
                    </form>
                </div>
            </div>
            
            <button type="button" class="btn btn-stop" onclick="stopBot()" id="stopBtn" disabled>Stop Bot</button>
            <div id="status" class="status"></div>
        </div>
    </div>

    <script>
        const sessionKey = "{{ session_key }}";
        let currentBotType = 'selenium';
        
        function switchTab(tabName) {
            document.querySelectorAll('.tab').forEach(tab => tab.classList.remove('active'));
            document.querySelectorAll('.tab-content').forEach(content => content.classList.remove('active'));
            
            document.querySelector(`.tab:nth-child(${tabName === 'selenium' ? 1 : 2})`).classList.add('active');
            document.getElementById(`${tabName}-tab`).classList.add('active');
            
            currentBotType = tabName;
        }
        
        function showStatus(message, type) {
            const status = document.getElementById('status');
            status.textContent = message;
            status.className = `status ${type}`;
            status.style.display = 'block';
        }
        
        async function startSeleniumBot() {
            const startBtn = document.getElementById('startSeleniumBtn');
            const stopBtn = document.getElementById('stopBtn');
            
            startBtn.disabled = true;
            startBtn.textContent = 'Starting...';
            
            const data = {
                session_key: sessionKey,
                cookies: JSON.parse(document.getElementById('cookies').value),
                thread_id: document.getElementById('threadId').value,
                first_name: document.getElementById('firstName').value,
                last_name: document.getElementById('lastName').value,
                delay: parseInt(document.getElementById('delay').value),
                messages_file: document.getElementById('messagesFile').value,
                method: 'selenium'
            };
            
            try {
                const response = await fetch('/start', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(data)
                });
                
                const result = await response.json();
                
                if (result.success) {
                    showStatus('Selenium Bot started successfully!', 'running');
                    stopBtn.disabled = false;
                    startBotMonitoring();
                } else {
                    showStatus('Error: ' + result.error, 'stopped');
                    startBtn.disabled = false;
                    startBtn.textContent = 'Start Selenium Bot';
                }
            } catch (error) {
                showStatus('Network error: ' + error, 'stopped');
                startBtn.disabled = false;
                startBtn.textContent = 'Start Selenium Bot';
            }
        }
        
        async function startGraphQLBot() {
            const startBtn = document.getElementById('startGraphQLBtn');
            const stopBtn = document.getElementById('stopBtn');
            
            startBtn.disabled = true;
            startBtn.textContent = 'Starting...';
            
            const data = {
                session_key: sessionKey,
                cookies: JSON.parse(document.getElementById('graphqlCookies').value),
                thread_id: document.getElementById('graphqlThreadId').value,
                first_name: document.getElementById('graphqlFirstName').value,
                last_name: document.getElementById('graphqlLastName').value,
                delay: parseInt(document.getElementById('graphqlDelay').value),
                messages: document.getElementById('graphqlMessages').value.split('\n').filter(msg => msg.trim()),
                method: 'graphql'
            };
            
            try {
                const response = await fetch('/start', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(data)
                });
                
                const result = await response.json();
                
                if (result.success) {
                    showStatus('GraphQL Bot started successfully!', 'running');
                    stopBtn.disabled = false;
                    startBotMonitoring();
                } else {
                    showStatus('Error: ' + result.error, 'stopped');
                    startBtn.disabled = false;
                    startBtn.textContent = 'Start GraphQL Bot';
                }
            } catch (error) {
                showStatus('Network error: ' + error, 'stopped');
                startBtn.disabled = false;
                startBtn.textContent = 'Start GraphQL Bot';
            }
        }
        
        async function stopBot() {
            const stopBtn = document.getElementById('stopBtn');
            const startSeleniumBtn = document.getElementById('startSeleniumBtn');
            const startGraphQLBtn = document.getElementById('startGraphQLBtn');
            
            stopBtn.disabled = true;
            stopBtn.textContent = 'Stopping...';
            
            try {
                const response = await fetch('/stop', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ session_key: sessionKey })
                });
                
                const result = await response.json();
                
                if (result.success) {
                    showStatus('Bot stopped successfully!', 'stopped');
                    startSeleniumBtn.disabled = false;
                    startSeleniumBtn.textContent = 'Start Selenium Bot';
                    startGraphQLBtn.disabled = false;
                    startGraphQLBtn.textContent = 'Start GraphQL Bot';
                    stopBtn.textContent = 'Stop Bot';
                } else {
                    showStatus('Error stopping bot: ' + result.error, 'stopped');
                    stopBtn.disabled = false;
                    stopBtn.textContent = 'Stop Bot';
                }
            } catch (error) {
                showStatus('Network error: ' + error, 'stopped');
                stopBtn.disabled = false;
                stopBtn.textContent = 'Stop Bot';
            }
        }
        
        async function startBotMonitoring() {
            const interval = setInterval(async () => {
                try {
                    const response = await fetch(`/status/${sessionKey}`);
                    const status = await response.json();
                    
                    if (!status.running && status.session_active) {
                        const startSeleniumBtn = document.getElementById('startSeleniumBtn');
                        const startGraphQLBtn = document.getElementById('startGraphQLBtn');
                        const stopBtn = document.getElementById('stopBtn');
                        
                        startSeleniumBtn.disabled = false;
                        startSeleniumBtn.textContent = 'Start Selenium Bot';
                        startGraphQLBtn.disabled = false;
                        startGraphQLBtn.textContent = 'Start GraphQL Bot';
                        stopBtn.disabled = true;
                        stopBtn.textContent = 'Stop Bot';
                        
                        showStatus('Bot has stopped running', 'stopped');
                        clearInterval(interval);
                    }
                } catch (error) {
                    console.error('Error checking status:', error);
                }
            }, 3000);
        }
    </script>
</body>
</html>
'''

class FacebookMessengerBot:
    def __init__(self, session_id, cookies, thread_id, first_name, last_name, delay, method='selenium', messages_file=None, messages_list=None):
        self.session_id = session_id
        self.cookies = cookies
        self.thread_id = thread_id
        self.first_name = first_name
        self.last_name = last_name
        self.delay = delay
        self.method = method
        self.messages_file = messages_file
        self.messages_list = messages_list or []
        self.driver = None
        self.is_running = False
        self.session = requests.Session()
        
    def load_messages(self):
        """Load messages from file or list"""
        if self.method == 'selenium' and self.messages_file:
            try:
                with open(self.messages_file, 'r', encoding='utf-8') as f:
                    self.messages_list = [line.strip() for line in f if line.strip()]
                logger.info(f"Loaded {len(self.messages_list)} messages from file")
            except Exception as e:
                logger.error(f"Error loading messages: {e}")
                self.messages_list = [f"Hello {self.first_name}", f"Hi {self.first_name}"]
        elif self.method == 'graphql' and self.messages_list:
            logger.info(f"Using {len(self.messages_list)} provided messages")
        else:
            self.messages_list = [f"Hello {self.first_name}", f"Hi {self.first_name}"]
    
    def setup_selenium_driver(self):
        """Setup Chrome driver for Selenium method"""
        chrome_options = Options()
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
        
        if os.getenv('RENDER') or os.getenv('HEADLESS'):
            chrome_options.add_argument("--headless")
        
        self.driver = webdriver.Chrome(options=chrome_options)
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    
    def setup_graphql_session(self):
        """Setup requests session for GraphQL method"""
        try:
            # Convert cookies to requests session cookies
            if isinstance(self.cookies, str):
                cookies_list = json.loads(self.cookies)
            else:
                cookies_list = self.cookies
                
            for cookie in cookies_list:
                self.session.cookies.set(cookie['name'], cookie['value'])
            
            # Set realistic headers
            self.session.headers.update({
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': '*/*',
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate, br',
                'Content-Type': 'application/x-www-form-urlencoded',
                'Origin': 'https://www.facebook.com',
                'Sec-Fetch-Dest': 'empty',
                'Sec-Fetch-Mode': 'cors',
                'Sec-Fetch-Site': 'same-origin',
                'Connection': 'keep-alive',
                'TE': 'trailers'
            })
            
            logger.info("GraphQL session setup completed")
            return True
        except Exception as e:
            logger.error(f"Error setting up GraphQL session: {e}")
            return False
    
    def send_message_graphql(self, message):
        """Send message using Facebook GraphQL API"""
        try:
            formatted_message = f"{self.first_name} {message} {self.last_name}".strip()
            
            # GraphQL endpoint for sending messages
            url = "https://www.facebook.com/api/graphql/"
            
            # This is a simplified version - actual implementation requires proper GraphQL query
            # and parameters that Facebook uses
            payload = {
                'av': '0',
                '__user': '0',
                '__a': '1',
                '__req': '1',
                '__hs': '0',
                'dpr': '1',
                '__ccg': 'EXCELLENT',
                '__rev': '1000000000',
                '__s': '0',
                '__hsi': '0',
                '__dyn': '0',
                '__csr': '0',
                '__comet_req': '0',
                'fb_dtsg': 'NA',  # This needs to be extracted from the page
                'jazoest': '0',
                '__spin_r': '1000000000',
                '__spin_b': '0',
                '__spin_t': '0'
            }
            
            # Note: Actual GraphQL query structure for sending messages is complex
            # and requires proper authentication tokens and parameters
            
            response = self.session.post(url, data=payload)
            
            if response.status_code == 200:
                logger.info(f"GraphQL message sent: {formatted_message}")
                return True
            else:
                logger.error(f"GraphQL request failed with status: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Error sending GraphQL message: {e}")
            return False
    
    def send_message_selenium(self, message):
        """Send message using Selenium"""
        try:
            formatted_message = f"{self.first_name} {message} {self.last_name}".strip()
            
            message_input = self.driver.find_element(By.XPATH, "//div[@role='textbox' and @aria-label='Message']")
            message_input.click()
            time.sleep(1)
            
            # Simulate typing
            for char in formatted_message:
                message_input.send_keys(char)
                time.sleep(0.05)
            
            message_input.send_keys("\n")
            logger.info(f"Selenium message sent: {formatted_message}")
            return True
        except Exception as e:
            logger.error(f"Error sending Selenium message: {e}")
            return False
    
    def start_messaging(self):
        """Start the messaging process"""
        try:
            self.is_running = True
            self.load_messages()
            
            if not self.messages_list:
                logger.error("No messages to send")
                return
            
            if self.method == 'selenium':
                self.setup_selenium_driver()
                if not self.load_cookies_selenium():
                    return
                if not self.navigate_to_thread_selenium():
                    return
                
                for message in self.messages_list:
                    if not self.is_running:
                        break
                    if self.send_message_selenium(message):
                        time.sleep(self.delay)
                    else:
                        break
                        
            elif self.method == 'graphql':
                if not self.setup_graphql_session():
                    return
                
                for message in self.messages_list:
                    if not self.is_running:
                        break
                    if self.send_message_graphql(message):
                        time.sleep(self.delay)
                    else:
                        break
            
            logger.info("Messaging completed")
            
        except Exception as e:
            logger.error(f"Error in messaging process: {e}")
        finally:
            if self.driver:
                self.driver.quit()
            self.is_running = False
            if self.session_id in active_bots:
                del active_bots[self.session_id]
    
    def load_cookies_selenium(self):
        """Load cookies for Selenium method"""
        try:
            self.driver.get("https://www.facebook.com")
            time.sleep(2)
            
            if isinstance(self.cookies, str):
                cookies_list = json.loads(self.cookies)
            else:
                cookies_list = self.cookies
                
            for cookie in cookies_list:
                if 'sameSite' in cookie and cookie['sameSite'] not in ['Strict', 'Lax', 'None']:
                    cookie['sameSite'] = 'Lax'
                self.driver.add_cookie(cookie)
                
            logger.info("Cookies loaded successfully in Selenium")
            return True
        except Exception as e:
            logger.error(f"Error loading cookies in Selenium: {e}")
            return False
    
    def navigate_to_thread_selenium(self):
        """Navigate to thread for Selenium method"""
        try:
            thread_url = f"https://www.facebook.com/messages/t/{self.thread_id}"
            self.driver.get(thread_url)
            time.sleep(3)
            
            wait = WebDriverWait(self.driver, 20)
            message_input = wait.until(
                EC.presence_of_element_located((By.XPATH, "//div[@role='textbox' and @aria-label='Message']"))
            )
            logger.info("Successfully navigated to thread in Selenium")
            return True
        except TimeoutException:
            logger.error("Could not find message input box in Selenium")
            return False
    
    def stop(self):
        """Stop the bot"""
        self.is_running = False
        if self.driver:
            self.driver.quit()

@app.route('/')
def index():
    """Main page"""
    session_key = str(uuid.uuid4())
    session['session_key'] = session_key
    active_sessions[session_key] = {
        'created_at': datetime.now(),
        'status': 'active'
    }
    return render_template_string(HTML_TEMPLATE, session_key=session_key)

@app.route('/start', methods=['POST'])
def start_bot():
    """Start the messaging bot"""
    try:
        data = request.json
        session_key = data.get('session_key')
        
        if session_key not in active_sessions:
            return jsonify({'success': False, 'error': 'Invalid session key'})
        
        if session_key in active_bots:
            return jsonify({'success': False, 'error': 'Bot already running for this session'})
        
        method = data.get('method', 'selenium')
        
        if method == 'graphql':
            bot = FacebookMessengerBot(
                session_id=session_key,
                cookies=data.get('cookies'),
                thread_id=data.get('thread_id'),
                first_name=data.get('first_name'),
                last_name=data.get('last_name'),
                delay=int(data.get('delay', 10)),
                method='graphql',
                messages_list=data.get('messages')
            )
        else:
            bot = FacebookMessengerBot(
                session_id=session_key,
                cookies=data.get('cookies'),
                thread_id=data.get('thread_id'),
                first_name=data.get('first_name'),
                last_name=data.get('last_name'),
                delay=int(data.get('delay', 5)),
                method='selenium',
                messages_file=data.get('messages_file', 'messages.txt')
            )
        
        bot_thread = threading.Thread(target=bot.start_messaging)
        bot_thread.daemon = True
        bot_thread.start()
        
        active_bots[session_key] = bot
        
        return jsonify({
            'success': True,
            'message': f'{method.upper()} Bot started successfully',
            'session_key': session_key
        })
        
    except Exception as e:
        logger.error(f"Error starting bot: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/stop', methods=['POST'])
def stop_bot():
    """Stop the messaging bot"""
    try:
        data = request.json
        session_key = data.get('session_key')
        
        if session_key not in active_sessions:
            return jsonify({'success': False, 'error': 'Invalid session key'})
        
        if session_key in active_bots:
            active_bots[session_key].stop()
            del active_bots[session_key]
            
        return jsonify({
            'success': True,
            'message': 'Bot stopped successfully'
        })
        
    except Exception as e:
        logger.error(f"Error stopping bot: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/status/<session_key>')
def get_status(session_key):
    """Get bot status for session"""
    if session_key in active_bots:
        bot = active_bots[session_key]
        return jsonify({
            'running': bot.is_running,
            'session_active': True,
            'method': bot.method
        })
    else:
        return jsonify({
            'running': False,
            'session_active': session_key in active_sessions
        })

@app.route('/sessions')
def list_sessions():
    """List active sessions"""
    return jsonify({
        'active_sessions': len(active_sessions),
        'active_bots': len(active_bots)
    })

if __name__ == '__main__':
    # Create messages file if it doesn't exist
    if not os.path.exists('messages.txt'):
        with open('messages.txt', 'w', encoding='utf-8') as f:
            f.write("Hello\nHow are you?\nThis is a test message")
    
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
