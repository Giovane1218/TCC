from pathlib import Path
import cv2
import numpy as np
from skimage import exposure
from skimage.filters import unsharp_mask

imagems_dir = Path(__file__).resolve().parent.parent / "imagens"

def processar_imagem(conteudo: bytes, target_size: int = 224) -> np.ndarray:
    """Orquestra a leitura em bytes, o ajuste de proporção (prep_xray) 

    e o tratamento de contraste (convert_image_array).
    """
    try:
        # 1. Decodifica os bytes para array OpenCV (Grayscale)
        np_array = np.frombuffer(conteudo, np.uint8)
        imagem = cv2.imdecode(np_array, cv2.IMREAD_GRAYSCALE)

        if imagem is None:
            raise ValueError("Imagem inválida ou corrompida")

        # 2. Mantém o aspect ratio e faz padding quadrado (prep_xray)
        imagem_padded = prep_xray(imagem, target_size=target_size)

        # 3. Aplica realce de contraste e histograma (convert_image_array)
        imagem_processada = convert_image_array(
            imagem_padded,
            convert_grayscale=False,
            equalize=True,
            intensity_crop=0.05,
            sharpen=False,
            outputbitdepth=8
        )

        imagem_final = imagem_processada.astype(np.float32) / 255.0
        imagem_final = np.expand_dims(imagem_final, axis=(0, -1)) 
       

        return imagem_final

    except Exception as e:
        raise ValueError(f"Erro ao processar a imagem: {e}")
def convert_image_array(
    img: np.ndarray,
    convert_grayscale: bool = False,
    equalize: bool = True,
    intensity_crop: float = 0.05,
    sharpen: bool = False,
    outputbitdepth: int = 8
) -> np.ndarray:
    """
    Processes and converts an image array according to specified parameters.
    
    Parameters:
        img (np.ndarray): Input image array (uint8 or uint16).
        convert_grayscale (bool): Convert array to 1-channel grayscale if True.
        equalize (bool): Apply intensity rescaling and adaptive histogram equalization (CLAHE).
        intensity_crop (float): Percentile threshold for rescale_intensity prior to equalization.
        sharpen (bool): Apply unsharp masking.
        outputbitdepth (int): Output bit depth (8 or 16).
        
    Returns:
        np.ndarray: Converted image array.
    """
    # 1. Convert to grayscale if requested
    if convert_grayscale and len(img.shape) == 3:
        img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # 2. Normalize input bit depth to float64 in range [0, 1]
    if img.dtype == np.uint16:
        img_float = (img / 65535.0).astype(np.float64)
    elif img.dtype == np.uint8:
        img_float = (img / 255.0).astype(np.float64)
    else:
        raise ValueError(f"Unsupported input array dtype: {img.dtype}")

    # 3. CLAHE Contrast Enhancement
    if equalize:
        p_low = np.percentile(img_float, intensity_crop)
        p_high = np.percentile(img_float, 100 - intensity_crop)
        img_float = exposure.rescale_intensity(img_float, in_range=(p_low, p_high))
        img_float = exposure.equalize_adapthist(img_float)

    # 4. Sharpening
    if sharpen:
        img_float = unsharp_mask(img_float, radius=1, amount=1)

    # 5. Rescale to target output bit depth
    if outputbitdepth == 8:
        target_dtype = np.uint8
    elif outputbitdepth == 16:
        target_dtype = np.uint16
    else:
        raise ValueError(f"Unsupported output bit depth: {outputbitdepth}")

    max_val = int((2 ** outputbitdepth) - 1)
    converted_img = cv2.normalize(
        img_float, dst=None, alpha=0, beta=max_val, norm_type=cv2.NORM_MINMAX
    ).astype(target_dtype)

    return converted_img


def prep_xray(img: np.ndarray, target_size: int = 512) -> np.ndarray:
    """Redimensiona a imagem mantendo o aspect ratio e adiciona bordas pretas para torná-la quadrada."""
    old_size = img.shape[:2] 
    ratio = float(target_size) / max(old_size)
    new_size = tuple([int(x * ratio) for x in old_size])
    
    img_resized = cv2.resize(img, (new_size[1], new_size[0]), interpolation=cv2.INTER_AREA)
    
    delta_w = target_size - new_size[1]
    delta_h = target_size - new_size[0]
    top, bottom = delta_h // 2, delta_h - (delta_h // 2)
    left, right = delta_w // 2, delta_w - (delta_w // 2)
    
    color = [0, 0, 0] if len(img.shape) == 3 else 0
    final_xray = cv2.copyMakeBorder(
        img_resized, top, bottom, left, right, 
        cv2.BORDER_CONSTANT, value=color
    )
    
    return final_xray