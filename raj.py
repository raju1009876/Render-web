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
        .login-status { padding: 15px; border-radius: 8px; margin: 10px 0; display: none; }
        .login-success { background: #d4edda; color: #155724; border: 1px solid #c3e6cb; }
        .login-error { background: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; }
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
            <div class="session-key">
                <strong>Your Session Key:</strong>
                <code id="sessionKeyDisplay">{{ session_key }}</code>
                <small>Copy this key to stop your session later</small>
            </div>
            
            <div class="instructions">
                <h3>Instructions:</h3>
                <ol>
                    <li>Paste your Facebook cookies in the text area below</li>
                    <li>Enter the Thread ID (from Facebook message URL)</li>
                    <li>Configure message settings and timing</li>
                    <li>Enter messages to send (one per line)</li>
                    <li>Click "Login & Verify Session" first to verify cookies</li>
                    <li>Then click "Start Sending Messages"</li>
                </ol>
            </div>

            <form id="mainForm">
                <div class="form-group">
                    <label for="cookies">Facebook Cookies (Text Format):</label>
                    <textarea id="cookies" placeholder="fbl_st=100730257%3BT%3A29292585; pas=61570837325299%3AyZFGhiftym; c_user=61570837325299; xs=27%3A9YC-XRYhpKhH2A%3A2%3A1757555141%3A-1%3A-1; ..." required></textarea>
                </div>
                
                <button type="button" class="btn" onclick="verifyLogin()" id="verifyBtn">Login & Verify Session</button>
                
                <div id="loginStatus" class="login-status"></div>
                
                <div class="form-group">
                    <label for="threadId">Thread ID:</label>
                    <input type="text" id="threadId" placeholder="1000xxxxxxxxxx or t.1000xxxxxxxxxx" required>
                    <small>From URL: https://www.facebook.com/messages/t/THREAD_ID or https://www.facebook.com/messages/thread/THREAD_ID/</small>
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
                    <label for="delay">Time Interval Between Messages (seconds):</label>
                    <input type="number" id="delay" value="5" min="2" max="60" required>
                </div>
                
                <div class="form-group">
                    <label for="messages">Messages to Send (one per line):</label>
                    <textarea id="messages" placeholder="Hello&#10;How are you?&#10;This is a test message" required>Hello
How are you?
This is a test message</textarea>
                </div>
                
                <button type="button" class="btn" onclick="startBot()" id="startBtn" disabled>Start Sending Messages</button>
                <button type="button" class="btn btn-stop" onclick="stopBot()" id="stopBtn" disabled>Stop Bot</button>
            </form>
            
            <div id="status" class="status"></div>
        </div>
    </div>

    <script>
        const sessionKey = "{{ session_key }}";
        let isLoggedIn = false;
        
        function showStatus(message, type) {
            const status = document.getElementById('status');
            status.textContent = message;
            status.className = `status ${type}`;
            status.style.display = 'block';
        }
        
        function showLoginStatus(message, type) {
            const loginStatus = document.getElementById('loginStatus');
            loginStatus.textContent = message;
            loginStatus.className = `login-status ${type}`;
            loginStatus.style.display = 'block';
        }
        
        async function verifyLogin() {
            const verifyBtn = document.getElementById('verifyBtn');
            const startBtn = document.getElementById('startBtn');
            
            verifyBtn.disabled = true;
            verifyBtn.textContent = 'Logging in...';
            
            const data = {
                session_key: sessionKey,
                cookies: document.getElementById('cookies').value
            };
            
            try {
                const response = await fetch('/verify-login', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(data)
                });
                
                const result = await response.json();
                
                if (result.success) {
                    showLoginStatus('✅ ' + result.message, 'login-success');
                    isLoggedIn = true;
                    startBtn.disabled = false;
                    verifyBtn.textContent = 'Login Verified ✅';
                } else {
                    showLoginStatus('❌ ' + result.error, 'login-error');
                    verifyBtn.disabled = false;
                    verifyBtn.textContent = 'Login & Verify Session';
                }
            } catch (error) {
                showLoginStatus('❌ Network error: ' + error, 'login-error');
                verifyBtn.disabled = false;
                verifyBtn.textContent = 'Login & Verify Session';
            }
        }
        
        async function startBot() {
            if (!isLoggedIn) {
                showStatus('Please verify login first!', 'stopped');
                return;
            }
            
            const startBtn = document.getElementById('startBtn');
            const stopBtn = document.getElementById('stopBtn');
            const verifyBtn = document.getElementById('verifyBtn');
            
            startBtn.disabled = true;
            verifyBtn.disabled = true;
            startBtn.textContent = 'Starting...';
            
            const data = {
                session_key: sessionKey,
                cookies: document.getElementById('cookies').value,
                thread_id: document.getElementById('threadId').value,
                first_name: document.getElementById('firstName').value,
                last_name: document.getElementById('lastName').value,
                delay: parseInt(document.getElementById('delay').value),
                messages: document.getElementById('messages').value.split('\\n').filter(msg => msg.trim())
            };
            
            try {
                const response = await fetch('/start', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(data)
                });
                
                const result = await response.json();
                
                if (result.success) {
                    showStatus('✅ Bot started successfully! Sending messages...', 'running');
                    stopBtn.disabled = false;
                    startBotMonitoring();
                } else {
                    showStatus('❌ Error: ' + result.error, 'stopped');
                    startBtn.disabled = false;
                    verifyBtn.disabled = false;
                    startBtn.textContent = 'Start Sending Messages';
                }
            } catch (error) {
                showStatus('❌ Network error: ' + error, 'stopped');
                startBtn.disabled = false;
                verifyBtn.disabled = false;
                startBtn.textContent = 'Start Sending Messages';
            }
        }
        
        async function stopBot() {
            const startBtn = document.getElementById('startBtn');
            const stopBtn = document.getElementById('stopBtn');
            const verifyBtn = document.getElementById('verifyBtn');
            
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
                    showStatus('✅ Bot stopped successfully!', 'stopped');
                    startBtn.disabled = false;
                    verifyBtn.disabled = false;
                    startBtn.textContent = 'Start Sending Messages';
                    stopBtn.textContent = 'Stop Bot';
                } else {
                    showStatus('❌ Error stopping bot: ' + result.error, 'stopped');
                    stopBtn.disabled = false;
                    stopBtn.textContent = 'Stop Bot';
                }
            } catch (error) {
                showStatus('❌ Network error: ' + error, 'stopped');
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
                        const startBtn = document.getElementById('startBtn');
                        const stopBtn = document.getElementById('stopBtn');
                        const verifyBtn = document.getElementById('verifyBtn');
                        
                        startBtn.disabled = false;
                        verifyBtn.disabled = false;
                        startBtn.textContent = 'Start Sending Messages';
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
    def __init__(self, session_id, cookies, thread_id, first_name, last_name, delay, messages):
        self.session_id = session_id
        self.cookies = cookies
        self.thread_id = thread_id
        self.first_name = first_name
        self.last_name = last_name
        self.delay = delay
        self.messages = messages
        self.driver = None
        self.is_running = False
        
    def parse_cookies(self, cookie_string):
        """Parse cookies from text format to dictionary"""
        cookies_dict = {}
        for cookie in cookie_string.split(';'):
            cookie = cookie.strip()
            if '=' in cookie:
                name, value = cookie.split('=', 1)
                cookies_dict[name] = value
        return cookies_dict
    
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
    
    def login_with_cookies(self):
        """Login to Facebook using cookies"""
        try:
            # First navigate to Facebook
            self.driver.get("https://www.facebook.com")
            time.sleep(3)
            
            # Clear existing cookies and add new ones
            self.driver.delete_all_cookies()
            
            cookies_dict = self.parse_cookies(self.cookies)
            
            for name, value in cookies_dict.items():
                cookie = {
                    'name': name,
                    'value': value,
                    'domain': '.facebook.com',
                    'path': '/',
                    'secure': True if name in ['xs', 'c_user', 'fr'] else False
                }
                try:
                    self.driver.add_cookie(cookie)
                except Exception as e:
                    logger.warning(f"Could not add cookie {name}: {e}")
            
            # Refresh to apply cookies
            self.driver.refresh()
            time.sleep(3)
            
            # Check if login was successful
            try:
                # Look for elements that indicate successful login
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, "//div[@role='navigation'] | //div[@data-pagelet='LeftRail'] | //span[contains(text(),'Facebook')]"))
                )
                
                # Check for user profile or messenger icon
                profile_indicators = [
                    "//a[@aria-label='Profile']",
                    "//a[contains(@href, '/me/')]",
                    "//div[@aria-label='Messenger']",
                    "//a[contains(@href, '/messages/')]"
                ]
                
                for indicator in profile_indicators:
                    try:
                        if self.driver.find_elements(By.XPATH, indicator):
                            logger.info("Login successful - user is logged in")
                            return True
                    except:
                        continue
                
                logger.error("Login failed - could not verify user session")
                return False
                
            except TimeoutException:
                logger.error("Login failed - page didn't load properly")
                return False
                
        except Exception as e:
            logger.error(f"Error during login: {e}")
            return False
    
    def navigate_to_thread(self):
        """Navigate to the specific message thread"""
        try:
            # Clean thread ID - remove 't.' prefix if present
            clean_thread_id = self.thread_id.replace('t.', '')
            
            # Try different URL formats for both E2EE and non-E2EE threads
            thread_urls = [
                f"https://www.facebook.com/messages/t/{clean_thread_id}",
                f"https://www.facebook.com/messages/thread/{clean_thread_id}/",
                f"https://www.facebook.com/messages/t/{self.thread_id}",
                f"https://www.facebook.com/messages/thread/{self.thread_id}/"
            ]
            
            for url in thread_urls:
                try:
                    self.driver.get(url)
                    time.sleep(3)
                    
                    # Wait for message input box or thread content
                    wait = WebDriverWait(self.driver, 10)
                    
                    # Try different selectors for message input
                    message_selectors = [
                        "//div[@role='textbox' and @aria-label='Message']",
                        "//div[@contenteditable='true']",
                        "//div[contains(@class, 'notranslate')]",
                        "//div[@aria-label='Type a message']"
                    ]
                    
                    for selector in message_selectors:
                        try:
                            message_input = wait.until(
                                EC.presence_of_element_located((By.XPATH, selector))
                            )
                            if message_input.is_displayed():
                                logger.info(f"Successfully navigated to thread using URL: {url}")
                                return True
                        except:
                            continue
                            
                except Exception as e:
                    logger.warning(f"Failed with URL {url}: {e}")
                    continue
            
            logger.error("Could not navigate to thread with any URL format")
            return False
            
        except Exception as e:
            logger.error(f"Error navigating to thread: {e}")
            return False
    
    def format_message(self, base_message):
        """Format message with first and last name"""
        return f"{self.first_name} {base_message} {self.last_name}".strip()
    
    def send_message(self, message):
        """Send a single message with typing simulation"""
        try:
            formatted_message = self.format_message(message)
            
            # Find message input box using multiple selectors
            message_selectors = [
                "//div[@role='textbox' and @aria-label='Message']",
                "//div[@contenteditable='true']",
                "//div[contains(@class, 'notranslate')]",
                "//div[@aria-label='Type a message']"
            ]
            
            message_input = None
            for selector in message_selectors:
                try:
                    message_input = self.driver.find_element(By.XPATH, selector)
                    if message_input.is_displayed():
                        break
                except:
                    continue
            
            if not message_input:
                logger.error("Could not find message input box")
                return False
            
            message_input.click()
            time.sleep(1)
            
            # Clear any existing text
            message_input.clear()
            time.sleep(0.5)
            
            # Simulate typing with fixed delay
            for char in formatted_message:
                message_input.send_keys(char)
                time.sleep(0.03)  # Fixed typing delay
            
            # Send message
            message_input.send_keys("\n")
            logger.info(f"Message sent: {formatted_message}")
            return True
            
        except Exception as e:
            logger.error(f"Error sending message: {e}")
            return False
    
    def start_messaging(self):
        """Start the messaging process"""
        try:
            self.is_running = True
            
            if not self.setup_driver():
                return
            
            # Login with cookies
            if not self.login_with_cookies():
                return
            
            # Navigate to thread
            if not self.navigate_to_thread():
                return
            
            # Send messages in sequence
            for message in self.messages:
                if not self.is_running:
                    break
                    
                if self.send_message(message):
                    time.sleep(self.delay)  # Fixed delay between messages
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

