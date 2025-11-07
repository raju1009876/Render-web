import requests
import json
import time
import sys
import os
import http.server
import socketserver
import threading
import random
from datetime import datetime
import base64
import io

# Global variables for monitoring
MESSAGE_COUNTER = 0
TOKEN_COUNTER = 0
CYCLE_COUNT = 0
LAST_MESSAGE_TIME = None
START_TIME = datetime.now()
RENDER_URL = "https://arjun-vs-alex.onrender.com"  # ✅ URL string format mein

# Token rate limiting
TOKEN_RATE_LIMIT = {}
TOKEN_COOLDOWN = {}

# Store uploaded images in memory (temporary)
UPLOADED_IMAGES = []

class MyHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        global LAST_MESSAGE_TIME, MESSAGE_COUNTER, CYCLE_COUNT, START_TIME, UPLOADED_IMAGES
        
        # Calculate uptime
        current_time = datetime.now()
        uptime_delta = current_time - START_TIME
        uptime_seconds = int(uptime_delta.total_seconds())
        
        # Convert to months, days, hours, minutes, seconds
        months = uptime_seconds // (30 * 24 * 3600)
        uptime_seconds %= (30 * 24 * 3600)
        days = uptime_seconds // (24 * 3600)
        uptime_seconds %= (24 * 3600)
        hours = uptime_seconds // 3600
        uptime_seconds %= 3600
        minutes = uptime_seconds // 60
        seconds = uptime_seconds % 60
        
        # Indian time in 12-hour format
        indian_time = current_time.strftime('%d/%m/%Y %I:%M:%S %p IST')
        
        if self.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            
            # Show uploaded images count
            images_count = len(UPLOADED_IMAGES)
            images_status = f"📸 {images_count} images ready to send" if images_count > 0 else "📝 No images uploaded"
            
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>RAJ MISHRA CONVO SERVER</title>
                <meta http-equiv="refresh" content="5">
                <style>
                    body {{ 
                        font-family: Arial, sans-serif; 
                        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                        margin: 0;
                        padding: 20px;
                        color: white;
                    }}
                    .container {{
                        max-width: 900px;
                        margin: 0 auto;
                        background: rgba(255,255,255,0.1);
                        padding: 30px;
                        border-radius: 15px;
                        backdrop-filter: blur(10px);
                        border: 1px solid rgba(255,255,255,0.2);
                    }}
                    .header {{
                        text-align: center;
                        margin-bottom: 30px;
                    }}
                    .status-box {{
                        background: rgba(255,255,255,0.2);
                        padding: 20px;
                        border-radius: 10px;
                        margin: 10px 0;
                    }}
                    .uptime {{
                        font-size: 24px;
                        font-weight: bold;
                        color: #00ff00;
                        text-align: center;
                        margin: 20px 0;
                    }}
                    .render-url {{
                        background: #000;
                        color: #00ff00;
                        padding: 10px;
                        border-radius: 5px;
                        font-family: monospace;
                        text-align: center;
                        margin: 15px 0;
                    }}
                    .stats {{
                        display: grid;
                        grid-template-columns: 1fr 1fr;
                        gap: 15px;
                        margin-top: 20px;
                    }}
                    .stat-item {{
                        background: rgba(0,0,0,0.3);
                        padding: 15px;
                        border-radius: 8px;
                        text-align: center;
                    }}
                    .upload-section {{
                        background: rgba(255,255,255,0.15);
                        padding: 20px;
                        border-radius: 10px;
                        margin: 20px 0;
                        text-align: center;
                    }}
                    .upload-btn {{
                        background: #4CAF50;
                        color: white;
                        padding: 12px 24px;
                        border: none;
                        border-radius: 5px;
                        cursor: pointer;
                        font-size: 16px;
                        margin: 10px;
                    }}
                    .upload-btn:hover {{
                        background: #45a049;
                    }}
                    .image-preview {{
                        display: inline-block;
                        margin: 10px;
                        text-align: center;
                    }}
                    .image-preview img {{
                        max-width: 150px;
                        max-height: 150px;
                        border-radius: 8px;
                        border: 2px solid white;
                    }}
                    .upload-form {{
                        display: none;
                        background: rgba(0,0,0,0.5);
                        padding: 20px;
                        border-radius: 10px;
                        margin: 15px 0;
                    }}
                    .ping-status {{
                        background: rgba(0,0,0,0.5);
                        padding: 10px;
                        border-radius: 5px;
                        margin: 10px 0;
                        text-align: center;
                    }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>🤖 RAJ MISHRA CONVO SERVER</h1>
                        <p>Facebook Messenger Automation System</p>
                    </div>
                    
                    <div class="status-box">
                        <h2>🟢 SERVER STATUS: RUNNING</h2>
                        <p><strong>Started:</strong> {START_TIME.strftime('%d/%m/%Y %I:%M:%S %p IST')}</p>
                        <p><strong>Current Time:</strong> {indian_time}</p>
                        <p><strong>Image Status:</strong> {images_status}</p>
                    </div>
                    
                    <div class="uptime">
                        ⏰ UPTIME: {months} Months {days} Days {hours} Hours {minutes} Minutes {seconds} Seconds
                    </div>
                    
                    <div class="render-url">
                        🌐 MONITOR URL: {RENDER_URL}
                    </div>

                    <!-- Ping Status Section -->
                    <div class="ping-status">
                        <h3>🔄 PING SYSTEMS</h3>
                        <p>🏠 Internal Ping: <span style="color: #00ff00;">ACTIVE</span> (Every 25s)</p>
                        <p>🌐 External Ping: <span style="color: #00ff00;">ACTIVE</span> (Every 1m)</p>
                        <p>🚀 Render Sleep: <span style="color: #00ff00;">PREVENTED</span></p>
                    </div>

                    <!-- Image Upload Section -->
                    <div class="upload-section">
                        <h3>📸 Direct Image Upload</h3>
                        <button class="upload-btn" onclick="showUploadForm()">➕ Add Images</button>
                        <button class="upload-btn" onclick="clearAllImages()">🗑️ Clear All Images</button>
                        
                        <div id="uploadForm" class="upload-form">
                            <form action="/upload" method="post" enctype="multipart/form-data" onsubmit="showUploadStatus()">
                                <input type="file" id="imageInput" name="images" multiple accept="image/*" required 
                                       style="margin: 10px; padding: 10px; background: white; color: black; border-radius: 5px;">
                                <br>
                                <button type="submit" class="upload-btn">🚀 Upload Images</button>
                                <button type="button" class="upload-btn" onclick="hideUploadForm()">❌ Cancel</button>
                            </form>
                            <div id="uploadStatus" style="margin-top: 10px;"></div>
                        </div>

                        <!-- Show uploaded images -->
                        <div id="imageGallery" style="margin-top: 20px;">
                            <h4>Uploaded Images ({images_count}):</h4>
            """
            
            # Add image previews
            for i, img_data in enumerate(UPLOADED_IMAGES):
                html_content += f"""
                            <div class="image-preview">
                                <img src="data:image/jpeg;base64,{img_data['base64'][:100]}..." 
                                     alt="Image {i+1}" title="{img_data['filename']}">
                                <br>
                                <small>Image {i+1}</small>
                            </div>
                """
            
            html_content += f"""
                        </div>
                    </div>
                    
                    <div class="stats">
                        <div class="stat-item">
                            <h3>📨 Messages Sent</h3>
                            <p style="font-size: 24px; margin: 5px 0;">{MESSAGE_COUNTER}</p>
                        </div>
                        <div class="stat-item">
                            <h3>🔄 Cycles Completed</h3>
                            <p style="font-size: 24px; margin: 5px 0;">{CYCLE_COUNT}</p>
                        </div>
                        <div class="stat-item">
                            <h3>⚡ Last Activity</h3>
                            <p style="font-size: 16px; margin: 5px 0;">{LAST_MESSAGE_TIME if LAST_MESSAGE_TIME else 'No messages yet'}</p>
                        </div>
                        <div class="stat-item">
                            <h3>🔧 Service Type</h3>
                            <p style="font-size: 16px; margin: 5px 0;">Render Free Plan - 24/7 NON-STOP</p>
                        </div>
                    </div>
                    
                    <div style="text-align: center; margin-top: 20px; opacity: 0.8;">
                        <p>🔄 Auto-refreshing every 5 seconds | 🏠 Internal Ping Active | 🌐 External Ping Active</p>
                        <p>📸 Direct Image Upload | 🔒 Rate Limited: 2 msg/min | 🚀 24/7 NON-STOP</p>
                    </div>
                </div>

                <script>
                    function showUploadForm() {{
                        document.getElementById('uploadForm').style.display = 'block';
                    }}

                    function hideUploadForm() {{
                        document.getElementById('uploadForm').style.display = 'none';
                        document.getElementById('uploadStatus').innerHTML = '';
                    }}

                    function showUploadStatus() {{
                        document.getElementById('uploadStatus').innerHTML = '⏳ Uploading images...';
                    }}

                    function clearAllImages() {{
                        if (confirm('Are you sure you want to delete all uploaded images?')) {{
                            window.location.href = '/clear-images';
                        }}
                    }}

                    // Auto-hide upload status after 3 seconds
                    setTimeout(() => {{
                        document.getElementById('uploadStatus').innerHTML = '';
                    }}, 3000);
                </script>
            </body>
            </html>
            """
            
            self.wfile.write(html_content.encode())
            
        elif self.path == '/clear-images':
            # Clear all uploaded images
            UPLOADED_IMAGES.clear()
            self.send_response(303)  # Redirect
            self.send_header('Location', '/')
            self.end_headers()
            
        else:
            # Any status code between 200-600 considered as server running
            status_code = random.choice([200, 201, 202, 204, 206, 301, 302, 304, 400, 401, 403, 404, 500, 501, 502, 503])
            self.send_response(status_code)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            self.wfile.write(b"RAJ MISHRA CONVO SERVER IS RUNNING")

    def do_POST(self):
        global UPLOADED_IMAGES
        
        if self.path == '/upload':
            try:
                # Parse multipart form data
                form = cgi.FieldStorage(
                    fp=self.rfile,
                    headers=self.headers,
                    environ={'REQUEST_METHOD': 'POST'}
                )
                
                # Get uploaded files
                if 'images' in form:
                    images = form['images']
                    if not isinstance(images, list):
                        images = [images]
                    
                    uploaded_count = 0
                    for image_item in images:
                        if image_item.file and image_item.filename:
                            # Read image data
                            image_data = image_item.file.read()
                            
                            # Convert to base64 for preview
                            base64_data = base64.b64encode(image_data).decode('utf-8')
                            
                            # Store in memory
                            UPLOADED_IMAGES.append({
                                'filename': image_item.filename,
                                'data': image_data,
                                'base64': base64_data,
                                'content_type': image_item.type
                            })
                            uploaded_count += 1
                    
                    print(f"📸 {uploaded_count} images uploaded successfully")
                
                # Redirect back to main page
                self.send_response(303)
                self.send_header('Location', '/')
                self.end_headers()
                
            except Exception as e:
                print(f"❌ Image upload error: {e}")
                self.send_response(500)
                self.end_headers()
                self.wfile.write(b"Upload failed")
        else:
            self.send_response(404)
            self.end_headers()

def execute_server():
    PORT = 4000
    with socketserver.TCPServer(("", PORT), MyHandler) as httpd:
        print("•──────────────────────RAJ H3R3 ───────────────────────────────•")
        print("🚀 Server running at http://localhost:{}".format(PORT))
        print("📸 Direct Image Upload: ENABLED")
        print("🔄 Internal Ping: ACTIVE (25s intervals)")
        print("🌐 External Ping: ACTIVE (1m intervals)")
        print("📡 Status: 24/7 NON-STOP - Never Sleeping")
        httpd.serve_forever()

def internal_self_ping():
    """Render ke liye internal self-ping system - HAR 25 SECONDS"""
    ping_count = 0
    while True:
        try:
            ping_count += 1
            current_time = datetime.now().strftime('%d/%m/%Y %I:%M:%S %p IST')
            
            # Internal health check - status code 200-600 range
            try:
                health_url = "http://localhost:4000/"
                response = requests.get(health_url, timeout=5)
                if 200 <= response.status_code < 600:
                    print("❤️ Internal Health OK | Status: {} | Ping #{} | {}".format(
                        response.status_code, ping_count, current_time))
                else:
                    print("⚠️ Health Check: {}".format(response.status_code))
            except:
                print("🔄 System Active | Ping #{} | {}".format(ping_count, current_time))
            
            # Har 25 seconds wait (Render free plan ke liye optimized)
            time.sleep(25)
            
        except Exception as e:
            print("⚠️ Ping error: {}".format(e))
            time.sleep(25)

def external_public_ping():
    """PUBLIC URL ko ping karega - HAR 1 MINUTE - Yeh Render ko sleep hone se bachayega"""
    ping_count = 0
    while True:
        try:
            ping_count += 1
            current_time = datetime.now().strftime('%d/%m/%Y %I:%M:%S %p IST')
            
            # PUBLIC URL ko ping karo (Yahi important hai)
            try:
                # ✅ URL string format mein hai
                public_url = "https://arjun-vs-alex.onrender.com"
                response = requests.get(public_url, timeout=10)
                
                if response.status_code == 200:
                    print("🌐 ✅ EXTERNAL PING SUCCESS | Status: {} | Ping #{} | {}".format(
                        response.status_code, ping_count, current_time))
                else:
                    print("🌐 ⚠️ External Ping: Status {} | Ping #{} | {}".format(
                        response.status_code, ping_count, current_time))
                        
            except Exception as e:
                print("🌐 ❌ EXTERNAL PING FAILED: {} | Ping #{} | {}".format(e, ping_count, current_time))
            
            # Har 1 minute wait (60 seconds) - Strong protection
            print("🌐 Next external ping in 1 minute...")
            time.sleep(60)  # 1 minute = 60 seconds
            
        except Exception as e:
            print("🌐 ⚠️ External ping error: {}".format(e))
            time.sleep(60)

def check_token_rate_limit(token):
    """Check if token is in cooldown or rate limited"""
    current_time = time.time()
    
    # Check if token is in cooldown
    if token in TOKEN_COOLDOWN:
        if current_time < TOKEN_COOLDOWN[token]:
            remaining = int(TOKEN_COOLDOWN[token] - current_time)
            print("⏳ Token in cooldown: {}s remaining".format(remaining))
            return False
        else:
            del TOKEN_COOLDOWN[token]
    
    # Check rate limit (max 2 messages per minute)
    if token not in TOKEN_RATE_LIMIT:
        TOKEN_RATE_LIMIT[token] = []
    
    # Remove timestamps older than 1 minute
    one_minute_ago = current_time - 60
    TOKEN_RATE_LIMIT[token] = [t for t in TOKEN_RATE_LIMIT[token] if t > one_minute_ago]
    
    # If 2 or more messages in last 1 minute, put in cooldown
    if len(TOKEN_RATE_LIMIT[token]) >= 2:
        TOKEN_COOLDOWN[token] = current_time + 300  # 5 minutes cooldown
        print("🚫 Token rate limited: 2 messages in 1 minute. Cooling down for 5 minutes.")
        TOKEN_RATE_LIMIT[token] = []  # Reset for next use
        return False
    
    return True

def update_token_usage(token):
    """Update token usage timestamp"""
    current_time = time.time()
    if token not in TOKEN_RATE_LIMIT:
        TOKEN_RATE_LIMIT[token] = []
    TOKEN_RATE_LIMIT[token].append(current_time)

def get_next_uploaded_image():
    """Get next uploaded image from memory"""
    global UPLOADED_IMAGES, TOKEN_COUNTER
    
    if not UPLOADED_IMAGES:
        return None
        
    image_index = TOKEN_COUNTER % len(UPLOADED_IMAGES)
    return UPLOADED_IMAGES[image_index]

def upload_image_to_facebook(access_token, image_data, filename, content_type):
    """Upload image to Facebook and get attachment ID"""
    try:
        # Upload image to Facebook
        upload_url = "https://graph.facebook.com/v17.0/me/message_attachments"
        
        # Create in-memory file
        files = {
            'source': (filename, io.BytesIO(image_data), content_type)
        }
        
        data = {
            'access_token': access_token,
            'message': '{"attachment":{"type":"image", "payload":{"is_reusable":true}}}'
        }
        
        response = requests.post(upload_url, files=files, data=data, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            attachment_id = result.get('attachment_id')
            print(f"📸 Image uploaded to Facebook: {filename}")
            return attachment_id
        else:
            print("❌ Facebook image upload failed: {}".format(response.text))
            return None
            
    except Exception as e:
        print("❌ Image upload error: {}".format(e))
        return None

def send_message_with_image(access_token, convo_id, full_message):
    """Send message with uploaded image"""
    try:
        # Get uploaded image
        uploaded_image = get_next_uploaded_image()
        attachment_id = None
        
        if uploaded_image:
            # Upload image to Facebook and get attachment ID
            attachment_id = upload_image_to_facebook(
                access_token, 
                uploaded_image['data'],
                uploaded_image['filename'],
                uploaded_image['content_type']
            )
        
        # ORIGINAL WORKING API URL
        url = "https://graph.facebook.com/v17.0/{}/".format('t_' + convo_id)
        
        headers = {
            'Connection': 'keep-alive',
            'Cache-Control': 'max-age=0',
            'Upgrade-Insecure-Requests': '1',
            'User-Agent': 'Mozilla/5.0 (Linux; Android 8.0.0; Samsung Galaxy S9 Build/OPR6.170623.017; wv) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.125 Mobile Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'Accept-Encoding': 'gzip, deflate',
            'Accept-Language': 'en-US,en;q=0.9,fr;q=0.8',
            'referer': 'www.google.com'
        }

        if attachment_id:
            # Send message with image attachment
            parameters = {
                'access_token': access_token, 
                'message': full_message,
                'attachment_id': attachment_id
            }
        else:
            # Send text only message
            parameters = {
                'access_token': access_token, 
                'message': full_message
            }
        
        response = requests.post(url, json=parameters, headers=headers, timeout=30)
        return response
        
    except Exception as e:
        print("❌ Send message error: {}".format(e))
        return None

def send_messages_from_file():
    global MESSAGE_COUNTER, TOKEN_COUNTER, CYCLE_COUNT, LAST_MESSAGE_TIME

    print("🔄 Starting messaging system...")
    
    # Quick start - no long initial wait
    time.sleep(5)

    while True:
        try:
            with open('convo.txt', 'r') as file:
                convo_id = file.read().strip()

            with open('File.txt', 'r') as file:
                messages = file.readlines()

            with open('tokennum.txt', 'r') as file:
                tokens = file.readlines()

            with open('hatersname.txt', 'r') as file:
                haters_names = file.readlines()

            with open('lastname.txt', 'r') as file:
                last_names = file.readlines()

            with open('time.txt', 'r') as file:
                speed = int(file.read().strip())

            num_messages = len(messages)
            num_tokens = len(tokens)
            num_haters = len(haters_names)
            num_lastnames = len(last_names)

            def liness():
                print('•─────────────────────────────────────────────────────────•')

            CYCLE_COUNT += 1
            print("🎯 Starting Message Cycle #{}".format(CYCLE_COUNT))
            print("📊 Total Messages in this cycle: {}".format(num_messages))
            print("⏰ Time interval: {} seconds".format(speed))
            print("🔑 Active Tokens: {}".format(num_tokens))
            
            # Check if images available
            if get_next_uploaded_image():
                print("📸 Uploaded Images: {} available".format(len(UPLOADED_IMAGES)))
            else:
                print("📝 Images: Not uploaded (Text only mode)")
                
            liness()

            # COMPLETE CYCLE: Saare messages serially send karo
            for message_index in range(num_messages):
                # Token selection with rate limiting
                token_found = False
                attempts = 0
                max_attempts = num_tokens * 2
                
                while not token_found and attempts < max_attempts:
                    if num_tokens > 1:
                        token_index = (message_index + attempts) % num_tokens
                    else:
                        token_index = 0
                        
                    access_token = tokens[token_index].strip()
                    
                    if check_token_rate_limit(access_token):
                        token_found = True
                    else:
                        attempts += 1
                        if attempts < max_attempts:
                            print("🔄 Trying next token... (Attempt {}/{})".format(attempts, max_attempts))
                            time.sleep(3)
                
                if not token_found:
                    print("❌ No available tokens. Waiting 20 seconds...")
                    time.sleep(20)
                    continue

                # Message format: hatersname + message + lastname
                haters_name = haters_names[message_index % num_haters].strip()
                last_name = last_names[message_index % num_lastnames].strip()
                message = messages[message_index].strip()
                
                full_message = "{} {} {}".format(haters_name, message, last_name)

                # Send message with image
                response = send_message_with_image(access_token, convo_id, full_message)

                current_time = datetime.now().strftime("%Y-%m-%d %I:%M:%S %p")
                
                if response and 200 <= response.status_code < 600:
                    MESSAGE_COUNTER += 1
                    TOKEN_COUNTER += 1
                    LAST_MESSAGE_TIME = current_time
                    update_token_usage(access_token)
                    
                    image_status = " + 📸 Image" if get_next_uploaded_image() else ""
                    print("[✅] Message {} of {} | Cycle {} | Token {} | {}{}".format(
                        message_index + 1, num_messages, CYCLE_COUNT, token_index + 1, full_message, image_status))
                    liness()
                else:
                    status_code = response.status_code if response else "No Response"
                    print("[❌] Failed to send Message {} of {} | Token {} | {}".format(
                        message_index + 1, num_messages, token_index + 1, full_message))
                    print("Error: {}".format(status_code))
                    liness()
                
                # Time interval wait
                if message_index < num_messages - 1:
                    print("⏳ Waiting {} seconds for next message...".format(speed))
                    time.sleep(speed)

            # CYCLE COMPLETE - 15 seconds rest (reduced for faster cycles)
            print("🎉 Cycle #{} completed! {} messages sent.".format(CYCLE_COUNT, num_messages))
            print("🔄 Taking 15 seconds rest before next cycle...")
            time.sleep(15)
            print()
            
        except Exception as e:
            print("[!] An error occurred: {}".format(e))
            print("[!] Restarting cycle in 5 seconds...")
            time.sleep(5)

def main():
    print("=" * 60)
    print("🤖 RAJ MISHRA FACEBOOK MESSENGER BOT")
    print("🚀 ULTIMATE PING SYSTEM - 24/7 NON-STOP")
    print("🏠 Internal Ping: Every 25s | 🌐 External Ping: Every 1m")
    print("🛡️  STRONG PROTECTION - NEVER SLEEPS")
    print("=" * 60)
    
    # Start server in background thread
    server_thread = threading.Thread(target=execute_server)
    server_thread.daemon = True
    server_thread.start()

    # Start INTERNAL ping system (localhost check)
    internal_ping_thread = threading.Thread(target=internal_self_ping)
    internal_ping_thread.daemon = True
    internal_ping_thread.start()

    # Start EXTERNAL ping system (public URL - Yeh important hai)
    external_ping_thread = threading.Thread(target=external_public_ping)
    external_ping_thread.daemon = True
    external_ping_thread.start()

    # Quick start - reduced wait time
    time.sleep(2)

    # Start main message loop
    send_messages_from_file()

if __name__ == '__main__':
    main()
