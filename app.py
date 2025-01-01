import os
import pickle
from flask import Flask, render_template, request, redirect, url_for
import psycopg2

app = Flask(__name__)


model_file_path = 'randomforest6.pkl'  
model = None

with open(model_file_path, 'rb') as file:
    model = pickle.load(file)


db_config = {
    'dbname': 'shoe-size',  
    'user': 'postgres',    
    'password': 'Tonye_0455',  
    'host': 'localhost',       
    'port': '5432'             
}

# Function to insert data into the PostgreSQL database
def insert_user_data(height, weight, gender, prediction):
    conn = psycopg2.connect(**db_config)
    cursor = conn.cursor()
    query = """
    INSERT INTO users (height, weight, gender, predicted_shoe_size) 
    VALUES (%s, %s, %s, %s) RETURNING id
    """
    cursor.execute(query, (height, weight, gender, prediction))
    user_id = cursor.fetchone()[0]
    conn.commit()
    cursor.close()
    conn.close()
    return user_id

# Route to display the form and handle user input
@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        # Get user input
        height = float(request.form['height'])
        weight = float(request.form['weight'])
        gender = request.form['gender']
        
        # Gender mapping: female -> 1, male -> 0
        if gender == 'female':
            gender = 1
        elif gender == 'male':
            gender = 0
        else:
            gender = None

        # Prepare data for prediction (model expects height, weight, gender)
        input_data = [[height, weight, gender]]
        prediction = model.predict(input_data)[0]

        # Round the prediction to the nearest whole number
        rounded_prediction = round(prediction)

        # Store data in PostgreSQL, including the rounded prediction
        user_id = insert_user_data(height, weight, gender, rounded_prediction)

        # Redirect to the prediction page with the user ID and predicted result
        return redirect(url_for('predict', user_id=user_id, prediction=rounded_prediction))

    return render_template('index.html')

# Route to handle prediction and asking for shoe size
@app.route('/predict', methods=['GET', 'POST'])
def predict():
    user_id = request.args.get('user_id')
    prediction = request.args.get('prediction')

    if request.method == 'POST':
        # Get actual shoe size from user input
        shoe_size = int(request.form['shoe_size'])

        # Update the database with the actual shoe size
        conn = psycopg2.connect(**db_config)
        cursor = conn.cursor()
        query = """
        UPDATE users SET shoe_size = %s WHERE id = %s
        """
        cursor.execute(query, (shoe_size, user_id))
        conn.commit()
        cursor.close()
        conn.close()

        return "Thank you for submitting your shoe size!"

    return render_template('predict.html', prediction=prediction, user_id=user_id)

if __name__ == '__main__':
    app.run(debug=True)
