import cv2
import numpy as np
import asyncio
import logging
import aiohttp
import io
import base64
import binascii

from fastapi import APIRouter, Depends, HTTPException, Request, Header, status
from fastapi.responses import JSONResponse, StreamingResponse
from typing import List
from concurrent.futures import ProcessPoolExecutor

from app.inference.client import get_sr_service
from app.inference.sr_service import SuperResolutionService
from app.schemas.model import SuperResolutionInput


api_router = APIRouter()

logger = logging.getLogger(__name__)

@api_router.post("/super-resolution")
async def super_resolution(
    payload: SuperResolutionInput,
    sr_service: SuperResolutionService = Depends(get_sr_service)
) -> StreamingResponse:
    logger.info(f"Received upscale_json request for filename: {payload.filename}")

    # 1. 입력 모델에서 이미지 바이트 가져오기
    image_bytes = payload.image
    # image 필드가 Optional일 경우 None 체크 추가
    # if image_bytes is None:
    #     logger.warning("Request received with null image field.")
    #     raise HTTPException(
    #         status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
    #         detail="Image bytes are required in the request body.",
    #     )

    if not image_bytes:
        logger.warning("Request received with empty image bytes.")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Image bytes cannot be empty.",
        )
    
    try:
        # Pydantic 모델에서 image_base64 필드 접근
        image_bytes = base64.b64decode(image_bytes)
        # 빈 문자열 디코딩 시 빈 바이트가 될 수 있으므로 체크
        if not image_bytes:
            raise ValueError("Decoded image bytes are empty.")
        logger.info(f"Successfully decoded Base64 string to {len(image_bytes)} bytes.")
    except (binascii.Error, ValueError) as e: # binascii.Error는 잘못된 Base64 패딩 등을 잡음
        logger.error(f"Invalid Base64 data received: {e}")
        # 유효하지 않은 Base64 데이터는 클라이언트 오류 (422 Unprocessable Entity)
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid Base64 image data provided: {e}",
        )
    except Exception as e:
        logger.exception("Error during Base64 decoding.")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, # 다른 디코딩 관련 오류
            detail=f"Failed to decode Base64 data: {e}",
        )
    try:
        # 바이트 데이터를 NumPy 1D 배열로 변환
        image_np_1d = np.frombuffer(image_bytes, np.uint8)
        # 1D 배열을 이미지 형식(BGR 순서)으로 디코딩 (H, W, C 형태)
        # cv2.IMREAD_COLOR: BGR 3채널 이미지로 로드
        # cv2.IMREAD_UNCHANGED: 알파 채널 포함하여 로드 (예: PNG)
        img_decoded_np = cv2.imdecode(image_np_1d, cv2.IMREAD_COLOR)

        # 디코딩 실패 시 에러 처리 (imdecode는 실패 시 None 반환)
        if img_decoded_np is None:
            logger.error("Failed to decode image bytes. Input might not be a valid image format.")
            raise ValueError("Invalid image data provided. Could not decode.")

        logger.info(f"Successfully decoded image to NumPy array with shape: {img_decoded_np.shape}") # (H, W, 3)

    except ValueError as ve: # cv2.imdecode 실패 또는 다른 값 관련 오류 처리
         logger.error(f"ValueError during image decoding: {ve}")
         raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid image data: {ve}"
         )
    except Exception as e:
        logger.exception("Unexpected error during image decoding.")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, # 디코딩 실패는 클라이언트 요청 문제일 가능성 높음
            detail=f"Error decoding image: {e}",
        )

    # 2. Super Resolution 서비스 호출
    try:
        logger.info("Calling SuperResolutionService to upscale image...")
        upscaled_image_bytes = await sr_service.predict(img_decoded_np)
        logger.info("Successfully received upscaled image bytes from service.")
        if upscaled_image_bytes is None:
             raise ValueError("Upscaling service returned empty result.")

    except ValueError as ve:
         logger.error(f"Value error during upscaling: {ve}")
         raise HTTPException(
             status_code=status.HTTP_400_BAD_REQUEST,
             detail=f"Processing error: {ve}",
         )
    except Exception as e:
        logger.exception("Unexpected error during Super Resolution processing.")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upscale image due to an internal error: {e}",
        )

    # 3. 결과 반환 (StreamingResponse 사용)
    # 입력 파일의 content_type 정보가 없으므로, 출력 미디어 타입을 고정하거나
    # 다른 방법(예: filename 확장자 추론 - 비추천, 결과 바이트 분석)으로 결정해야 함.
    # 여기서는 PNG로 가정합니다.
    output_media_type = "image/png"
    logger.info(f"Returning upscaled image with assumed media type: {output_media_type}")
    cv2.imwrite("/app/debug_output/test.png", upscaled_image_bytes)
    return StreamingResponse(io.BytesIO(upscaled_image_bytes), media_type=output_media_type)
