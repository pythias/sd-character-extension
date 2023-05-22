import cv2
import gradio as gr
import modules.scripts as scripts
import modules.shared as shared
import numpy as np
import torch

from facexlib.detection import RetinaFace, init_detection_model, retinaface
from facexlib.parsing import BiSeNet, init_parsing_model
from facexlib.utils.misc import img2tensor
from PIL import Image
from torchvision.transforms.functional import normalize
from typing import Optional
from operator import attrgetter

from modules.processing import Processed, StableDiffusionProcessing, StableDiffusionProcessingImg2Img, process_images

from character import face, lib
from character.metrics import hRepair, cRepair

class Face:
    def __init__(self, entire_image: np.ndarray, face_box: np.ndarray, face_margin: float):
        left, top, right, bottom = self.__to_square(face_box)

        self.left, self.top, self.right, self.bottom = self.__ensure_margin(left, top, right, bottom, entire_image, face_margin)
        self.width = self.right - self.left
        self.height = self.bottom - self.top
        self.image = self.__crop_face_image(entire_image)

    def __crop_face_image(self, entire_image: np.ndarray):
        cropped = entire_image[self.top: self.bottom, self.left: self.right, :]
        return Image.fromarray(cv2.resize(cropped, dsize=(512, 512)))

    def __to_square(self, face_box: np.ndarray):
        left, top, right, bottom, *_ = list(map(int, face_box))

        width = right - left
        height = bottom - top

        if width % 2 == 1:
            right = right + 1
            width = width + 1
        if height % 2 == 1:
            bottom = bottom + 1
            height = height + 1

        diff = int(abs(width - height) / 2)
        if width > height:
            top = top - diff
            bottom = bottom + diff
        else:
            left = left - diff
            right = right + diff

        return left, top, right, bottom

    def __ensure_margin(self, left: int, top: int, right: int, bottom: int, entire_image: np.ndarray, margin: float):
        entire_height, entire_width = entire_image.shape[:2]

        side_length = right - left
        margin = min(min(entire_height, entire_width) / side_length, margin)
        diff = int((side_length * margin - side_length) / 2)

        top = top - diff
        bottom = bottom + diff
        left = left - diff
        right = right + diff

        if top < 0:
            bottom = bottom - top
            top = 0
        if left < 0:
            right = right - left
            left = 0

        if bottom > entire_height:
            top = top - (bottom - entire_height)
            bottom = entire_height
        if right > entire_width:
            left = left - (right - entire_width)
            right = entire_width

        return left, top, right, bottom

class FaceCropper(scripts.Script):
    def __init__(self) -> None:
        super().__init__()

    def title(self):
        return face.CROPPER_NAME

    def show(self, is_img2img):
        return False

    def ui(self, is_img2img):
        enabled = gr.Checkbox(label="Enabled Face Detect", value=False)
        return [enabled]


class FaceRepairerExtension(scripts.Script):
    def __init__(self) -> None:
        super().__init__()
        self.__is_running = False

    def title(self):
        return face.NAME

    def show(self, is_img2img):
        return scripts.AlwaysVisible

    def ui(self, is_img2img):
        with gr.Accordion("Face Repairer", open=False, elem_id="sd-face-repairer-extension"):
            return [gr.Checkbox(label="Face Repairer Enabled", value=False)] + FaceRepairer().ui(is_img2img)

    def before_process_batch(self, p: StableDiffusionProcessing, **kwargs):
        unit = face.get_unit(p)
        if unit is None or unit.enabled is False:
            return

        if self.__is_running:
            return

        if not unit.keep_original:
            p.do_not_save_samples = True

    def postprocess(self, p: StableDiffusionProcessing, processed, *args):
        unit = face.get_unit(p)
        if unit is None or unit.enabled is False:
            return

        try:
            self.__is_running = True

            if o.scripts is not None:
                o.scripts.postprocess(o, processed)

            o.do_not_save_samples = False
            script = FaceRepairer()
            mask_model, detection_model = script.get_face_models()
            script.repair_images(mask_model, detection_model, processed, unit)
        finally:
            self.__is_running = False

