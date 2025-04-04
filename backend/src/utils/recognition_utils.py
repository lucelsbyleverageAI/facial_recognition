# built-in dependencies
import os
import pickle
from typing import List, Union, Optional, Dict, Any, Set
import time
import io
from typing import Generator, IO, List, Union, Tuple
import hashlib
import base64
from pathlib import Path

# 3rd party dependencies
import numpy as np
import pandas as pd
from tqdm import tqdm
import requests
import numpy as np
import cv2
from PIL import Image
from werkzeug.datastructures import FileStorage

# project dependencies
from deepface.commons import image_utils
from deepface.modules import representation, detection, verification
from deepface.commons.logger import Logger

IMAGE_EXTS = {".jpg", ".jpeg", ".png"}
PIL_EXTS = {"jpeg", "png"}





def list_images(path: str) -> List[str]:
    """
    List images in a given path
    Args:
        path (str): path's location
    Returns:
        images (list): list of exact image paths
    """
    images = []
    for r, _, f in os.walk(path):
        for file in f:
            if os.path.splitext(file)[1].lower() in IMAGE_EXTS:
                exact_path = os.path.join(r, file)
                with Image.open(exact_path) as img:  # lazy
                    if img.format.lower() in PIL_EXTS:
                        images.append(exact_path)
    return images


def yield_images(path: str) -> Generator[str, None, None]:
    """
    Yield images in a given path
    Args:
        path (str): path's location
    Yields:
        image (str): image path
    """
    for r, _, f in os.walk(path):
        for file in f:
            if os.path.splitext(file)[1].lower() in IMAGE_EXTS:
                exact_path = os.path.join(r, file)
                with Image.open(exact_path) as img:  # lazy
                    if img.format.lower() in PIL_EXTS:
                        yield exact_path


def find_image_hash(file_path: str) -> str:
    """
    Find the hash of given image file with its properties
        finding the hash of image content is costly operation
    Args:
        file_path (str): exact image path
    Returns:
        hash (str): digest with sha1 algorithm
    """
    file_stats = os.stat(file_path)

    # some properties
    file_size = file_stats.st_size
    creation_time = file_stats.st_ctime
    modification_time = file_stats.st_mtime

    properties = f"{file_size}-{creation_time}-{modification_time}"

    hasher = hashlib.sha1()
    hasher.update(properties.encode("utf-8"))
    return hasher.hexdigest()


def load_image(img: Union[str, np.ndarray, IO[bytes]]) -> Tuple[np.ndarray, str]:
    """
    Load image from path, url, file object, base64 or numpy array.
    Args:
        img: a path, url, file object, base64 or numpy array.
    Returns:
        image (numpy array): the loaded image in BGR format
        image name (str): image name itself
    """

    # The image is already a numpy array
    if isinstance(img, np.ndarray):
        return img, "numpy array"

    # The image is an object that supports `.read`
    if hasattr(img, 'read') and callable(img.read):
        if isinstance(img, io.StringIO):
            raise ValueError(
                'img requires bytes and cannot be an io.StringIO object.'
            )
        return load_image_from_io_object(img), 'io object'

    if isinstance(img, Path):
        img = str(img)

    if not isinstance(img, str):
        raise ValueError(f"img must be numpy array or str but it is {type(img)}")

    # The image is a base64 string
    if img.startswith("data:image/"):
        return load_image_from_base64(img), "base64 encoded string"

    # The image is a url
    if img.lower().startswith(("http://", "https://")):
        return load_image_from_web(url=img), img

    # The image is a path
    if not os.path.isfile(img):
        raise ValueError(f"Confirm that {img} exists")

    # image must be a file on the system then

    # image name must have english characters
    if not img.isascii():
        raise ValueError(f"Input image must not have non-english characters - {img}")

    img_obj_bgr = cv2.imread(img)
    # img_obj_rgb = cv2.cvtColor(img_obj_bgr, cv2.COLOR_BGR2RGB)
    return img_obj_bgr, img


