import yfinance as yf
import pandas as pd
import re
from datetime import datetime, timedelta
from textblob import TextBlob

class StockChatbot:
    def __init__(self, prediction_model):
        self.model = prediction_model
        self.stock_data_cache = {}
        
    def process_message(self, message):
        # Clean and analyze the message
        message = message.lower().strip()
        sentiment = self.analyze_sentiment(message)
        
        # Extract stock symbol
        symbol = self.extract_stock_symbol(message)
        if not symbol:
            return "Please specify a stock ticker symbol (e.g., AAPL, MSFT)"
        
        # Determine intent
        if any(word in message for word in ['predict', 'forecast', 'tomorrow', 'next week']):
            return self.handle_prediction_request(symbol)
        elif any(word in message for word in ['price', 'current', 'today']):
            return self.handle_current_price_request(symbol)
        elif any(word in message for word in ['history', 'chart', 'graph']):
            return self.handle_historical_request(symbol)
        else:
            return self.handle_general_info(symbol, sentiment)
    
    def extract_stock_symbol(self, text):
        # Simple pattern matching for stock symbols
        matches = re.findall(r'\b[A-Z]{1,5}\b', text.upper())
        return matches[0] if matches else None
    
    def analyze_sentiment(self, text):
        analysis = TextBlob(text)
        return analysis.sentiment.polarity
    
    def handle_prediction_request(self, symbol):
        try:
            data = self.get_stock_data(symbol, period="1d")
            if data.empty:
                return f"Could not fetch data for {symbol}. Please check the ticker symbol."
            
            features = data[['Open', 'High', 'Low', 'Close', 'Volume']]
            prediction = self.model.predict(features)
            return f"Predicted next closing price for {symbol}: ${prediction[0]:.2f}"
        except Exception as e:
            return f"Sorry, I couldn't make a prediction for {symbol}. Error: {str(e)}"
    
    def handle_current_price_request(self, symbol):
        try:
            data = yf.download(symbol, period="1d")
            if data.empty:
                return f"Could not fetch current price for {symbol}. Please check the ticker symbol."
            return f"Current {symbol} price: ${data['Close'].iloc[-1]:.2f}"
        except Exception as e:
            return f"Sorry, I couldn't fetch the price for {symbol}. Error: {str(e)}"
    
    def handle_historical_request(self, symbol):
        return f"Here's the link to historical data for {symbol}: /graph/{symbol}"
    
    def handle_general_info(self, symbol, sentiment):
        try:
            stock = yf.Ticker(symbol)
            info = stock.info
            name = info.get('longName', symbol)
            sector = info.get('sector', 'unknown sector')
            current_price = info.get('currentPrice', 'unknown price')
            
            sentiment_msg = "neutral"
            if sentiment > 0.2:
                sentiment_msg = "positive"
            elif sentiment < -0.2:
                sentiment_msg = "negative"
                
            return (f"{name} ({symbol}) is a {sector} company. "
                   f"Current price: ${current_price}. "
                   f"Market sentiment appears {sentiment_msg}.")
        except Exception as e:
            return f"Sorry, I couldn't fetch information for {symbol}. Error: {str(e)}"
    
    def get_stock_data(self, symbol, period="1y"):
        if symbol not in self.stock_data_cache:
            self.stock_data_cache[symbol] = yf.download(symbol, period=period)
        return self.stock_data_cache[symbol]