import os
import cv2
import glob
import time
import torch
import argparse

import numpy as np
import torch.nn.functional as F

from core.SeemoRe import SeemoRe_T
from core.utils import normalize, denormalize

model = SeemoRe_T()


datasets = [
    "./images/benchmark/Set5/LR",
    "./images/benchmark/Set14/LR",
    "./images/benchmark/B100/LR",
    "./images/benchmark/Urban100/LR",
    "./images/benchmark/Manga109/LR",
]

parser = argparse.ArgumentParser(description="choice model")

model = SeemoRe_T()
model.load_state_dict(torch.load("./weights/SeemoRe_T.pth")['params'], strict=True)
model.cuda()

for dataset in datasets:
    dataset_name = dataset.split("/")[-2]

    print(f"start infer {dataset_name}")
    os.makedirs(os.path.join(f"./results/{dataset_name}"), exist_ok=True)
    data_file = glob.glob(os.path.join(dataset, "*.png"))

    start_time = time.time()
    for file_name in data_file:
        lr_image = cv2.imread(file_name)

        lr_image = normalize(lr_image)
        with torch.no_grad():
            sr_image = denormalize(model(lr_image))

        file, ext = os.path.splitext(file_name)
        file = file.split("/")[-1] + ".png"
        # cv2.imwrite(f'./results/{dataset_name}/{file}', sr_image)
        cv2.imwrite(f"./results/{dataset_name}/{file}", sr_image)
    finish_time = time.time()

    print(f'total time: {finish_time - start_time}')