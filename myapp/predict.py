import numpy as np
import pandas as pd
from tensorflow.keras.models import load_model
from sklearn.preprocessing import StandardScaler

def load_trained_model(model_path):
    return load_model(model_path)

def predict_loyalty_rating(input_features, model, scaler):
    input_df = pd.DataFrame([input_features])
    scaled_features = scaler.transform(input_df)

    predictions = model.predict(scaled_features)
    predicted_rating = np.argmax(predictions, axis=1) + 1

    return predicted_rating[0]

trained_model = load_trained_model('/models/resnet_model.h5')

# Example input
input_features = {
    'CreditScore': 595,
    'Gender': 0,  # {0: 'Female', 1: 'Male'}
    'Age': 44,
    'Tenure': 4,
    'Balance': 96553.52,
    'HasCrCard': 1,
    'IsActiveMember': 0,
    'EstimatedSalary': 143952.24,
    'Satisfaction Score': 4,
    'Card Type': 0  # {0: 'DIAMOND', 1: 'GOLD', 2: 'PLATINUM', 3: 'SILVER'}
}

predict_loyalty_rating(input_features, trained_model, scaler)
