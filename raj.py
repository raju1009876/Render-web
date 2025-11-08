from flask import Flask, request, jsonify, session, render_template_string, send_file
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
import tempfile

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
    <title>Vampire Rulex - Facebook Messenger</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height: 100vh; padding: 20px; }
        .container { max-width: 900px; margin: 0 auto; background: white; border-radius: 15px; box-shadow: 0 20px 40px rgba(0,0,0,0.1); overflow: hidden; }
        .header { background: linear-gradient(135deg, #2c3e50 0%, #34495e 100%); color: white; padding: 30px; text-align: center; }
        .header h1 { font-size: 2.5em; margin-bottom: 10px; background: linear-gradient(45deg, #e74c3c, #f39c12); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
        .header .developer { font-size: 1.1em; opacity: 0.8; }
        .form-container { padding: 40px; }
        .form-group { margin-bottom: 25px; }
        label { display: block; margin-bottom: 8px; font-weight: 600; color: #2c3e50; }
        input, textarea, select, button { width: 100%; padding: 12px 15px; border: 2px solid #e0e0e0; border-radius: 8px; font-size: 16px; transition: border-color 0.3s; }
        input:focus, textarea:focus, select:focus { outline: none; border-color: #667eea; }
        textarea { height: 120px; resize: vertical; font-family: monospace; }
        .session-key { background: #f8f9fa; padding: 15px; border-radius: 8px; border-left: 4px solid #667eea; margin-bottom: 20px; }
        .session-key code { background: #e9ecef; padding: 5px 10px; border-radius: 4px; font-family: monospace; font-weight: bold; color: #e74c3c; }
        .btn { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; border: none; padding: 15px 30px; border-radius: 8px; font-size: 16px; font-weight: 600; cursor: pointer; transition: transform 0.2s; margin: 5px 0; }
        .btn:hover { transform: translateY(-2px); }
        .btn-login { background: linear-gradient(135deg, #27ae60 0%, #2ecc71 100%); }
        .btn-stop { background: linear-gradient(135deg, #e74c3c 0%, #c0392b 100%); }
        .btn:disabled { opacity: 0.6; cursor: not-allowed; transform: none; }
        .status { padding: 15px; border-radius: 8px; margin: 20px 0; text-align: center; font-weight: 600; }
        .status.running { background: #d4edda; color: #155724; border: 1px solid #c3e6cb; }
        .status.stopped { background: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; }
        .status.login-success { background: #d1ecf1; color: #0c5460; border: 1px solid #bee5eb; }
        .instructions { background: #fff3cd; border: 1px solid #ffeaa7; border-radius: 8px; padding: 20px; margin: 20px 0; }
        .instructions h3 { color: #856404; margin-bottom: 10px; }
        .instructions ol { margin-left: 20px; color: #856404; }
        .instructions li { margin-bottom: 8px; }
        .step { margin-bottom: 30px; padding: 20px; border: 2px solid #e0e0e0; border-radius: 10px; }
        .step h3 { color: #2c3e50; margin-bottom: 15px; padding-bottom: 10px; border-bottom: 1px solid #e0e0e0; }
        .hidden { display: none; }
        .file-input { padding: 10px; border: 2px dashed #ccc; border-radius: 5px; text-align: center; cursor: pointer; }
        .file-input:hover { border-color: #667eea; }
        .message-preview { background: #f8f9fa; padding: 10px; border-radius: 5px; margin-top: 10px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>VAMPIRE RULEX</h1>
            <div class="developer">Facebook Messenger Bot</div>
            <div class="developer">Owner: Vampire Rulex</div>
        </div>
        
        <div class="form-container">
            <div id="status" class="status"></div>

            <!-- Step 1: Login with Cookies -->
            <div class="step" id="step1">
                <h3>Step 1: Login with Facebook Cookies</h3>
                <div class="form-group">
                    <label for="cookiesText">Paste Facebook Cookies (Text Format):</label>
                    <textarea id="cookiesText" placeholder="Paste your cookies in text format here...
Example:
c_user=123456789
xs=ABC123...
datr=XYZ...
..." required></textarea>
                    <small>Get cookies from browser developer tools (F12 → Application → Cookies)</small>
                </div>
                <button type="button" class="btn btn-login" onclick="loginWithCookies()" id="loginBtn">Login with Cookies</button>
            </div>

            <!-- Step 2: Session Management -->
            <div class="step hidden" id="step2">
                <h3>Step 2: Your Session</h3>
                <div class="session-key">
                    <strong>Session ID:</strong>
                    <code id="sessionIdDisplay"></code>
                    <small>Copy this Session ID to stop your session later</small>
                </div>
                <div class="form-group">
                    <label for="inputSessionId">Enter Session ID to Stop:</label>
                    <input type="text" id="inputSessionId" placeholder="Paste session ID here to stop">
                </div>
                <button type="button" class="btn btn-stop" onclick="stopSession()" id="stopBtn">Stop Session</button>
            </div>

            <!-- Step 3: Message Configuration -->
            <div class="step hidden" id="step3">
                <h3>Step 3: Configure Messaging</h3>
                <div class="form-group">
                    <label for="threadUrl">Facebook Thread URL:</label>
                    <input type="text" id="threadUrl" placeholder="https://www.facebook.com/messages/t/THREAD_ID or https://www.facebook.com/e2ee/t/THREAD_ID" required>
                    <small>Paste the complete Facebook message thread URL</small>
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
                    <label for="delay">Time Interval between messages (seconds):</label>
                    <input type="number" id="delay" value="10" min="5" max="300" required>
                </div>
                
                <div class="form-group">
                    <label for="messageFile">Choose Message File:</label>
                    <input type="file" id="messageFile" accept=".txt" required>
                    <small>Select a .txt file with one message per line</small>
                    <div id="filePreview" class="message-preview hidden"></div>
                </div>
                
                <button type="button" class="btn" onclick="startMessaging()" id="startBtn">Start Messaging</button>
            </div>
        </div>
    </div>

    <script>
        let currentSessionId = '';
        
        function showStatus(message, type) {
            const status = document.getElementById('status');
            status.textContent = message;
            status.className = `status ${type}`;
            status.style.display = 'block';
        }
        
        async function loginWithCookies() {
            const loginBtn = document.getElementById('loginBtn');
            const cookiesText = document.getElementById('cookiesText').value;
            
            if (!cookiesText.trim()) {
                showStatus('Please paste your cookies', 'stopped');
                return;
            }
            
            loginBtn.disabled = true;
            loginBtn.textContent = 'Logging in...';
            
            try {
                const response = await fetch('/login', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ cookies: cookiesText })
                });
                
                const result = await response.json();
                
                if (result.success) {
                    currentSessionId = result.session_id;
                    document.getElementById('sessionIdDisplay').textContent = currentSessionId;
                    document.getElementById('inputSessionId').value = currentSessionId;
                    
                    // Show next steps
                    document.getElementById('step1').classList.add('hidden');
                    document.getElementById('step2').classList.remove('hidden');
                    document.getElementById('step3').classList.remove('hidden');
                    
                    showStatus('✅ Login successful! Your Session ID: ' + currentSessionId, 'login-success');
                } else {
                    showStatus('Login failed: ' + result.error, 'stopped');
                }
            } catch (error) {
                showStatus('Network error: ' + error, 'stopped');
            } finally {
                loginBtn.disabled = false;
                loginBtn.textContent = 'Login with Cookies';
            }
        }
        
        async function stopSession() {
            const sessionId = document.getElementById('inputSessionId').value.trim();
            const stopBtn = document.getElementById('stopBtn');
            
            if (!sessionId) {
                showStatus('Please enter a Session ID', 'stopped');
                return;
            }
            
            stopBtn.disabled = true;
            stopBtn.textContent = 'Stopping...';
            
            try {
                const response = await fetch('/stop', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ session_id: sessionId })
                });
                
                const result = await response.json();
                
                if (result.success) {
                    showStatus('Session stopped successfully!', 'stopped');
                    if (sessionId === currentSessionId) {
                        currentSessionId = '';
                        document.getElementById('step2').classList.add('hidden');
                        document.getElementById('step3').classList.add('hidden');
                        document.getElementById('step1').classList.remove('hidden');
                    }
                } else {
                    showStatus('Error: ' + result.error, 'stopped');
                }
            } catch (error) {
                showStatus('Network error: ' + error, 'stopped');
            } finally {
                stopBtn.disabled = false;
                stopBtn.textContent = 'Stop Session';
            }
        }
        
        async function startMessaging() {
            const startBtn = document.getElementById('startBtn');
            const threadUrl = document.getElementById('threadUrl').value;
            const firstName = document.getElementById('firstName').value;
            const lastName = document.getElementById('lastName').value;
            const delay = document.getElementById('delay').value;
            const messageFile = document.getElementById('messageFile').files[0];
            
            if (!currentSessionId) {
                showStatus('Please login first', 'stopped');
                return;
            }
            
            if (!threadUrl || !firstName || !lastName || !messageFile) {
                showStatus('Please fill all fields', 'stopped');
                return;
            }
            
            startBtn.disabled = true;
            startBtn.textContent = 'Starting...';
            
            const formData = new FormData();
            formData.append('session_id', currentSessionId);
            formData.append('thread_url', threadUrl);
            formData.append('first_name', firstName);
            formData.append('last_name', lastName);
            formData.append('delay', delay);
            formData.append('message_file', messageFile);
            
            try {
                const response = await fetch('/start', {
                    method: 'POST',
                    body: formData
                });
                
                const result = await response.json();
                
                if (result.success) {
                    showStatus('Messaging started successfully!', 'running');
                } else {
                    showStatus('Error: ' + result.error, 'stopped');
                }
            } catch (error) {
                showStatus('Network error: ' + error, 'stopped');
            } finally {
                startBtn.disabled = false;
                startBtn.textContent = 'Start Messaging';
            }
        }
        
        // File preview functionality
        document.getElementById('messageFile').addEventListener('change', function(e) {
            const file = e.target.files[0];
            const preview = document.getElementById('filePreview');
            
            if (file) {
                const reader = new FileReader();
                reader.onload = function(e) {
                    const content = e.target.result;
                    const lines = content.split('\n').slice(0, 5); // Show first 5 lines
                    preview.innerHTML = '<strong>Preview (first 5 messages):</strong><br>' + 
                                       lines.map(line => '• ' + line.trim()).join('<br>');
                    preview.classList.remove('hidden');
                };
                reader.readAsText(file);
            } else {
                preview.classList.add('hidden');
            }
        });
        
        // Extract thread ID from URL helper
        document.getElementById('threadUrl').addEventListener('blur', function() {
            const url = this.value;
            if (url.includes('facebook.com/messages/t/') || url.includes('facebook.com/e2ee/t/')) {
                // URL is already in correct format
                showStatus('✅ Valid Facebook thread URL', 'login-success');
            } else if (url) {
                showStatus('⚠️ Please enter a valid Facebook message thread URL', 'stopped');
            }
        });
    </script>
</body>
</html>
'''

class FacebookMessengerBot:
    def __init__(self, session_id, cookies_dict, thread_url, first_name, last_name, delay, messages):
        self.session_id = session_id
        self.cookies_dict = cookies_dict
        self.thread_url = thread_url
        self.first_name = first_name
        self.last_name = last_name
        self.delay = delay
        self.messages = messages
        self.driver = None
        self.is_running = False
        
    def setup_driver(self):
        """Setup Chrome driver with realistic settings"""
        chrome_options = Options()
        
        # Realistic browser settings
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        
        # Headless mode for deployment
        if os.getenv('RENDER') or os.getenv('HEADLESS'):
            chrome_options.add_argument("--headless")
        
        try:
            self.driver = webdriver.Chrome(options=chrome_options)
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            return True
        except Exception as e:
            logger.error(f"Error setting up driver: {e}")
            return False
    
    def load_cookies_and_login(self):
        """Load cookies and verify login"""
        try:
            # First navigate to Facebook
            self.driver.get("https://www.facebook.com")
            time.sleep(3)
            
            # Clear existing cookies and add new ones
            self.driver.delete_all_cookies()
            
            for cookie_name, cookie_value in self.cookies_dict.items():
                if cookie_name and cookie_value:
                    cookie = {
                        'name': cookie_name.strip(),
                        'value': cookie_value.strip(),
                        'domain': '.facebook.com',
                        'path': '/',
                        'secure': True,
                        'httpOnly': False
                    }
                    try:
                        self.driver.add_cookie(cookie)
                    except Exception as e:
                        logger.warning(f"Could not set cookie {cookie_name}: {e}")
            
            # Refresh to apply cookies
            self.driver.get("https://www.facebook.com")
            time.sleep(3)
            
            # Check if login was successful
            if "login" in self.driver.current_url.lower() or "log in" in self.driver.page_source.lower():
                logger.error("Login failed - redirected to login page")
                return False
                
            # Check for user element
            user_indicators = [
                "//div[contains(@aria-label, 'Your profile')]",
                "//a[contains(@href, '/me/')]",
                "//span[contains(text(), 'Facebook')]"
            ]
            
            for indicator in user_indicators:
                try:
                    element = WebDriverWait(self.driver, 10).until(
                        EC.presence_of_element_located((By.XPATH, indicator))
                    )
                    if element:
                        logger.info("Login successful - user element found")
                        return True
                except:
                    continue
            
            # If we can access messages, consider it successful
            self.driver.get("https://www.facebook.com/messages")
            time.sleep(3)
            if "messages" in self.driver.current_url:
                logger.info("Login successful - can access messages")
                return True
                
            logger.error("Login verification failed")
            return False
            
        except Exception as e:
            logger.error(f"Error during login: {e}")
            return False
    
    def navigate_to_thread(self):
        """Navigate to the message thread"""
        try:
            # Use the provided URL directly
            self.driver.get(self.thread_url)
            time.sleep(5)
            
            # Wait for message input box with multiple possible selectors
            selectors = [
                "//div[@role='textbox' and @aria-label='Message']",
                "//div[@contenteditable='true' and @role='textbox']",
                "//div[contains(@class, 'notranslate') and @contenteditable='true']",
                "//div[@aria-label='Message']"
            ]
            
            for selector in selectors:
                try:
                    wait = WebDriverWait(self.driver, 15)
                    message_input = wait.until(
                        EC.presence_of_element_located((By.XPATH, selector))
                    )
                    if message_input:
                        logger.info("Successfully navigated to thread and found message input")
                        return True
                except TimeoutException:
                    continue
            
            logger.error("Could not find message input box with any selector")
            return False
            
        except Exception as e:
            logger.error(f"Error navigating to thread: {e}")
            return False
    
    def format_message(self, base_message):
        """Format message with first and last name"""
        return f"{self.first_name} {base_message} {self.last_name}".strip()
    
    def send_message(self, message):
        """Send a single message"""
        try:
            formatted_message = self.format_message(message)
            
            # Find message input box with multiple selectors
            selectors = [
                "//div[@role='textbox' and @aria-label='Message']",
                "//div[@contenteditable='true' and @role='textbox']",
                "//div[contains(@class, 'notranslate') and @contenteditable='true']"
            ]
            
            message_input = None
            for selector in selectors:
                try:
                    message_input = self.driver.find_element(By.XPATH, selector)
                    if message_input:
                        break
                except:
                    continue
            
            if not message_input:
                logger.error("Could not find message input element")
                return False
            
            message_input.click()
            time.sleep(1)
            
            # Clear any existing text
            message_input.clear()
            time.sleep(1)
            
            # Type message character by character
            for char in formatted_message:
                message_input.send_keys(char)
                time.sleep(0.05)  # Fixed typing delay
            
            # Send message
            message_input.send_keys("\n")
            logger.info(f"Message sent: {formatted_message}")
            
            # Wait a bit after sending
            time.sleep(2)
            return True
            
        except Exception as e:
            logger.error(f"Error sending message: {e}")
            return False
    
    def start_messaging(self):
        """Start the messaging process"""
        try:
            self.is_running = True
            
            if not self.messages:
                logger.error("No messages to send")
                return
            
            if not self.setup_driver():
                return
            
            if not self.load_cookies_and_login():
                return
            
            if not self.navigate_to_thread():
                return
            
            # Send messages in sequence
            for message in self.messages:
                if not self.is_running:
                    logger.info("Messaging stopped by user")
                    break
                    
                if self.send_message(message):
                    logger.info(f"Waiting {self.delay} seconds before next message")
                    time.sleep(self.delay)
                else:
                    logger.error("Failed to send message, stopping")
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
    
    def stop(self):
        """Stop the bot"""
        self.is_running = False
        if self.driver:
            try:
                self.driver.quit()
            except:
                pass

def parse_cookies_text(cookies_text):
    """Parse cookies from text format to dictionary"""
    cookies_dict = {}
    lines = cookies_text.strip().split('\n')
    
    for line in lines:
        line = line.strip()
        if '=' in line:
            # Handle different formats
            if '\t' in line:  # Tab-separated
                parts = line.split('\t')
            else:  # Standard format
                parts = line.split('=', 1)
            
            if len(parts) >= 2:
                key = parts[0].strip()
                value = parts[1].split(';')[0].strip()  # Remove trailing semicolon and attributes
                if key and value:
                    cookies_dict[key] = value
    
    logger.info(f"Parsed {len(cookies_dict)} cookies")
    return cookies_dict

def extract_thread_id_from_url(url):
    """Extract thread ID from Facebook URL"""
    try:
        if '/messages/t/' in url:
            return url.split('/messages/t/')[-1].split('/')[0].split('?')[0]
        elif '/e2ee/t/' in url:
            return url.split('/e2ee/t/')[-1].split('/')[0].split('?')[0]
        else:
            return url
    except:
        return url

@app.route('/')
def index():
    """Main page"""
    return render_template_string(HTML_TEMPLATE)

@app.route('/login', methods=['POST'])
def login():
    """Login with cookies and create session"""
    try:
        data = request.json
        cookies_text = data.get('cookies', '').strip()
        
        if not cookies_text:
            return jsonify({'success': False, 'error': 'No cookies provided'})
        
        # Parse cookies from text
        cookies_dict = parse_cookies_text(cookies_text)
        
        if not cookies_dict:
            return jsonify({'success': False, 'error': 'Could not parse cookies from text'})
        
        # Create session
        session_id = str(uuid.uuid4())
        
        # Test login with cookies
        test_bot = FacebookMessengerBot(session_id, cookies_dict, "https://www.facebook.com", "", "", 0, [])
        if not test_bot.setup_driver():
            return jsonify({'success': False, 'error': 'Failed to setup browser'})
        
        login_success = test_bot.load_cookies_and_login()
        test_bot.stop()
        
        if not login_success:
            return jsonify({'success': False, 'error': 'Login failed - invalid cookies'})
        
        # Store session
        active_sessions[session_id] = {
            'cookies_dict': cookies_dict,
            'created_at': datetime.now(),
            'status': 'logged_in'
        }
        
        return jsonify({
            'success': True,
            'session_id': session_id,
            'message': 'Login successful! Your session has been created.'
        })
        
    except Exception as e:
        logger.error(f"Login error: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/start', methods=['POST'])
def start_bot():
    """Start the messaging bot"""
    try:
        session_id = request.form.get('session_id')
        thread_url = request.form.get('thread_url')
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        delay = int(request.form.get('delay', 10))
        message_file = request.files.get('message_file')
        
        if not all([session_id, thread_url, first_name, last_name, message_file]):
            return jsonify({'success': False, 'error': 'Missing required fields'})
        
        if session_id not in active_sessions:
            return jsonify({'success': False, 'error': 'Invalid session ID. Please login first.'})
        
        if session_id in active_bots:
            return jsonify({'success': False, 'error': 'Bot already running for this session'})
        
        # Read messages from file
        messages_content = message_file.read().decode('utf-8')
        messages = [line.strip() for line in messages_content.split('\n') if line.strip()]
        
        if not messages:
            return jsonify({'success': False, 'error': 'No messages found in file'})
        
        # Get cookies from session
        cookies_dict = active_sessions[session_id]['cookies_dict']
        
        # Create and start bot
        bot = FacebookMessengerBot(
            session_id=session_id,
            cookies_dict=cookies_dict,
            thread_url=thread_url,
            first_name=first_name,
            last_name=last_name,
            delay=delay,
            messages=messages
        )
        
        # Start bot in separate thread
        bot_thread = threading.Thread(target=bot.start_messaging)
        bot_thread.daemon = True
        bot_thread.start()
        
        active_bots[session_id] = bot
        active_sessions[session_id]['status'] = 'messaging'
        
        return jsonify({
            'success': True,
            'message': f'Messaging started! Sending {len(messages)} messages with {delay} second intervals.'
        })
        
    except Exception as e:
        logger.error(f"Error starting bot: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/stop', methods=['POST'])
def stop_bot():
    """Stop the messaging bot"""
    try:
        data = request.json
        session_id = data.get('session_id')
        
        if not session_id:
            return jsonify({'success': False, 'error': 'No session ID provided'})
        
        if session_id in active_bots:
            active_bots[session_id].stop()
            del active_bots[session_id]
            
        if session_id in active_sessions:
            active_sessions[session_id]['status'] = 'stopped'
            
        return jsonify({
            'success': True,
            'message': 'Session stopped successfully'
        })
        
    except Exception as e:
        logger.error(f"Error stopping bot: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/status/<session_id>')
def get_status(session_id):
    """Get bot status for session"""
    if session_id in active_bots:
        bot = active_bots[session_id]
        return jsonify({
            'running': bot.is_running,
            'session_active': True
        })
    else:
        return jsonify({
            'running': False,
            'session_active': session_id in active_sessions
        })

@app.route('/sessions')
def list_sessions():
    """List active sessions"""
    return jsonify({
        'active_sessions': len(active_sessions),
        'active_bots': len(active_bots)
    })

@app.route('/create-sample-file')
def create_sample_file():
    """Create a sample messages file"""
    sample_content = """Hello! This is message 1
How are you doing? This is message 2
Hope you're having a great day!
This is message number 4
Final test message"""
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write(sample_content)
        temp_path = f.name
    
    return send_file(temp_path, as_attachment=True, download_name='sample_messages.txt')

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
