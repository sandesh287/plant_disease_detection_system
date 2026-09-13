import os

os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "2")

import tensorflow as tf
import numpy as np
import joblib
from keras.preprocessing import image
from pathlib import Path

tf.get_logger().setLevel("ERROR")

# Broad set of plant and agricultural categories recognized by ImageNet
PLANT_KEYWORDS = {
    "plant", "tree", "flower", "rose", "daisy", "tulip", "orchid",
    "sunflower", "cardoon", "zucchini", "squash", "cucumber", "artichoke",
    "cabbage", "broccoli", "cauliflower", "lemon", "orange", "banana",
    "apple", "strawberry", "pineapple", "corn", "fig", "pomegranate",
    "hay", "grass", "houseplant", "vegetable", "granny_smith", "bell_pepper",
    "head_cabbage", "acorn_squash", "butternut_squash", "spaghetti_squash",
    "rapeseed", "buckeye", "hip",
}

def get_plant_classification(file_path):
    """Backend helper function: Validates whether the image contains a plant."""
    img = image.load_img(file_path, target_size=(224, 224))
    img_array = image.img_to_array(img)
    img_array = np.expand_dims(img_array, axis=0)
    img_array = tf.keras.applications.mobilenet_v2.preprocess_input(img_array)

    preds = get_plant_classifier().predict(img_array, verbose=0)
    decoded = tf.keras.applications.mobilenet_v2.decode_predictions(preds, top=10)[0]

    matches = []
    for _, label, score in decoded:
        normalized_label = label.lower().replace("-", "_")
        label_words = set(normalized_label.split("_"))
        is_match = (
            normalized_label in PLANT_KEYWORDS
            or bool(label_words.intersection(PLANT_KEYWORDS))
        )
        if is_match:
            matches.append({"label": label, "score": float(score)})

    is_plant = any(match["score"] >= 0.05 for match in matches)
    return {
        "is_plant": is_plant,
        "predictions": [
            {"label": label, "score": float(score)}
            for _, label, score in decoded
        ],
        "matches": matches,
    }


def is_plant_image(file_path):
    return get_plant_classification(file_path)["is_plant"]


# Paths to the saved models
MODEL_DIR = Path(__file__).resolve().parent / "models"
CNN_MODEL_PATH = MODEL_DIR / "fix_model.h5"
RF_MODEL_PATH = MODEL_DIR / "rf_fix_model.pkl"
class_names = ['Apple___Apple_scab', 'Apple___Black_rot', 'Apple___Cedar_apple_rust', 'Apple___healthy', 'Corn___Cercospora_leaf_spot Gray_leaf_spot', 'Corn___Common_rust', 'Corn___Northern_Leaf_Blight', 'Corn___healthy', 'Grape___Black_rot', 'Grape___Esca_(Black_Measles)', 'Grape___Leaf_blight_(Isariopsis_Leaf_Spot)', 'Grape___healthy', 'Tomato___Bacterial_spot', 'Tomato___Early_blight', 'Tomato___Late_blight', 'Tomato___Leaf_Mold', 'Tomato___Septoria_leaf_spot', 'Tomato___Spider_mites Two-spotted_spider_mite', 'Tomato___Target_Spot', 'Tomato___Tomato_Yellow_Leaf_Curl_Virus', 'Tomato___Tomato_mosaic_virus', 'Tomato___healthy']

plant_classifier = None
cnn_model = None
rf_model = None
feature_extractor = None


def get_plant_classifier():
    global plant_classifier

    if plant_classifier is None:
        plant_classifier = tf.keras.applications.MobileNetV2(weights="imagenet")
    return plant_classifier


def get_disease_models():
    global cnn_model, rf_model, feature_extractor

    if cnn_model is None:
        cnn_model = tf.keras.models.load_model(str(CNN_MODEL_PATH), compile=False)
        cnn_model.compile(optimizer='adam', loss='sparse_categorical_crossentropy', metrics=['accuracy'])

    if rf_model is None:
        rf_model = joblib.load(str(RF_MODEL_PATH))

    if feature_extractor is None:
        feature_extractor = tf.keras.Model(
            inputs=cnn_model.inputs,
            outputs=cnn_model.layers[-2].output
        )

    return feature_extractor, rf_model

# Function to preprocess the image
def preprocess_image(img_path):
    img = image.load_img(img_path, target_size=(180, 180))  # Adjust target size if needed
    img = image.img_to_array(img)
    img = np.expand_dims(img, axis=0)
    img = img / 255.0  # Normalize the image
    return img


def extract_features(img):
    """Extract features using the CNN model."""
    feature_extractor, _ = get_disease_models()
    features = feature_extractor.predict(img, verbose=0)
    features = features.reshape(features.shape[0], -1)
    return features

def predict(file_path):
    """Predict the class of the given image."""
    img_array = preprocess_image(file_path)
    features = extract_features(img_array)
    _, rf_model = get_disease_models()
    prediction = rf_model.predict(features)

    # If the prediction is in 2D, access the scalar value
    predicted_class_idx = prediction[0] if prediction.ndim == 1 else prediction[0][0]

    # Map the prediction index to class name
    predicted_class = class_names[predicted_class_idx]

    return predicted_class
