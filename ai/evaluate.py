import argparse
import cv2
import numpy as np
import glob
import json
from core.utils import calculate_psnr, calculate_ssim

if __name__ == "__main__":
    gt_path = ['images/benchmark/B100/HR', 'images/benchmark/Manga109/HR', 'images/benchmark/Set5/HR', 
               'images/benchmark/Set14/HR', 'images/benchmark/Urban100/HR']
    sr_path = [f'results/B100', f'results/Manga109', f'results/Set5', 
               f'results/Set14', f'results/Urban100', f'results/Test']

    for gt, sr in zip(gt_path, sr_path):
        sr_image_paths = sorted(glob.glob(f"{sr}/*"))
        hr_image_paths = sorted(glob.glob(f"{gt}/*"))
        dataset_name = sr.split('/')[-1]
        print(f'evaluate {dataset_name} dataset!')

        results = {}
        psnr_list = []
        ssim_list = []

        for sr_image_path, hr_image_path in zip(sr_image_paths, hr_image_paths):
            file_name = sr_image_path.split('/')[-1]

            sr_image = cv2.imread(sr_image_path)
            hr_image = cv2.imread(hr_image_path)

            h, w, _ = sr_image.shape
            hr_image = hr_image[:h, :w, :]

            psnr_value = calculate_psnr(sr_image, hr_image, crop_border=4, test_y_channel=True)
            ssim_value = calculate_ssim(sr_image, hr_image, crop_border=4, test_y_channel=True)
            psnr_list.append(psnr_value)
            ssim_list.append(ssim_value)
            results[file_name] = {
                'psnr': np.round(psnr_value, decimals=2),
                'ssim': np.round(ssim_value, decimals=4)
            }
        print("psnr: ", np.mean(psnr_list))
        print('ssim: ', np.mean(ssim_list))