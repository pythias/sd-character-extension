import numpy as np
from regex import F
import torch
import cv2
import base64

from character import lib, errors, models, names, input
from character.metrics import hSegment

from modules.api.api import decode_base64_to_image, encode_pil_to_base64
from PIL import Image, ImageOps

lib.load_extension("sd-webui-controlnet")
from scripts.processor import model_oneformer_ade20k, model_oneformer_coco, resize_image_with_pad
from annotator.util import HWC3
from annotator.oneformer.oneformer.demo.visualizer import Visualizer, ColorMode

_OFF_WHITE = (1.0, 1.0, 1.0)
_OFF_BLACK = (0.0, 0.0, 0.0)

def segment(image_b64, algorithm, mask_color=None, background_color=255):
    if algorithm == models.SegmentAlgorithm.OFCOCO:
        return segment_ofcoco(image_b64, mask_color, background_color)
    elif algorithm == models.SegmentAlgorithm.OFADE20K:
        return segment_ofade20k(image_b64, mask_color, background_color)
    else:
        return segment_ufade20k(image_b64, mask_color, background_color)


@hSegment.time()
def segment_ufade20k(image_b64, mask_color=None, background_color=255):
    raise errors.ApiException(errors.code_not_ready_yet, "Not ready to open yet")


@hSegment.time()
def segment_ofcoco(image_b64, mask_color=None, background_color=255):
    global model_oneformer_coco
    if model_oneformer_coco is None:
        from annotator.oneformer import OneformerDetector
        model_oneformer_coco = OneformerDetector(OneformerDetector.configs["coco"])
    
    return _run(image_b64, model_oneformer_coco, mask_color, background_color)


@hSegment.time()
def segment_ofade20k(image_b64, mask_color=None, background_color=255):
    global model_oneformer_ade20k
    if model_oneformer_ade20k is None:
        from annotator.oneformer import OneformerDetector
        model_oneformer_ade20k = OneformerDetector(OneformerDetector.configs["ade20k"])
    
    return _run(image_b64, model_oneformer_ade20k, mask_color, background_color)

    
def _run(b64, preprocessor, mask_color, background_color):
    if preprocessor.model is None:
        preprocessor.load_model()

    preprocessor.model.model.to(preprocessor.device)    
    predictor = preprocessor.model
    metadata = preprocessor.metadata
    segments = []

    img = HWC3(np.asarray(decode_base64_to_image(b64)))
    img, remove_pad = resize_image_with_pad(img, 512)

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
            if mask_color is None:
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
            alpha=1.0,
            is_text=False,
        )
        segment_mask = visualizer_map.output.get_image()
        segment_mask = remove_pad(segment_mask)
        segment_image = np.where(binary_mask[..., None], img, background_color)

        segments.append({
            "label": text,
            "score": 1.0,
            "mask": segment_mask,
            "color": segment_image
        })

    return segments


def to_items(segments):
    return [models.SegmentItem(
        label = s["label"],
        score = s["score"],
        color = lib.encode_to_base64(s["color"])
    ) for s in segments]


def prepare_for_segments(request):
    models.prepare_request(request)

    segment_image = input.get_extra_value(request, names.ParamImage, None)
    if segment_image is None:
        lib.log("segment_image is None")
        return
    
    segment_labels = input.get_extra_value(request, names.ParamSegmentLabels, None)
    segment_erase = input.get_extra_value(request, names.ParamSegmentErase, False)
    if segment_labels is None:
        lib.log("segment_labels is None")
        return
    
    segment_algorithm = input.get_extra_value(request, 'segment_algorithm', models.SegmentAlgorithm.OFADE20K)
    segments = segment(segment_image, segment_algorithm, mask_color=[0, 0, 0])
    if not segments:
        lib.log("segments is None")
        return

    segment_masks = []
    for s in segments:
        if s["label"] in segment_labels:
            segment_masks.append(s["mask"])
        
    if not segment_masks:
        lib.log("segment_masks is None")
        return
    
    # 不要caption
    input.update_extra(request, names.ParamIgnoreCaption, True)

    if len(segment_masks) == 1:
        mask_merged = segment_masks[0]
    else:
        mask_merged = np.maximum.reduce(segment_masks)

    # 缩放蒙版至原图大小
    img = lib.valid_base64(segment_image)
    height, width = img.size[0], img.size[1]
    mask_resized = cv2.resize(mask_merged, (height, width), interpolation=cv2.INTER_NEAREST)

    _, mask_buffer = cv2.imencode('.png', mask_resized)
    mask_base64 = base64.b64encode(mask_buffer).decode('utf-8')

    request.init_images = [segment_image]
    request.mask = mask_base64
    request.inpainting_mask_invert = segment_erase
    request.inpainting_fill = 1
    
    if input.is_debug(request):
        input.update_extra(request, "debug-segment-size", (height, width))
        input.update_extra(request, "debug-segment-input", segment_image)
        input.update_extra(request, "debug-segment-invert", encode_pil_to_base64(ImageOps.invert(Image.fromarray(mask_resized))).decode('utf-8'))
        input.update_extra(request, "debug-segment", mask_base64)
        input.update_extra(request, "debug-segment-masks", len(segment_masks))

def prepare_for_background(request):
    models.prepare_request(request)
    