class FaceRepairer(scripts.Script):
    """
    modify from https://github.com/ototadana/sd-face-editor.git
    """
    def __init__(self) -> None:
        super().__init__()

    def title(self):
        return "Face Repairer Script"

    def show(self, is_img2img):
        return scripts.AlwaysVisible

    def ui(self, is_img2img):
        keep_original = gr.Checkbox(label="Keep Original Image Before Face Repair", value=False)
        return [keep_original]

    def run(self, p: StableDiffusionProcessing, *args):
        unit = face.get_unit(p)
        if unit is None or unit.enabled is False:
            return

        mask_model, detection_model = self.get_face_models()

        if isinstance(p, StableDiffusionProcessingImg2Img) and p.n_iter == 1 and p.batch_size == 1:
            processed = self._repair_image(mask_model, detection_model, p, unit)
            if processed is not None:
                return processed
            return Processed(p, images_list=[None])

        shared.state.job_count = p.n_iter * 3

        if not unit.keep_original:
            p.do_not_save_samples = True

        processed = process_images(p)
        p.do_not_save_samples = False
        self.repair_images(mask_model, detection_model, p, processed, unit)
        return processed

    def get_face_models(self):
        if hasattr(retinaface, 'device'):
            retinaface.device = shared.device

        mask_model = init_parsing_model(device=shared.device)
        detection_model = init_detection_model("retinaface_resnet50", device=shared.device)
        return (mask_model, detection_model)

    @hRepair.time()
    def repair_images(self, mask_model: BiSeNet, detection_model: RetinaFace, p: StableDiffusionProcessing, processed: Processed, unit: face.FaceUnit):
        repaired_images = []
        seed_index = 0
        subseed_index = 0
        for i, image in enumerate(processed.images):
            lib.log(message=f"Repairing face for image {i + 1}/{len(processed.images)}, keep original: {unit.keep_original}")

            p1 = StableDiffusionProcessingImg2Img()
            p1.extra_generation_params["face-repairer-processing"] = True
            p1.__dict__.update(p.__dict__)
            p1.init_images = [image]
            p1.width, p1.height = image.size
            p1.do_not_save_samples = True
            if seed_index < len(processed.all_seeds):
                p1.seed = processed.all_seeds[seed_index]
                seed_index += 1
            if subseed_index < len(processed.all_subseeds):
                p1.subseed = processed.all_subseeds[subseed_index]
                subseed_index += 1
            
            repaired_result = self._repair_image(mask_model, detection_model, p1, unit)
            if repaired_result is None:
                repaired_images.append(image)
            else:
                repaired_images.extend(repaired_result.images)
        
        if unit.keep_original:
            processed.images.extend(repaired_images)
        else:
            processed.images = repaired_images

    def _repair_image(self, mask_model: BiSeNet, detection_model: RetinaFace, p: StableDiffusionProcessingImg2Img, unit: face.FaceUnit) -> Optional[Processed]:
        rgb_image = self.__to_rgb_image(p.init_images[0])

        faces = self.__crop_face(detection_model, rgb_image, unit.face_margin, unit.confidence)
        if len(faces) == 0:
            return None

        if shared.state.job_count == -1:
            shared.state.job_count = len(faces) * 2 + 1

        entire_image = np.array(rgb_image)
        entire_mask_image = np.zeros_like(entire_image)
        entire_width = (p.width // 8) * 8
        entire_height = (p.height // 8) * 8
        entire_prompt = p.prompt
        p.batch_size = 1
        p.n_iter = 1

        scripts = p.scripts        
        faces = faces[:unit.max_face_count]
        for face in faces:
            # todo 脸部交叠的问题
            # 挨个脸修复
            if shared.state.interrupted:
                break

            cRepair.inc()

             # 忽略其他脚本
            p.scripts = None
            p.init_images = [face.image]
            p.width = face.image.width
            p.height = face.image.height
            p.denoising_strength = unit.face_denoising_strength
            p.prompt = unit.prompt_for_face if len(unit.prompt_for_face) > 0 else entire_prompt
            p.do_not_save_samples = True

            processed = process_images(p)
            
            face_image = np.array(self.__to_rgb_image(processed.images[0]))
            mask_image = self.__to_mask_image(mask_model, face_image, unit.mask_size)
            face_image = cv2.resize(face_image, dsize=(face.width, face.height))
            mask_image = cv2.resize(mask_image, dsize=(face.width, face.height))

            entire_image[
                face.top: face.bottom,
                face.left: face.right,
            ] = face_image
            entire_mask_image[
                face.top: face.bottom,
                face.left: face.right,
            ] = mask_image

        # 合并重绘
        p.scripts = scripts
        p.prompt = entire_prompt
        p.width = entire_width
        p.height = entire_height
        p.init_images = [Image.fromarray(entire_image)]
        p.denoising_strength = unit.entire_denoising_strength
        p.mask_blur = unit.mask_blur
        p.inpainting_mask_invert = 1
        p.inpainting_fill = 1
        p.image_mask = Image.fromarray(entire_mask_image)
        p.do_not_save_samples = False

        final = process_images(p)
        # final.images = output_images
        return final

    def __to_rgb_image(self, img):
        return lib.to_rgb_image(img)

    def __to_masked_image(self, mask_image: np.ndarray, image: np.ndarray) -> np.ndarray:
        gray_mask = np.where(mask_image == 0, 47, 255) / 255.0
        return (image * gray_mask).astype('uint8')

    def __crop_face(self, detection_model: RetinaFace, image: Image, face_margin: float, confidence: float) -> list:
        with torch.no_grad():
            face_boxes, _ = detection_model.align_multi(image, confidence)
            return self.__crop(image, face_boxes, face_margin)

    def __crop(self, image: Image, face_boxes: list, face_margin: float) -> list:
        image = np.array(image, dtype=np.uint8)

        areas = []
        for face_box in face_boxes:
            areas.append(Face(image, face_box, face_margin))

        return sorted(areas, key=attrgetter("height"), reverse=True)

    def __to_mask_image(self, mask_model: BiSeNet, face_image: Image, mask_size: int) -> np.ndarray:
        face_image = np.array(face_image)
        face_tensor = img2tensor(face_image.astype("float32") / 255.0, float32=True)
        normalize(face_tensor, (0.5, 0.5, 0.5), (0.5, 0.5, 0.5), inplace=True)
        face_tensor = torch.unsqueeze(face_tensor, 0).to(shared.device)

        with torch.no_grad():
            face = mask_model(face_tensor)[0]
        face = face.squeeze(0).cpu().numpy().argmax(0)
        face = face.copy().astype(np.uint8)

        mask = self.__to_mask(face)
        if mask_size > 0:
            mask = cv2.dilate(mask, np.empty(0, np.uint8), iterations=mask_size)
        return mask

    def __to_mask(self, face: np.ndarray) -> np.ndarray:
        mask = np.zeros((face.shape[0], face.shape[1], 3), dtype=np.uint8)
        num_of_class = np.max(face)
        for i in range(1, num_of_class + 1):
            index = np.where(face == i)
            if i < 14:
                mask[index[0], index[1], :] = [255, 255, 255]
        return mask

lib.log("Face loaded")