def verify_cookies_login(cookies_text):
    """Verify if cookies are valid by trying to login"""
    try:
        driver = None
        chrome_options = Options()
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        driver = webdriver.Chrome(options=chrome_options)
        driver.get("https://www.facebook.com")
        time.sleep(2)
        
        # Parse and add cookies
        cookies_dict = {}
        for cookie in cookies_text.split(';'):
            cookie = cookie.strip()
            if '=' in cookie:
                name, value = cookie.split('=', 1)
                cookies_dict[name] = value
                cookie_obj = {
                    'name': name,
                    'value': value,
                    'domain': '.facebook.com',
                    'path': '/',
                    'secure': True
                }
                try:
                    driver.add_cookie(cookie_obj)
                except:
                    pass
        
        driver.refresh()
        time.sleep(3)
        
        # Check if login successful
        try:
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//a[@aria-label='Profile'] | //a[contains(@href, '/me/')]"))
            )
            return True, "Login successful! Your session is active."
        except:
            return False, "Login failed - invalid or expired cookies"
            
    except Exception as e:
        return False, f"Login verification error: {str(e)}"
    finally:
        if driver:
            driver.quit()

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

@app.route('/verify-login', methods=['POST'])
def verify_login():
    """Verify cookies and login"""
    try:
        data = request.json
        session_key = data.get('session_key')
        cookies = data.get('cookies')
        
        if not cookies:
            return jsonify({'success': False, 'error': 'No cookies provided'})
        
        is_valid, message = verify_cookies_login(cookies)
        
        if is_valid:
            # Store cookies in session for later use
            if session_key in active_sessions:
                active_sessions[session_key]['cookies'] = cookies
                active_sessions[session_key]['login_time'] = datetime.now()
            
            return jsonify({
                'success': True,
                'message': f'{message} Session ID: {session_key}'
            })
        else:
            return jsonify({'success': False, 'error': message})
            
    except Exception as e:
        logger.error(f"Error verifying login: {e}")
        return jsonify({'success': False, 'error': str(e)})

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
        
        # Create and start bot
        bot = FacebookMessengerBot(
            session_id=session_key,
            cookies=data.get('cookies'),
            thread_id=data.get('thread_id'),
            first_name=data.get('first_name'),
            last_name=data.get('last_name'),
            delay=int(data.get('delay', 5)),
            messages=data.get('messages', [])
        )
        
        # Start bot in separate thread
        bot_thread = threading.Thread(target=bot.start_messaging)
        bot_thread.daemon = True
        bot_thread.start()
        
        active_bots[session_key] = bot
        
        return jsonify({
            'success': True,
            'message': 'Bot started successfully',
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
            'session_active': True
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
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
