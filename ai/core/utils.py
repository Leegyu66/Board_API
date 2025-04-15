import cv2
import torch
import numpy as np

def denormalize(image: torch.Tensor):
    min_max = (0, 1)
    image = image.squeeze(0).float().detach().cpu().clamp_(*min_max)
    image = (image - min_max[0]) / (min_max[1] - min_max[0])
    image = image.numpy().transpose(1, 2, 0)
    image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
    image = (image * 255.0).round()
    return image.astype(np.uint8)


def normalize(image: np.ndarray):
    img = image.astype(np.float32) / 255.0
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    img = torch.from_numpy(img.transpose(2, 0, 1))
    img = img.float()
    img = img.unsqueeze(0)
    img = img.to("cuda")

    return img


def to_y_channel(img):

    img = img.astype(np.float32) / 255.
    if img.ndim == 3 and img.shape[2] == 3:
        img = bgr2ycbcr(img)
        img = img[..., None]
    return img * 255.

def bgr2ycbcr(img):
    out_img = np.dot(img, [24.966, 128.553, 65.481]) + 16.0
    out_img = out_img / 255.
    return out_img


def _ssim_(img, img2):

    c1 = (0.01 * 255)**2
    c2 = (0.03 * 255)**2
    kernel = cv2.getGaussianKernel(11, 1.5)
    window = np.outer(kernel, kernel.transpose())

    mu1 = cv2.filter2D(img, -1, window)[5:-5, 5:-5]  # valid mode for window size 11
    mu2 = cv2.filter2D(img2, -1, window)[5:-5, 5:-5]
    mu1_sq = mu1**2
    mu2_sq = mu2**2
    mu1_mu2 = mu1 * mu2
    sigma1_sq = cv2.filter2D(img**2, -1, window)[5:-5, 5:-5] - mu1_sq
    sigma2_sq = cv2.filter2D(img2**2, -1, window)[5:-5, 5:-5] - mu2_sq
    sigma12 = cv2.filter2D(img * img2, -1, window)[5:-5, 5:-5] - mu1_mu2

    ssim_map = ((2 * mu1_mu2 + c1) * (2 * sigma12 + c2)) / ((mu1_sq + mu2_sq + c1) * (sigma1_sq + sigma2_sq + c2))
    return ssim_map.mean()

def calculate_ssim(img: np.ndarray, img2: np.ndarray, crop_border=4, input_order='HWC', test_y_channel=True):

    assert img.shape == img2.shape, (f'Image shapes are different: {img.shape}, {img2.shape}.')
    if input_order not in ['HWC', 'CHW']:
        raise ValueError(f'Wrong input_order {input_order}. Supported input_orders are "HWC" and "CHW"')

    if crop_border != 0:
        img = img[crop_border:-crop_border, crop_border:-crop_border, ...]
        img2 = img2[crop_border:-crop_border, crop_border:-crop_border, ...]

    if test_y_channel:
        img = to_y_channel(img)
        img2 = to_y_channel(img2)

    img = img.astype(np.float64)
    img2 = img2.astype(np.float64)

    ssims = []
    for i in range(img.shape[2]):
        ssims.append(_ssim_(img[..., i], img2[..., i]))
    return np.array(ssims).mean()

def calculate_psnr(img, img2, crop_border=4, input_order='HWC', test_y_channel=True):

    assert img.shape == img2.shape, (f'Image shapes are different: {img.shape}, {img2.shape}.')
    if input_order not in ['HWC', 'CHW']:
        raise ValueError(f'Wrong input_order {input_order}. Supported input_orders are "HWC" and "CHW"')

    if crop_border != 0:
        img = img[crop_border:-crop_border, crop_border:-crop_border, ...]
        img2 = img2[crop_border:-crop_border, crop_border:-crop_border, ...]

    if test_y_channel:
        img = to_y_channel(img)
        img2 = to_y_channel(img2)

    img = img.astype(np.float64)
    img2 = img2.astype(np.float64)

    mse = np.mean((img - img2)**2)
    if mse == 0:
        return float('inf')
    return 10. * np.log10(255. * 255. / mse)