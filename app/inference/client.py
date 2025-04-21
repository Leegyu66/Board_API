from app.inference.sr_service import SuperResolutionService
from app.core.config import settings


# class SuperResolutionService():
#     def __init__(self, triton_url: str):
#         pass

async def get_sr_service():
    return SuperResolutionService(settings.TRITON_SERVER_URL)