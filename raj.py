from flask import Flask, render_template_string

app = Flask(__name__)

HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Elegant AI Card UI</title>
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <style>
    body {
      background: #101139;
      min-height: 100vh;
      display: flex;
      align-items: center;
      justify-content: center;
      margin: 0;
    }
    .card {
      width: 340px;
      border-radius: 28px;
      background: linear-gradient(135deg, #22264b 65%, #1c3947 100%);
      box-shadow: 0 6px 32px rgba(0,0,0,0.18);
      padding: 48px 28px 36px 28px;
      text-align: center;
      position: relative;
      overflow: hidden;
    }
    .card::before {
      content: "";
      position: absolute;
      top: 0; left: 0;
      width: 120px;
      height: 100%;
      background: radial-gradient(circle at 0% 0%, #2ee6ff48 20%, transparent 80%);
      z-index: 0;
    }
    .icon-glow {
      width: 110px;
      height: 110px;
      margin: 0 auto 30px auto;
      border-radius: 50%;
      background: radial-gradient(circle, #3d72fc 20%, #8350fc 100%);
      box-shadow: 0 0 38px 8px #6464fd77;
      display: flex;
      align-items: center;
      justify-content: center;
      position: relative;
      z-index: 1;
    }
    .icon-glow svg {
      width: 50px;
      height: 50px;
      fill: #fff;
      filter: drop-shadow(0 0 10px #ccd5ff);
    }
    .card h2 {
      color: #fff;
      font-size: 1.18rem;
      font-weight: 600;
      margin-bottom: 18px;
      margin-top: 0;
      z-index: 1;
      position: relative;
    }
    .card p {
      color: #ccd8ff;
      font-size: 1rem;
      margin-bottom: 36px;
      margin-top: 0;
      z-index: 1;
      position: relative;
    }
    .start-btn {
      background: linear-gradient(90deg, #edf2ff 80%, #d7efff 100%);
      color: #232442;
      font-weight: 500;
      padding: 16px 0;
      font-size: 1.05rem;
      width: 100%;
      border-radius: 14px;
      border: none;
      cursor: pointer;
      box-shadow: 0 4px 22px #2e40fc44;
      transition: box-shadow 0.2s;
      z-index: 1;
      position: relative;
    }
    .start-btn:hover {
      box-shadow: 0 7px 34px #4b5dfc88;
    }
  </style>
</head>
<body>
  <div class="card">
    <div class="icon-glow">
      <svg viewBox="0 0 24 24">
        <path d="M12 2.5l2.3 6.9h7.2l-5.8 4.2 2.2 7-5.9-4.2-5.9 4.2 2.3-7-5.8-4.2h7.2z"/>
      </svg>
    </div>
    <h2>Solve your problem with<br>elegance.</h2>
    <p>
      The ultimate AI companion for designers<br>
      enhance your creativity and accelerate your<br>
      project delivery.
    </p>
    <button class="start-btn">
      Get started &rarr;
    </button>
  </div>
</body>
</html>
"""

@app.route("/")
def home():
    return render_template_string(HTML)

if __name__ == "__main__":
    app.run(port=5000, debug=True)
