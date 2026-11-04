import cv2
import streamlit as st

@st.cache_resource
def load_assets():
    """Memuat dan mengkonfigurasi aset gambar dengan caching Streamlit."""
    apple = cv2.resize(cv2.imread('assets/apple.png', cv2.IMREAD_UNCHANGED), (80, 80))
    watermelon = cv2.resize(cv2.imread('assets/watermelon.png', cv2.IMREAD_UNCHANGED), (120, 120))
    bomb = cv2.resize(cv2.imread('assets/bomb.png', cv2.IMREAD_UNCHANGED), (100, 100))
    return {'apple': apple, 'watermelon': watermelon, 'bomb': bomb}

def overlay_transparent(bg_img, img_to_overlay, x, y):
    """Menempelkan gambar PNG dengan transparansi channel Alpha ke atas gambar latar."""
    bg_img_copy = bg_img.copy()
    h, w, _ = img_to_overlay.shape
    
    if y < 0 or y + h > bg_img.shape[0] or x < 0 or x + w > bg_img.shape[1]:
        return bg_img_copy

    roi = bg_img_copy[y:y+h, x:x+w]
    b, g, r, a = cv2.split(img_to_overlay)
    
    mask = cv2.merge((a, a, a))
    mask_inv = cv2.bitwise_not(mask)
    
    bg_part = cv2.bitwise_and(roi, roi, mask=mask_inv[:,:,0])
    fg_part = cv2.merge((b, g, r))
    fg_part = cv2.bitwise_and(fg_part, fg_part, mask=mask[:,:,0])
    
    dst = cv2.add(bg_part, fg_part)
    bg_img_copy[y:y+h, x:x+w] = dst
    return bg_img_copy