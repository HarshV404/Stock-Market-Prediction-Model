from flask import Flask, jsonify, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from database import init_db, add_user, get_user_by_email, check_user_password
import yfinance as yf
from dotenv import load_dotenv
import joblib
import pandas as pd
import plotly.graph_objects as go
from chatbot_engine import StockChatbot
from flask_wtf.csrf import CSRFProtect


load_dotenv()

app = Flask(__name__)

# Initialize the database
app.config['SECRET_KEY'] = 'your_secret_key_here'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'  # Using SQLite database
app.config['SQLALCHEMY_TRACK_MODIFfICATIONS'] = False

# Initialize database and login manager
init_db(app)
csrf = CSRFProtect(app)  # Add this line after app creation
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# Load the trained model
model = joblib.load('stock_model.pkl')

# User loader for Flask-Login
@login_manager.user_loader
def load_user(user_id):
    from database import db, User
    return db.session.get(User, int(user_id))

# Routes for authentication
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        email = request.form['email']
        username = request.form['username']
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        if password != confirm_password:
            flash("Passwords do not match!", category="error")
            return redirect(url_for('signup'))

        if get_user_by_email(email):
            flash("Email already exists.", category="error")
            return render_template('index.html');

        add_user(email, username, password)
        flash("Account created successfully!", category="success")
        return redirect(url_for('login'))

    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        if not email or not password:
            flash("Email and password are required.", category="error")
            return redirect(url_for('login'))

        user = get_user_by_email(email)
        if user and check_user_password(user, password):
            login_user(user)
            flash("Logged in successfully!", category="success")
            return redirect(url_for('index'))
        else:
            flash("Invalid credentials.", category="error")
            return redirect(url_for('login'))

    return render_template('signup.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash("Logged out successfully.", category="success")
    return redirect(url_for('signup'))

# Your existing routes (index, graph, table)
@app.route('/', methods=['GET', 'POST'])
@login_required
def index():
    prediction = None
    if request.method == 'POST':
        # Get the ticker symbol from the form
        ticker = request.form['ticker']

        # Fetch historical data for the entire year
        start_date = "2023-01-01"
        end_date = pd.Timestamp.today().strftime('%Y-%m-%d')
        historical_data = yf.download(ticker, start=start_date, end=end_date)

        # Check if historical data is empty
        if not historical_data.empty:
            # Fetch the latest data for prediction
            latest_data = yf.download(ticker, period="1d")

            # Prepare the latest data for prediction
            latest_features = latest_data[['Open', 'High', 'Low', 'Close', 'Volume']]

            # Predict the next day's closing price
            predicted_price = model.predict(latest_features)
            prediction = round(predicted_price[0], 2)

    return render_template('index.html', prediction=prediction)

@app.route('/graph/<ticker>')
@login_required
def graph(ticker):
    start_date = "2023-01-01"
    end_date = pd.Timestamp.today().strftime('%Y-%m-%d')
    historical_data = yf.download(ticker, start=start_date, end=end_date)

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=historical_data.index,
        y=historical_data['Close'],
        mode='lines+markers',
        name='Closing Price'
    ))
    fig.update_layout(
        title=f"{ticker} Historical Stock Prices (2023)",
        xaxis_title="Date",
        yaxis_title="Price (USD)",
        template="plotly_dark"
    )

    graph_html = fig.to_html(full_html=False)
    return render_template('graph.html', graph_html=graph_html, ticker=ticker)

@app.route('/table/<ticker>')
@login_required
def table(ticker):
    start_date = "2023-01-01"
    end_date = pd.Timestamp.today().strftime('%Y-%m-%d')
    historical_data = yf.download(ticker, start=start_date, end=end_date)

    # Format the index (dates) to a consistent format
    historical_data.index = historical_data.index.strftime('%Y-%m-%d')

    # Convert the historical data to an HTML table
    historical_table = historical_data.to_html(classes='table table-striped', index=True)
    return render_template('table.html', historical_table=historical_table, ticker=ticker)

@app.route('/settings')
@login_required
def settings():
    return render_template('settings.html')

def get_bot_response(user_message):
    """Get chatbot response using our StockChatbot engine"""
    try:
        chatbot = StockChatbot(model)  # Use the loaded model
        return chatbot.process_message(user_message)
    except Exception as e:
        print(f"Error in chatbot processing: {e}")
        return "Sorry, I encountered an error processing your request."

# Update the /get-response route to include user context
@app.route('/get-response', methods=['POST'])
@login_required
def get_response():
    if not request.is_json:
        return jsonify({'error': 'Request must be JSON'}), 400
        
    data = request.get_json()
    user_msg = data.get('message')
    
    if not user_msg:
        return jsonify({'error': 'Message is required'}), 400
        
    try:
        bot_msg = get_bot_response(user_msg)
        return jsonify({'response': bot_msg})
    except Exception as e:
        app.logger.error(f"Error in get_response: {str(e)}")
        return jsonify({'response': "Sorry, I'm having trouble processing your request."}), 500
    
@app.route('/chatbot')
@login_required
def chatbot():
    return render_template('chatbot.html')

if __name__ == '__main__':
    app.run(debug=True)
