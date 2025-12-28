#!/usr/bin/env python3
"""
Image Manipulation Functions voor Beamer Projection
Losse functies voor crop, zoom, en perspective warp
"""

import cv2
import numpy as np
from pathlib import Path
from typing import Optional, Tuple, List
from numpy.typing import NDArray

# Type aliases voor leesbaarheid
ImageArray = NDArray[np.uint8]  # (H, W, 3) RGB image
Point = List[float]  # [x, y] coordinaat
Corners = List[Point]  # 4 punten: [top-left, top-right, bottom-right, bottom-left]


def load_image(path: Path | str) -> Optional[ImageArray]:
    """
    Laad een foto van disk
    
    Args:
        path: Path naar de foto
        
    Returns:
        numpy array (H, W, 3) in RGB, of None als fout
    """
    img = cv2.imread(str(path))
    if img is None:
        return None
    # OpenCV laadt in BGR, converteer naar RGB
    return cv2.cvtColor(img, cv2.COLOR_BGR2RGB)


def crop_image(
    img: ImageArray, 
    center_x: float, 
    center_y: float, 
    width: int, 
    height: int
) -> ImageArray:
    """
    Crop een rechthoekig stuk uit de foto
    
    Args:
        img: numpy array (H, W, 3)
        center_x: X coordinaat van center (in pixels van originele foto)
        center_y: Y coordinaat van center
        width: Breedte van crop window
        height: Hoogte van crop window
        
    Returns:
        Cropped image (height, width, 3)
        
    Voorbeeld:
        # Neem center 500x500 pixels uit het midden
        cropped = crop_image(img, img.shape[1]//2, img.shape[0]//2, 500, 500)
    """
    img_h, img_w = img.shape[:2]
    
    # Bereken crop bounds
    x1 = int(center_x - width // 2)
    y1 = int(center_y - height // 2)
    x2 = int(x1 + width)
    y2 = int(y1 + height)
    
    # Clamp binnen image bounds
    x1 = max(0, min(img_w, x1))
    y1 = max(0, min(img_h, y1))
    x2 = max(0, min(img_w, x2))
    y2 = max(0, min(img_h, y2))
    
    return img[y1:y2, x1:x2]


def zoom_crop(
    img: ImageArray, 
    zoom_factor: float, 
    offset_x: float = 0, 
    offset_y: float = 0
) -> ImageArray:
    """
    Zoom IN op de foto door te croppen
    Hogere zoom = kleinere crop = meer ingezoomd
    
    Args:
        img: numpy array (H, W, 3)
        zoom_factor: 1.0 = no zoom, 2.0 = 2x zoom in, 0.5 = zoom out (maar crop kan niet groter dan img)
        offset_x: Hoeveel pixels het crop center verschuiven (positief = rechts)
        offset_y: Hoeveel pixels het crop center verschuiven (positief = naar beneden)
        
    Returns:
        Cropped image
        
    Voorbeeld:
        # Zoom 2x in, verschuif 100px naar rechts
        zoomed = zoom_crop(img, 2.0, offset_x=100, offset_y=0)
    """
    img_h, img_w = img.shape[:2]
    
    # Bereken de crop window size (kleiner bij hogere zoom)
    crop_w = int(img_w / zoom_factor)
    crop_h = int(img_h / zoom_factor)
    
    # Center point met offset
    center_x = img_w // 2 + offset_x
    center_y = img_h // 2 + offset_y
    
    # Crop
    return crop_image(img, center_x, center_y, crop_w, crop_h)


def fit_image_to_aspect_ratio(
    img: ImageArray,
    target_aspect_ratio: float
) -> ImageArray:
    """
    Voeg padding toe aan image zodat het de target aspect ratio krijgt
    zonder de originele foto te vervormen (letterboxing/pillarboxing)
    
    Args:
        img: numpy array (H, W, 3)
        target_aspect_ratio: width/height van de target shape
        
    Returns:
        Image met padding, in target aspect ratio
        
    Voorbeeld:
        # Maak foto 16:9 zonder vervorming
        fitted = fit_image_to_aspect_ratio(img, 16/9)
    """
    img_h, img_w = img.shape[:2]
    img_ratio = img_w / img_h
    
    if abs(img_ratio - target_aspect_ratio) < 0.001:
        # Al de juiste ratio
        return img
    
    if img_ratio > target_aspect_ratio:
        # Image is te breed - voeg top/bottom padding toe
        new_height = int(img_w / target_aspect_ratio)
        pad_total = new_height - img_h
        pad_top = pad_total // 2
        pad_bottom = pad_total - pad_top
        
        padded = cv2.copyMakeBorder(
            img,
            pad_top, pad_bottom, 0, 0,
            cv2.BORDER_CONSTANT,
            value=(0, 0, 0)
        )
    else:
        # Image is te hoog - voeg left/right padding toe
        new_width = int(img_h * target_aspect_ratio)
        pad_total = new_width - img_w
        pad_left = pad_total // 2
        pad_right = pad_total - pad_left
        
        padded = cv2.copyMakeBorder(
            img,
            0, 0, pad_left, pad_right,
            cv2.BORDER_CONSTANT,
            value=(0, 0, 0)
        )
    
    return padded


def calculate_quad_aspect_ratio(corners: Corners) -> float:
    """
    Bereken de gemiddelde aspect ratio van je 4-hoek
    
    Args:
        corners: 4 hoekpunten [top-left, top-right, bottom-right, bottom-left]
        
    Returns:
        width/height ratio van de quad
    """
    # Bereken gemiddelde breedte (top + bottom) / 2
    top_width = abs(corners[1][0] - corners[0][0])
    bottom_width = abs(corners[2][0] - corners[3][0])
    avg_width = (top_width + bottom_width) / 2
    
    # Bereken gemiddelde hoogte (left + right) / 2
    left_height = abs(corners[3][1] - corners[0][1])
    right_height = abs(corners[2][1] - corners[1][1])
    avg_height = (left_height + right_height) / 2
    
    return avg_width / avg_height if avg_height > 0 else 1.0

def cover_image_to_aspect_ratio(
    img: ImageArray,
    target_aspect_ratio: float
) -> ImageArray:
    """
    Crop de foto zodat het de target aspect ratio krijgt
    zonder zwarte balken (zoals CSS object-fit: cover)
    
    Je VERLIEST wel een deel van de foto aan de randen!
    """
    img_h, img_w = img.shape[:2]
    img_ratio = img_w / img_h
    
    if abs(img_ratio - target_aspect_ratio) < 0.001:
        return img
    
    if img_ratio > target_aspect_ratio:
        # Image is te breed - crop links/rechts
        new_width = int(img_h * target_aspect_ratio)
        crop_x = (img_w - new_width) // 2
        return img[:, crop_x:crop_x + new_width]
    else:
        # Image is te hoog - crop top/bottom  
        new_height = int(img_w / target_aspect_ratio)
        crop_y = (img_h - new_height) // 2
        return img[crop_y:crop_y + new_height, :]

def perspective_warp(
    img: ImageArray, 
    corners: Corners, 
    output_size: Tuple[int, int],
    preserve_aspect_ratio: bool = True
) -> ImageArray:
    """
    Past perspective transformation toe (dit is de KERNFUNCTIE!)
    Neemt je cropped/zoomed foto en "buigt" hem in je 4 hoekpunten
    
    Args:
        img: numpy array (H, W, 3) - de cropped/zoomed foto
        corners: List van 4 [x,y] punten - de hoeken op je beamer/canvas waar de foto naartoe moet
                 Volgorde: [top-left, top-right, bottom-right, bottom-left]
        output_size: (width, height) van output canvas (bv beamer resolution)
        preserve_aspect_ratio: Als True, voeg padding toe zodat foto niet vervormd wordt
        
    Returns:
        numpy array met transformed image in canvas van output_size
        
    Voorbeeld:
        corners = [[100, 100], [800, 150], [750, 600], [150, 580]]
        warped = perspective_warp(img, corners, (1920, 1080))
    """
    # Als we aspect ratio willen behouden, fit image eerst
    if preserve_aspect_ratio:
        target_ratio = calculate_quad_aspect_ratio(corners)
        # img = fit_image_to_aspect_ratio(img, target_ratio)
        img = cover_image_to_aspect_ratio(img, target_ratio)
    
    img_h, img_w = img.shape[:2]
    
    # Source points: de 4 hoeken van je rechthoekige input foto
    src_points = np.float32([
        [0, 0],           # top-left
        [img_w, 0],       # top-right
        [img_w, img_h],   # bottom-right
        [0, img_h]        # bottom-left
    ])
    
    # Destination points: waar die hoeken naartoe moeten op de canvas
    dst_points = np.float32(corners)
    
    # Bereken de perspective transformation matrix
    # Dit is de wiskundige "recept" om elk pixel te verplaatsen
    matrix = cv2.getPerspectiveTransform(src_points, dst_points)
    
    # Pas de warp toe
    # INTER_LINEAR = bilinear interpolatie (goeie kwaliteit, snel)
    # Andere opties: INTER_CUBIC (beter kwaliteit, trager), INTER_NEAREST (snel, blocky)
    warped = cv2.warpPerspective(
        img, 
        matrix, 
        output_size,
        flags=cv2.INTER_LINEAR,
        borderMode=cv2.BORDER_CONSTANT,
        borderValue=(255, 255, 255)  # Zwarte achtergrond buiten de foto
    )
    
    return warped


def full_pipeline(
    img_path: Path | str, 
    corners: Corners, 
    beamer_size: Tuple[int, int], 
    zoom: float = 1.0, 
    offset_x: float = 0, 
    offset_y: float = 0
) -> Optional[ImageArray]:
    """
    Complete pipeline: load → zoom/crop → perspective warp
    Dit is wat je elke frame zou callen als je real-time wilt renderen
    
    Args:
        img_path: Path naar originele foto
        corners: 4 hoekpunten [[x,y], [x,y], [x,y], [x,y]]
        beamer_size: (width, height) tuple van je beamer
        zoom: zoom factor (1.0 = normaal, 2.0 = 2x inzoomen)
        offset_x: pan horizontaal (in pixels van originele foto)
        offset_y: pan verticaal
        
    Returns:
        Final warped image ready to display, of None bij errors
    """
    # 1. Laad originele foto
    img = load_image(img_path)
    if img is None:
        return None
    
    # 2. Crop/zoom based on user input
    cropped = zoom_crop(img, zoom, offset_x, offset_y)
    
    # 3. Perspective warp naar de 4 hoeken
    warped = perspective_warp(cropped, corners, beamer_size)
    
    return warped


def save_image(img: ImageArray, path: Path | str) -> None:
    """
    Sla een image op naar disk
    
    Args:
        img: numpy array in RGB
        path: output path
    """
    # Convert RGB terug naar BGR voor OpenCV
    img_bgr = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
    cv2.imwrite(str(path), img_bgr, [cv2.IMWRITE_JPEG_QUALITY, 95])


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_crop_dimensions(img_shape: Tuple[int, ...], zoom: float) -> Tuple[int, int]:
    """
    Bereken de crop dimensions voor een gegeven zoom level
    
    Args:
        img_shape: Shape van de image (H, W, ...) 
        zoom: Zoom factor
    
    Returns:
        (crop_width, crop_height)
    """
    img_h, img_w = img_shape[:2]
    return (int(img_w / zoom), int(img_h / zoom))


def validate_corners(corners: Corners, canvas_size: Tuple[int, int]) -> bool:
    """
    Check of hoekpunten binnen canvas vallen
    
    Args:
        corners: 4 hoekpunten
        canvas_size: (width, height) van canvas
    
    Returns:
        True als valid
    """
    w, h = canvas_size
    for corner in corners:
        if corner[0] < 0 or corner[0] > w or corner[1] < 0 or corner[1] > h:
            return False
    return True


# ============================================================================
# EXAMPLE USAGE
# ============================================================================

if __name__ == '__main__':
    """
    Voorbeeld hoe je dit zou gebruiken
    """
    
    # Config
    IMAGE_PATH = Path("uploads/current_beamer_image.jpg")
    BEAMER_SIZE: Tuple[int, int] = (1920, 1080)
    
    # Je controller state (zou je bijhouden in je main loop)
    corners: Corners = [
        [200, 150],      # top-left
        [1700, 200],     # top-right  
        [1650, 900],     # bottom-right
        [250, 850]       # bottom-left
    ]
    zoom: float = 1.5
    pan_x: float = 0
    pan_y: float = 0
    
    # Real-time rendering - doe dit elke frame in je game loop
    print("Rendering frame...")
    result = full_pipeline(IMAGE_PATH, corners, BEAMER_SIZE, zoom, pan_x, pan_y)
    
    if result is not None:
        print(f"✅ Rendered: {result.shape}")
        # Nu zou je dit displayen met pygame of cv2.imshow
        # cv2.imshow('Beamer', cv2.cvtColor(result, cv2.COLOR_RGB2BGR))
        # cv2.waitKey(0)
        
        # Optioneel: sla finaal resultaat op
        save_image(result, "output_warped.jpg")
        print("✅ Saved to output_warped.jpg")