import cv2
import numpy as np
import logging
import base64
import os.path as osp
import asyncio

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse

from app.inference.client import get_sr_service
from app.inference.sr_service import SuperResolutionService
from app.schemas.model import SuperResolutionInput, SuperResolutionOutput
from app.exceptions.custom_exception import ServerError


api_router = APIRouter()

logger = logging.getLogger(__name__)
loop = asyncio.get_running_loop()

@api_router.post("/super-resolution")
async def super_resolution(
    payload: SuperResolutionInput,
    sr_service: SuperResolutionService = Depends(get_sr_service)
) -> JSONResponse:

    image_bytes = payload.image
    filename = payload.filename

    try:
        _, ext = osp.splitext(filename)
    except:
        raise ServerError("Invalid file format")

    try:
        image_bytes = await loop.run_in_executor(
            None,
            base64.b64decode,
            image_bytes
        )
        if not image_bytes:
            raise ServerError("Decoded image bytes are empty")
        
    except:
        raise ServerError("Unexpected Error")
    
    try:
        image_np = await loop.run_in_executor(
            None,
            np.frombuffer,
            image_bytes, 
            np.uint8
        )

        img_decoded = await loop.run_in_executor(
            None,
            cv2.imdecode,
            image_np,
            cv2.IMREAD_COLOR
        )
        if img_decoded is None:
            raise ServerError("Invalid image data provided")

    except:
        raise ServerError("Unexpected Error")


    try:
        upscaled_image_bytes = await sr_service.predict(img_decoded)
        if upscaled_image_bytes is None:
            raise ServerError("Upscaling service returned empty result")
    except:
        raise ServerError("Unexpected Error")

    is_success, buffer = await loop.run_in_executor(
        None,
        cv2.imencode,
        ext, 
        upscaled_image_bytes
    )

    image_bytes = buffer.tobytes()
    base64_bytes = await loop.run_in_executor(
        None,
        base64.b64encode,
        image_bytes
    )
    
    base64_string = base64_bytes.decode('utf-8')

    return SuperResolutionOutput(filename=filename, image=base64_string)
