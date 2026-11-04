import cv2
import mediapipe as mp
import random
import numpy as np
from streamlit_webrtc import VideoTransformerBase
import av

from src.utils import load_assets, overlay_transparent

class FruitNinjaProcessor(VideoTransformerBase):
    def __init__(self):
        # 1. Memuat aset secara aman di __init__
        self.assets = load_assets()
        
        # 2. OPTIMASI MEDIAPIPE: Pakai model_complexity=0 agar super ringan
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(
            max_num_hands=1, 
            model_complexity=0, # Model ringan untuk web
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )
        self.mp_draw = mp.solutions.drawing_utils
        
        # State Game
        self.score = 0
        self.lives = 3
        self.game_over = False
        self.game_objects = []
        self.cut_halves = []
        self.particles = []

    def spawn_object(self, width, height):
        obj_type = random.choices(['apple', 'watermelon', 'bomb'], weights=[40, 40, 20])[0]
        img_obj = self.assets[obj_type]
        fh, fw, _ = img_obj.shape
        x = random.randint(100 + fw // 2, width - 100 - fw // 2)
        return {
            'x': x, 'y': height, 
            'sy': random.randint(-22, -15), 'sx': random.randint(-4, 4), 
            'img': img_obj, 'type': obj_type, 'w': fw, 'h': fh
        }

    def recv(self, frame):
        try:
            img = frame.to_ndarray(format="bgr24")
            img = cv2.flip(img, 1)
            h, w, _ = img.shape
            
            imgRGB = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            results = self.hands.process(imgRGB)
            
            index_finger = None
            
            if results.multi_hand_landmarks:
                for handLms in results.multi_hand_landmarks:
                    self.mp_draw.draw_landmarks(img, handLms, self.mp_hands.HAND_CONNECTIONS)
                    lm = handLms.landmark[8] 
                    cx, cy = int(lm.x * w), int(lm.y * h)
                    index_finger = (cx, cy)
                    
                    cv2.circle(img, (cx, cy), 15, (255, 255, 255), cv2.FILLED)
                    cv2.circle(img, (cx, cy), 20, (0, 255, 255), 2) 

            if not self.game_over:
                if random.random() < 0.04: 
                    self.game_objects.append(self.spawn_object(w, h))
                    
                # 1. Update Objek Utama
                for obj in self.game_objects[:]:
                    obj['x'] += obj['sx']
                    obj['y'] += obj['sy']
                    obj['sy'] += 1
                    
                    pos_x = int(obj['x'] - obj['w'] / 2)
                    pos_y = int(obj['y'] - obj['h'] / 2)
                    
                    img = overlay_transparent(img, obj['img'], pos_x, pos_y)
                    
                    if index_finger:
                        if pos_x < index_finger[0] < pos_x + obj['w'] and \
                           pos_y < index_finger[1] < pos_y + obj['h']: 
                            
                            if obj['type'] == 'bomb':
                                self.score -= 50
                            else:
                                half_w = obj['w'] // 2
                                img_left = obj['img'][:, :half_w]
                                img_right = obj['img'][:, half_w:]
                                
                                self.cut_halves.append({'img': img_left, 'x': pos_x, 'y': pos_y, 'sx': -4, 'sy': -4})
                                self.cut_halves.append({'img': img_right, 'x': pos_x + half_w, 'y': pos_y, 'sx': 4, 'sy': -4})

                                p_color = (0, 0, 255) if obj['type'] == 'apple' else ((0,0,255) if random.random() > 0.2 else (0,200,0))
                                
                                # OPTIMASI: Kurangi partikel dari 15 ke 6 agar CPU ringan
                                for _ in range(6):
                                    self.particles.append({
                                        'x': index_finger[0], 'y': index_finger[1],
                                        'sx': random.uniform(-10, 10), 'sy': random.uniform(-10, 3),
                                        'r': random.randint(3, 6), 'c': p_color, 'life': random.randint(8, 15)
                                    })
                                self.score += 20 if obj['type'] == 'watermelon' else 10
                                
                            self.game_objects.remove(obj)
                            continue
                            
                    if obj['y'] > h + 50:
                        if obj['type'] in ['apple', 'watermelon']:
                            self.lives -= 1
                            if self.lives <= 0:
                                self.game_over = True
                        self.game_objects.remove(obj)

                # 2. Update Potongan Buah
                for cut in self.cut_halves[:]:
                    cut['x'] += cut['sx']
                    cut['y'] += cut['sy']
                    cut['sy'] += 1
                    img = overlay_transparent(img, cut['img'], int(cut['x']), int(cut['y']))
                    if cut['y'] > h + 50:
                        self.cut_halves.remove(cut)
                        
                # 3. Update Partikel
                for p in self.particles[:]:
                    p['x'] += p['sx']
                    p['y'] += p['sy']
                    p['sy'] += 1
                    p['life'] -= 1
                    if p['life'] > 0:
                        cv2.circle(img, (int(p['x']), int(p['y'])), p['r'], p['c'], cv2.FILLED)
                    else:
                        self.particles.remove(p)
            else:
                cv2.putText(img, "GAME OVER", (w // 2 - 150, h // 2), cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 0, 255), 5)

            # Render Teks Skor & Nyawa
            cv2.putText(img, f'SCORE: {self.score}', (30, 70), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 255, 0), 4)
            cv2.putText(img, f'LIVES: {self.lives}', (w - 250, 70), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 0, 255), 4)
            
            return av.VideoFrame.from_ndarray(img, format="bgr24")
        
        except Exception as e:
            # Jika ada error mendadak, kembalikan frame asli agar video tidak membeku
            print(f"Error in WebRTC recv: {e}")
            return frame