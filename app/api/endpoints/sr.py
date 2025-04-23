import cv2
import numpy as np
import logging
import base64

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse

from app.inference.client import get_sr_service
from app.inference.sr_service import SuperResolutionService
from app.schemas.model import SuperResolutionInput, SuperResolutionOutput
from app.exceptions.custom_exception import ServerError


api_router = APIRouter()

logger = logging.getLogger(__name__)

@api_router.post("/super-resolution")
async def super_resolution(
    payload: SuperResolutionInput,
    sr_service: SuperResolutionService = Depends(get_sr_service)
) -> JSONResponse:

    image_bytes = payload.image
    filename = payload.filename

    if not image_bytes:
        raise ServerError("received with empty image bytes")
    
    try:
        image_bytes = base64.b64decode(image_bytes)
        if not image_bytes:
            raise ServerError("Decoded image bytes are empty.")
        
    except:
        raise ServerError("Unexpected Error")
    
    try:
        image_np_1d = np.frombuffer(image_bytes, np.uint8)
        img_decoded_np = cv2.imdecode(image_np_1d, cv2.IMREAD_COLOR)

        if img_decoded_np is None:
            raise ServerError("Invalid image data provided. Could not decode.")

    except:
        raise ServerError("Unexpected Error")


    try:
        upscaled_image_bytes = await sr_service.predict(img_decoded_np)
        if upscaled_image_bytes is None:
            raise ServerError("Upscaling service returned empty result")
    except:
        raise ServerError("Unexpected Error")

    cv2.imwrite("/app/debug_output/test.png", upscaled_image_bytes)

    image_format_extension = ".png"
    is_success, buffer = cv2.imencode(image_format_extension, upscaled_image_bytes)

    image_bytes = buffer.tobytes()
    base64_bytes = base64.b64encode(image_bytes)
    base64_string = base64_bytes.decode('utf-8')

    return SuperResolutionOutput(filename=filename, image=base64_string)
