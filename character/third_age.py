from character import lib
from modules import devices

from transformers import ViTFeatureExtractor, ViTForImageClassification

class AgeClassifier:
    def __init__(self):
        self.device = devices.get_device_for("ageclassifier")
        self.model = ViTForImageClassification.from_pretrained('nateraw/vit-age-classifier', cache_dir=lib.models_path)
        self.transforms = ViTFeatureExtractor.from_pretrained('nateraw/vit-age-classifier', cache_dir=lib.models_path)

    def unload_model(self):
        if self.model is not None:
            self.model.cpu()

    def __call__(self, img):
        self.model.to(self.device)

        # Transform our image and pass it through the model
        inputs = self.transforms(img, return_tensors='pt')
        output = self.model(**inputs)

        # Predicted Class probabilities
        proba = output.logits.softmax(1)

        # Predicted Classes
        return proba.argmax(1)


model_age_classifier = None


def get_age(img):
    global model_age_classifier
    if model_age_classifier is None:
        model_age_classifier = AgeClassifier()
    
    return model_age_classifier(img)