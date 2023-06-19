from curses import meta
from character.metrics import hSegment
from character import lib, errors, models

from modules.api.api import decode_base64_to_image

from scripts import processor
from scripts.processor import model_oneformer_ade20k, model_oneformer_coco

from annotator.util import HWC3
from annotator.oneformer.oneformer.demo.visualizer import Visualizer, ColorMode

import numpy as np
import torch

_OFF_WHITE = (1.0, 1.0, 1.0)


def segment(image_b64, algorithm):
    if algorithm == models.SegmentAlgorithm.OFCOCO:
        return segment_ofcoco(image_b64)
    elif algorithm == models.SegmentAlgorithm.OFADE20K:
        return segment_ofade20k(image_b64)
    else:
        return segment_ufade20k(image_b64)


@hSegment.time()
def segment_ufade20k(image_b64):
    raise errors.ApiException(errors.code_not_ready_yet, "Not ready to open yet")


@hSegment.time()
def segment_ofcoco(image_b64):
    global model_oneformer_coco
    if model_oneformer_coco is None:
        from annotator.oneformer import OneformerDetector
        model_oneformer_coco = OneformerDetector(OneformerDetector.configs["coco"])
    
    return _run(image_b64, model_oneformer_coco)


@hSegment.time()
def segment_ofade20k(image_b64):
    global model_oneformer_ade20k
    if model_oneformer_ade20k is None:
        from annotator.oneformer import OneformerDetector
        model_oneformer_ade20k = OneformerDetector(OneformerDetector.configs["ade20k"])
    
    return _run(image_b64, model_oneformer_ade20k)

    
def _run(b64, preprocessor):
    if preprocessor.model is None:
        preprocessor.load_model()

    preprocessor.model.model.to(preprocessor.device)    
    predictor = preprocessor.model
    metadata = preprocessor.metadata
    segments = []

    img = HWC3(np.asarray(decode_base64_to_image(b64)))
    img, remove_pad = processor.resize_image_with_pad(img, 512)

    predictions = predictor(img[:, :, ::-1], "semantic") 
    sem_seg = predictions["sem_seg"].argmax(dim=0).cpu()
    if isinstance(sem_seg, torch.Tensor):
        sem_seg = sem_seg.numpy()
    labels, areas = np.unique(sem_seg, return_counts=True)
    sorted_idxs = np.argsort(-areas).tolist()
    labels = labels[sorted_idxs]

    # 目前 coco 和 ade20k 的label列表都还不够详细到衣服，无法实现换装的效果。
    # 方案2：可以通过脸抠出来保留，人扣出来重新绘制，两次ControlNet的方式。
    
    for label in filter(lambda l: l < len(metadata.stuff_classes), labels):
        try:
            mask_color = [x / 255 for x in metadata.stuff_colors[label]]
        except (AttributeError, IndexError):
            mask_color = None

        binary_mask = (sem_seg == label).astype(np.uint8)
        text = metadata.stuff_classes[label]

        visualizer_map = Visualizer(img, is_img=False, metadata=metadata, instance_mode=ColorMode.IMAGE)
        visualizer_map.draw_binary_mask(
            binary_mask,
            color=mask_color,
            edge_color=_OFF_WHITE,
            text=text,
            alpha=0.8,
            area_threshold=None,
            is_text=False,
        )
        result = visualizer_map.output.get_image()
        result = remove_pad(result)

        segment = models.SegmentItem(label = text, score = 1.0, mask = lib.encode_to_base64(result))
        segments.append(segment)

    return segments
