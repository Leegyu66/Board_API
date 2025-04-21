from pydantic import BaseModel
from typing import Optional, List, Union

class SuperResolutionInput(BaseModel):
    filename: str
    image: Optional[str]