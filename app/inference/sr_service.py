import cv2
import torch

import numpy as np
import tritonclient.grpc.aio as grpcclient

class SuperResolutionService:
    def __init__(self, triton_url: str):

        self.model_name = "SeemoRe_T"
        self.triton_client = grpcclient.InferenceServerClient(url=triton_url)

    async def close(self):
        if self.triton_client:
            try:
                await self.triton_client.close()
            except Exception as e:
                pass
    
    
    def preprocess(self, image: np.ndarray) -> np.ndarray:
        image = image.astype(np.float32) / 255.0
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        # image: torch.Tensor = torch.from_numpy(image.transpose(2, 0, 1))[None]
        image = image.transpose(2, 0, 1)
        image = np.expand_dims(image, axis=0)
        
        return image
    
    def postprocess(self, image: np.ndarray) -> np.ndarray:
        image = image[0].clip(0.0, 1.0)
        image = image.transpose(1, 2, 0)
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        image = (image * 255.0).round()
        return image.astype(np.uint8)
    

    async def predict(self, image):
        image = self.preprocess(image)
        B, C, H, W = image.shape
        in0 = grpcclient.InferInput("INPUT__0", [B, C, H, W], "FP32")

        in0.set_data_from_numpy(image)

        out0 = grpcclient.InferRequestedOutput("OUTPUT__0")
        response = await self.triton_client.infer(
            model_name=self.model_name,
            inputs=[in0],
            outputs=[out0]
        )

        output_data = response.as_numpy("OUTPUT__0")

        if output_data is None:
            raise ValueError("No output returned from Triton server.")

        result = self.postprocess(output_data)
        return result