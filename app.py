import pickle
import numpy as np
from flask import Flask, render_template, request
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.multioutput import MultiOutputClassifier

# Create flask app
app = Flask(__name__)

@app.route('/')
def home():
    return render_template('upload.html')  # Page for uploading CSV


@app.route('/upload_csv', methods=['POST'])
def upload_csv():
    if 'file' not in request.files:
        return "No file part"

    file = request.files['file']

    if file.filename == '':
        return "No selected file"

    # Read the CSV file into a DataFrame
    df = pd.read_csv(file)

    # Ensure the uploaded CSV file has the correct columns
    required_columns = ['Temperature', 'Humidity', 'Light Intensity', 'Air Quality', 'Weather Condition',
                        'Air-quality Condition']
    if not all(column in df.columns for column in required_columns):
        return "Error: CSV file must contain 'Temperature', 'Humidity', 'Light Intensity','Air Quality', 'Weather Condition','Air-quality Condition' columns"

    # Prepare the data
    X = df[['Temperature', 'Humidity', 'Light Intensity', 'Air Quality']]
    y = df[['Weather Condition', 'Air-quality Condition']]

    # Split the dataset into train and test
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    # Feature scaling
    scaler = StandardScaler()
    X_train = scaler.fit_transform(X_train)
    scaler.transform(X_test)

    # Instantiate and train the model
    model = MultiOutputClassifier(RandomForestClassifier())
    model.fit(X_train, y_train)

    # Save the new model and scaler as pickle files
    pickle.dump(model, open('model_new.pkl', 'wb'))
    pickle.dump(scaler, open('scaler_new.pkl', 'wb'))

    return render_template('deploy.html')  # Redirect to the input page


# Page for inputting X variables
@app.route('/deploy')
def deploy():
    return render_template('deploy.html')


@app.route('/result', methods=['POST'])
def result():
    # Load the newly generated model and scaler
    model = pickle.load(open('model_new.pkl', 'rb'))
    scaler = pickle.load(open('scaler_new.pkl', 'rb'))

    # Capture the input values from the form
    temperature = float(request.form.get('a'))
    humidity = float(request.form.get('b'))
    lightintensity = float(request.form.get('c'))
    airquality = float(request.form.get('d'))

    # Prepare the features for prediction
    features = pd.DataFrame([[temperature, humidity, lightintensity, airquality]],
                            columns=['Temperature', 'Humidity', 'Light Intensity', 'Air Quality'])

    # Apply scaling
    features_scaled = scaler.transform(features)

    # Predict using the model
    prediction = model.predict(features_scaled)[0]
    weather_data = prediction[0]  # Weather Condition
    air_quality_data = prediction[1]  # Air-quality Condition

    # Simulate 24-hour prediction data based on the initial input
    predicted_conditions = []
    temperature_values = []
    humidity_values = []
    lightintensity_values = []
    airquality_values = []

    for i in range(24):
        # Introduce slight random variations to simulate realistic changes over 24 hours
        temperature_variation = temperature + np.random.uniform(-0.5, 0.5)
        humidity_variation = humidity + np.random.uniform(-0.5, 0.5)
        lightintensity_variation = lightintensity + np.random.uniform(0, 0.5)
        airquality_variation = airquality + np.random.uniform(-0.5, 0.5)

        # Update the features for each hour
        features_hourly = pd.DataFrame(
            [[temperature_variation, humidity_variation, lightintensity_variation, airquality_variation]],
            columns=['Temperature', 'Humidity', 'Light Intensity', 'Air Quality']
        )
        features_hourly_scaled = scaler.transform(features_hourly)

        # Predict weather condition for each hour
        prediction_hourly = model.predict(features_hourly_scaled)[0]

        # Append the simulated values
        predicted_conditions.append(prediction_hourly)
        temperature_values.append(temperature_variation)
        humidity_values.append(humidity_variation)
        lightintensity_values.append(lightintensity_variation)
        airquality_values.append(airquality_variation)

    # Render the result template with context
    return render_template('result.html',
                           predicted_conditions=predicted_conditions,
                           temperature_values=temperature_values,
                           humidity_values=humidity_values,
                           lightintensity_values=lightintensity_values,
                           airquality_values=airquality_values,
                           weather_data=weather_data,
                           air_quality_data=air_quality_data)

if __name__ == "__main__":
    app.run(debug=True)
