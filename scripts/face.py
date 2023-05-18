import cv2
import modules.scripts as scripts
import modules.shared as shared
import numpy as np
import torch

from facexlib.detection import RetinaFace, init_detection_model, retinaface
from facexlib.parsing import BiSeNet, init_parsing_model
from facexlib.utils.misc import img2tensor
from PIL import Image
from torchvision.transforms.functional import normalize

from modules.processing import Processed, StableDiffusionProcessing, StableDiffusionProcessingImg2Img, process_images

from character import face
from character.lib import log
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

class FaceRepairer(scripts.Script):
    """
    modify from https://github.com/ototadana/sd-face-editor.git
    """
    def __init__(self) -> None:
        super().__init__()

    def title(self):
        return face.NAME

    def show(self, is_img2img):
        return scripts.AlwaysVisible
 
    def run(self, p, *args):
        units = face.get_units(p)
        if units is None or len(units) == 0:
            return process_images(p)

        # p.do_not_save_samples = True
        shared.state.job_count = p.n_iter * 3

        # 原始过程
        result = process_images(p)

        # 获取模型
        mask_model, detection_model = self.get_face_models()
        
        # 修复过程
        return self._repair_images(mask_model, detection_model, p, result, units[0])

    def get_face_models(self):
        if hasattr(retinaface, 'device'):
            retinaface.device = shared.device

        mask_model = init_parsing_model(device=shared.device)
        detection_model = init_detection_model("retinaface_resnet50", device=shared.device)
        return (mask_model, detection_model)

    @hRepair.time()
    def _repair_images(self, mask_model: BiSeNet, detection_model: RetinaFace, p: StableDiffusionProcessing, result: Processed, unit: face.FaceUnit):
        repaired_images = []
        seed_index = 0
        subseed_index = 0
        for i, image in enumerate(result.images):
            if i < result.index_of_first_image:
                continue

            # 每张图片使用i2i进行修复
            p1 = StableDiffusionProcessingImg2Img()
            p1.__dict__.update(p.__dict__)
            p1.init_images = [image]
            p1.width, p1.height = image.size
            if seed_index < len(result.all_seeds):
                p1.seed = result.all_seeds[seed_index]
                seed_index += 1
            if subseed_index < len(result.all_subseeds):
                p1.subseed = result.all_subseeds[subseed_index]
                subseed_index += 1
            
            repaired_result = self._repair_image(mask_model, detection_model, p1, image, unit)
            repaired_images.extend(repaired_result.images)
        
        result.images = repaired_images
        # result.images.extend(repaired_images)
        return result

    def _format_init_images(self, p: StableDiffusionProcessingImg2Img):
        if not hasattr(p.init_images[0], 'mode') or p.init_images[0].mode != 'RGB':
            p.init_images[0] = p.init_images[0].convert('RGB')

    def _repair_image(self, mask_model: BiSeNet, detection_model: RetinaFace, p: StableDiffusionProcessingImg2Img, pre_image: Image, unit: face.FaceUnit) -> Processed:
        self._format_init_images(p)

        faces = self.__crop_face(detection_model, p.init_images[0], face_margin, confidence)
        log(f"number of faces: {len(faces)}")

        # 没有脸则不处理
        if len(faces) == 0 and pre_image is not None:
            return Processed(p, images_list=[pre_image])

        if shared.state.job_count == -1:
            shared.state.job_count = len(faces) * 2 + 1

        entire_image = np.array(p.init_images[0])
        entire_mask_image = np.zeros_like(entire_image)
        entire_width = (p.width // 8) * 8
        entire_height = (p.height // 8) * 8
        entire_prompt = p.prompt
        p.batch_size = 1
        p.n_iter = 1
        scripts = p.scripts

        output_images = []
        faces = faces[:unit.max_face_count]
        for face in faces:
            # todo 脸部交叠的问题
            # 挨个脸修复
            if shared.state.interrupted:
                break

            cRepair.inc()

            p.init_images = [face.image]
            p.width = face.image.width
            p.height = face.image.height
            p.denoising_strength = unit.face_denoising_strength
            p.prompt = unit.prompt_for_face if len(unit.prompt_for_face) > 0 else entire_prompt
            p.do_not_save_samples = True

            proc = process_images(p)

            self._format_init_images(p)
            face_image = np.array(proc.images[0])
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
        return process_images(p)

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

log("Face loaded")