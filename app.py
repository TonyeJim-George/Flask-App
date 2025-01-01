import os
import pickle
from flask import Flask, render_template, request, redirect, url_for
import psycopg2
from psycopg2.extras import RealDictCursor
from urllib.parse import urlparse

app = Flask(__name__)

# Load the machine learning model
model_file_path = 'randomforest6.pkl'
with open(model_file_path, 'rb') as file:
    model = pickle.load(file)

# Use Vercel PostgreSQL credentials from the environment
DATABASE_URL = os.getenv('DATABASE_URL')  # Vercel injects this environment variable

if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable not set. Check your Vercel configuration.")

# Parse DATABASE_URL for psycopg2 connection
url = urlparse(DATABASE_URL)
db_params = {
    'dbname': url.path[1:],
    'user': url.username,
    'password': url.password,
    'host': url.hostname,
    'port': url.port or 5432
}

# Function to insert data into the PostgreSQL database
def insert_user_data(height, weight, gender, prediction):
    try:
        with psycopg2.connect(**db_params, sslmode="require") as conn:
            with conn.cursor() as cursor:
                query = """
                INSERT INTO users (height, weight, gender, predicted_shoe_size) 
                VALUES (%s, %s, %s, %s) RETURNING id
                """
                cursor.execute(query, (height, weight, gender, prediction))
                user_id = cursor.fetchone()[0]
                return user_id
    except Exception as e:
        print(f"Error inserting data: {e}")
        raise

# Function to update shoe size in the PostgreSQL database
def update_shoe_size(user_id, shoe_size):
    try:
        with psycopg2.connect(**db_params, sslmode="require") as conn:
            with conn.cursor() as cursor:
                query = """
                UPDATE users SET shoe_size = %s WHERE id = %s
                """
                cursor.execute(query, (shoe_size, user_id))
    except Exception as e:
        print(f"Error updating data: {e}")
        raise

# Route to display the form and handle user input
@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        try:
            # Get user input
            height = float(request.form['height'])
            weight = float(request.form['weight'])
            gender = request.form['gender']
            
            # Gender mapping: female -> 1, male -> 0
            if gender not in ['male', 'female']:
                return "Invalid gender. Please select 'male' or 'female'.", 400
            gender = 1 if gender == 'female' else 0

            # Prepare data for prediction (model expects height, weight, gender)
            input_data = [[height, weight, gender]]
            prediction = model.predict(input_data)[0]

            # Round the prediction to the nearest whole number
            rounded_prediction = round(prediction)

            # Store data in PostgreSQL, including the rounded prediction
            user_id = insert_user_data(height, weight, gender, rounded_prediction)

            # Redirect to the prediction page with the user ID and predicted result
            return redirect(url_for('predict', user_id=user_id, prediction=rounded_prediction))
        except Exception as e:
            return f"An error occurred: {e}", 500

    return render_template('index.html')

# Route to handle prediction and asking for shoe size
@app.route('/predict', methods=['GET', 'POST'])
def predict():
    user_id = request.args.get('user_id')
    prediction = request.args.get('prediction')

    if request.method == 'POST':
        try:
            # Get actual shoe size from user input
            shoe_size = int(request.form['shoe_size'])

            # Update the database with the actual shoe size
            update_shoe_size(user_id, shoe_size)

            return "Thank you for submitting your shoe size!"
        except Exception as e:
            return f"An error occurred: {e}", 500

    return render_template('predict.html', prediction=prediction, user_id=user_id)

if __name__ == '__main__':
    app.run(debug=False)
