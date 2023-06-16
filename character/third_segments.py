from character.metrics import hSegment
from character import lib, errors

from scripts import processor
from scripts.processor import model_oneformer_ade20k

def segment(image_b64, algorithm):
    if algorithm == "seg_ufade20k":
        return segment_ufade20k(image_b64)
    elif algorithm == "seg_ofcoco":
        return segment_ofcoco(image_b64)
    elif algorithm == "seg_ofade20k":
        return segment_ofade20k(image_b64)
    else:
        raise errors.ApiException(errors.code_character_unknown_algorithm, "Unknown algorithm")

@hSegment.time()
def segment_ufade20k(image_b64):

    return []

@hSegment.time()
def segment_ofcoco(image_b64):
    return []

@hSegment.time()
def segment_ofade20k(image_b64):
    img, _ = processor.resize_image_with_pad(img, 512)
    
    global model_oneformer_ade20k
    if model_oneformer_ade20k is None:
        from annotator.oneformer import OneformerDetector
        model_oneformer_ade20k = OneformerDetector(OneformerDetector.configs["ade20k"])

    result = model_oneformer_ade20k(img)
    return [{
        "label": "",
        "score": 1.0,
        "image": result
    }]