def load_image_from_io_object(obj: IO[bytes]) -> np.ndarray:
    """
    Load image from an object that supports being read
    Args:
        obj: a file like object.
    Returns:
        img (np.ndarray): The decoded image as a numpy array (OpenCV format).
    """
    try:
        _ = obj.seek(0)
    except (AttributeError, TypeError, io.UnsupportedOperation):
        seekable = False
        obj = io.BytesIO(obj.read())
    else:
        seekable = True
    try:
        nparr = np.frombuffer(obj.read(), np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if img is None:
            raise ValueError("Failed to decode image")
        return img
    finally:
        if not seekable:
            obj.close()


def load_image_from_base64(uri: str) -> np.ndarray:
    """
    Load image from base64 string.
    Args:
        uri: a base64 string.
    Returns:
        numpy array: the loaded image.
    """

    encoded_data_parts = uri.split(",")

    if len(encoded_data_parts) < 2:
        raise ValueError("format error in base64 encoded string")

    encoded_data = encoded_data_parts[1]
    decoded_bytes = base64.b64decode(encoded_data)

    # similar to find functionality, we are just considering these extensions
    # content type is safer option than file extension
    with Image.open(io.BytesIO(decoded_bytes)) as img:
        file_type = img.format.lower()
        if file_type not in {"jpeg", "png"}:
            raise ValueError(f"Input image can be jpg or png, but it is {file_type}")

    nparr = np.frombuffer(decoded_bytes, np.uint8)
    img_bgr = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    # img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
    return img_bgr


def load_image_from_file_storage(file: FileStorage) -> np.ndarray:
    """
    Loads an image from a FileStorage object and decodes it into an OpenCV image.
    Args:
        file (FileStorage): The FileStorage object containing the image file.
    Returns:
        img (np.ndarray): The decoded image as a numpy array (OpenCV format).
    """
    file_bytes = np.frombuffer(file.read(), np.uint8)
    image = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
    if image is None:
        raise ValueError("Failed to decode image")
    return image


def load_image_from_web(url: str) -> np.ndarray:
    """
    Loading an image from web
    Args:
        url: link for the image
    Returns:
        img (np.ndarray): equivalent to pre-loaded image from opencv (BGR format)
    """
    response = requests.get(url, stream=True, timeout=60)
    response.raise_for_status()
    image_array = np.asarray(bytearray(response.raw.read()), dtype=np.uint8)
    img = cv2.imdecode(image_array, cv2.IMREAD_COLOR)
    return img





logger = Logger()

def find_bulk_embeddings(
    image_paths: Set[str],
    model_name: str = "VGG-Face",
    detector_backend: str = "opencv",
    enforce_detection: bool = True,
    align: bool = True,
    expand_percentage: int = 0,
    normalization: str = "base",
    silent: bool = False,
) -> List[Dict[str, Any]]:
    """
    Find embeddings for a list of face images.

    Args:
        image_paths: Set of paths to face images
        model_name: Face recognition model to use
        detector_backend: Face detector backend
        enforce_detection: Whether to enforce face detection
        align: Whether to align detected faces
        expand_percentage: Percentage to expand detected face area
        normalization: Normalization technique for face images
        silent: Whether to suppress progress bar

    Returns:
        List of dicts containing image metadata and embeddings
    """
    representations = []
    for image_path in tqdm(
        image_paths,
        desc="Generating face embeddings",
        disable=silent,
    ):
        file_hash = find_image_hash(image_path)

        try:
            img_objs = detection.extract_faces(
                img_path=image_path,
                detector_backend=detector_backend,
                grayscale=False,
                enforce_detection=enforce_detection,
                align=align,
                expand_percentage=expand_percentage,
            )

        except ValueError as err:
            logger.error(f"Failed to extract face from {image_path}: {str(err)}")
            img_objs = []

        if len(img_objs) == 0:
            representations.append({
                "identity": image_path,
                "hash": file_hash,
                "embedding": None,
                "target_x": 0,
                "target_y": 0,
                "target_w": 0,
                "target_h": 0,
            })
        else:
            for img_obj in img_objs:
                img_content = img_obj["face"]
                img_region = img_obj["facial_area"]
                embedding_obj = representation.represent(
                    img_path=img_content,
                    model_name=model_name,
                    enforce_detection=enforce_detection,
                    detector_backend="skip",
                    align=align,
                    normalization=normalization,
                )

                img_representation = embedding_obj[0]["embedding"]
                representations.append({
                    "identity": image_path,
                    "hash": file_hash,
                    "embedding": img_representation,
                    "target_x": img_region["x"],
                    "target_y": img_region["y"],
                    "target_w": img_region["w"],
                    "target_h": img_region["h"],
                })

    return representations