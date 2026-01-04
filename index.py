import json
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime
from flask import Flask, request, jsonify
import os

app = Flask(__name__)

class SimplePredictor:
    def fetch_data(self):
        try:
            tickers = ['^NSEI', 'NSEI.NS']
            for ticker in tickers:
                try:
                    data = yf.download(ticker, period='1mo', progress=False)
                    if not data.empty:
                        return data
                except:
                    continue
            return self.create_sample_data()
        except:
            return self.create_sample_data()
    
    def create_sample_data(self):
        dates = pd.date_range(end=datetime.now(), periods=30, freq='B')
        prices = 22000 + np.random.randn(30).cumsum() * 100
        return pd.DataFrame({
            'Open': prices * 0.99,
            'High': prices * 1.01,
            'Low': prices * 0.98,
            'Close': prices,
            'Volume': np.random.randint(1000000, 5000000, 30)
        }, index=dates)
    
    def predict(self, data):
        try:
            current_price = float(data['Close'].iloc[-1])
            if len(data) > 1:
                prev_price = float(data['Close'].iloc[-2])
                change = ((current_price - prev_price) / prev_price * 100)
                
                if change > 0.3:
                    prediction = 'BULLISH'
                    confidence = min(70 + change, 90)
                elif change < -0.3:
                    prediction = 'BEARISH'
                    confidence = min(70 + abs(change), 90)
                else:
                    prediction = 'NEUTRAL'
                    confidence = 60
            else:
                prediction = 'NEUTRAL'
                confidence = 55
            
            return prediction, round(confidence, 1), current_price
        except:
            return 'NEUTRAL', 55.0, 22000

predictor = SimplePredictor()

@app.route('/', methods=['GET'])
def home():
    html = '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Nifty 50 AI Predictor</title>
        <style>
            body { font-family: Arial; margin: 0; padding: 20px; background: #0f172a; color: white; }
            .container { max-width: 800px; margin: 0 auto; }
            .header { text-align: center; padding: 40px; background: linear-gradient(135deg, #1e40af, #7c3aed); border-radius: 20px; margin-bottom: 30px; }
            .prediction { padding: 30px; margin: 20px 0; border-radius: 15px; text-align: center; }
            .bullish { background: linear-gradient(135deg, #065f46, #047857); }
            .bearish { background: linear-gradient(135deg, #7f1d1d, #991b1b); }
            .neutral { background: linear-gradient(135deg, #854d0e, #a16207); }
            .btn { background: #3b82f6; color: white; padding: 12px 24px; border: none; border-radius: 10px; font-size: 16px; cursor: pointer; margin: 10px; }
            .stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 15px; margin: 30px 0; }
            .stat { background: rgba(255,255,255,0.1); padding: 20px; border-radius: 10px; text-align: center; }
            .disclaimer { background: rgba(239,68,68,0.2); padding: 15px; border-radius: 10px; margin: 20px 0; border: 1px solid rgba(239,68,68,0.3); }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>📈 Nifty 50 AI Predictor</h1>
                <p>Real-time Market Analysis</p>
            </div>
            
            <div style="text-align: center;">
                <button class="btn" onclick="getPrediction()">Get Prediction</button>
                <button class="btn" onclick="autoRefresh()" id="autoBtn">Auto Refresh (30s)</button>
            </div>
            
            <div id="prediction" class="prediction neutral">
                <h2>Click "Get Prediction" to start</h2>
            </div>
            
            <div class="stats">
                <div class="stat">
                    <h3 id="price">--</h3>
                    <p>Current Price</p>
                </div>
                <div class="stat">
                    <h3 id="change">--</h3>
                    <p>Today's Change</p>
                </div>
                <div class="stat">
                    <h3 id="confidence">--</h3>
                    <p>Confidence</p>
                </div>
                <div class="stat">
                    <h3 id="time">--</h3>
                    <p>Last Updated</p>
                </div>
            </div>
            
            <div class="disclaimer">
                <p>⚠️ <strong>Disclaimer:</strong> This is for educational purposes only. Not financial advice.</p>
            </div>
        </div>
        
        <script>
            let autoInterval = null;
            
            function getPrediction() {
                fetch('/api/predict')
                    .then(r => r.json())
                    .then(data => updateUI(data));
            }
            
            function updateUI(data) {
                const predDiv = document.getElementById('prediction');
                predDiv.innerHTML = `<h2>${data.prediction}</h2><p>${data.analysis}</p>`;
                predDiv.className = `prediction ${data.prediction.toLowerCase()}`;
                
                document.getElementById('price').textContent = data.current_price;
                document.getElementById('change').textContent = data.today_change;
                document.getElementById('change').style.color = data.today_change.includes('+') ? '#10b981' : '#ef4444';
                document.getElementById('confidence').textContent = data.confidence + '%';
                document.getElementById('time').textContent = new Date().toLocaleTimeString();
            }
            
            function autoRefresh() {
                const btn = document.getElementById('autoBtn');
                if (autoInterval) {
                    clearInterval(autoInterval);
                    autoInterval = null;
                    btn.textContent = 'Auto Refresh (30s)';
                } else {
                    autoInterval = setInterval(getPrediction, 30000);
                    btn.textContent = 'Stop Auto Refresh';
                    getPrediction();
                }
            }
            
            getPrediction();
        </script>
    </body>
    </html>
    '''
    return html

@app.route('/api/predict', methods=['GET'])
def get_prediction():
    data = predictor.fetch_data()
    prediction, confidence, current_price = predictor.predict(data)
    
    # Calculate change
    if len(data) > 1:
        prev_price = float(data['Close'].iloc[-2])
        change = ((current_price - prev_price) / prev_price * 100)
        today_change = f"{'+' if change >= 0 else ''}{change:.2f}%"
    else:
        today_change = "0.00%"
    
    analysis = {
        'BULLISH': 'Positive momentum detected',
        'BEARISH': 'Downward pressure observed',
        'NEUTRAL': 'Market in consolidation'
    }.get(prediction, 'Analyzing market data')
    
    return jsonify({
        'prediction': prediction,
        'confidence': confidence,
        'current_price': f'₹{current_price:,.2f}',
        'today_change': today_change,
        'analysis': analysis,
        'timestamp': datetime.now().strftime('%H:%M:%S')
    })

# For Vercel
if __name__ == '__main__':
    app.run(debug=False)
else:
    # Export for Vercel
    handler = app