import os

from character import lib
from modules import devices, paths
from modules.api import api

from transformers import ViTFeatureExtractor, ViTForImageClassification

class AgeClassifier:
    def __init__(self):
        self.model = None
        self.transforms = None

    def load(self):
        if self.model is not None:
            return
        
        model_path = os.path.join(paths.models_path, 'vit-age-classifier')
        self.model = ViTForImageClassification.from_pretrained(model_path)
        self.transforms = ViTFeatureExtractor.from_pretrained(model_path)
        self.model.to(devices.cpu)

        lib.log(f"AgeClassifier model loaded, from: {model_path}")


    def start(self):
        self.load()
        self.model.to(devices.device)


    def stop(self):
        self.model.to(devices.cpu)
        devices.torch_gc()


    def __call__(self, img):
        self.start()

        if isinstance(img, str):
            img = lib.download_to_base64(img)
            img = api.decode_base64_to_image(img)

        img = img.convert('RGB')

        # Transform our image and pass it through the model
        inputs = self.transforms(img, return_tensors='pt')
        inputs.to(devices.device)

        output = self.model(**inputs)

        # Predicted Class probabilities
        probabilities = output.logits.softmax(1)

        # Predicted Classes
        max = probabilities.argmax(1)
        id = int(max[0].int())

        if id not in self.model.config.id2label:
            age = 80
        else:
            range = self.model.config.id2label[id]
            age = int(range.split('-')[0])

        # Adjust age
        if age < 60 and age >= 20:
            age = int(age * 0.75)
    
        self.stop()

        return age


model_age_classifier = None


def get_age(img):
    global model_age_classifier
    if model_age_classifier is None:
        model_age_classifier = AgeClassifier()
    
    age = -1
    try:
        age = model_age_classifier(img)
    except Exception as e:
        lib.error(f"AgeClassifier error: {e}")

    return age