import os
import pickle
from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)

# Load the pre-trained model
model_file_path = 'randomforest6.pkl'  
model = None

with open(model_file_path, 'rb') as file:
    model = pickle.load(file)

# Route to display the form and handle user input
@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        # Get user input
        height = float(request.form['height'])
        weight = float(request.form['weight'])
        gender = request.form['gender']

        # Gender mapping: female -> 1, male -> 0
        gender = 1 if gender == 'female' else 0

        # Prepare data for prediction (model expects height, weight, gender)
        input_data = [[height, weight, gender]]
        prediction = model.predict(input_data)[0]

        # Round the prediction to the nearest whole number
        rounded_prediction = round(prediction)

        # Redirect to the prediction page with the predicted result
        return redirect(url_for('predict', prediction=rounded_prediction))

    return render_template('index.html')

# Route to display the prediction result
@app.route('/predict', methods=['GET'])
def predict():
    prediction = request.args.get('prediction')
    return render_template('predict.html', prediction=prediction)

if __name__ == '__main__':
    app.run(debug=True)
