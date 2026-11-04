import streamlit as st

st.set_page_config(page_title="Air Fruit Ninja", layout="wide")

from streamlit_webrtc import webrtc_streamer, RTCConfiguration, WebRtcMode
from src.game_processor import FruitNinjaProcessor

st.title("🍉 Air Fruit Ninja (Hand Tracking)")
st.write("Nyalakan kamera dan gunakan telunjukmu untuk memotong buah! Hindari bom.")

# --- SIDEBAR PANDUAN ---
st.sidebar.title("📖 Panduan & Aturan Main")

st.sidebar.subheader("🕹️ Cara Bermain")
st.sidebar.markdown("""
1. Klik tombol **START** dan izinkan akses kamera.
2. Angkat telunjuk ke kamera hingga muncul titik pelacak.
3. Gerakkan telunjuk untuk memotong buah.
""")

st.sidebar.subheader("⚖️ Aturan Poin")
st.sidebar.markdown("""
* 🍉 **Semangka:** +20 Poin
* 🍎 **Apel:** +10 Poin
* 💣 **Bom:** -50 Poin
""")

st.sidebar.subheader("❤️ Nyawa (Lives)")
st.sidebar.markdown("""
* Kamu memiliki **3 Nyawa**.
* Jika **Apel** atau **Semangka** jatuh melewati layar tanpa terpotong, nyawa berkurang 1.
* Membiarkan **Bom** jatuh *tidak* akan mengurangi nyawa.
* **GAME OVER** terjadi jika nyawa mencapai 0.
""")

# --- KONFIGURASI WEBRTC ---
RTC_CONFIGURATION = RTCConfiguration(
    {"iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]}
)

ctx = webrtc_streamer(
    key="fruit-ninja",
    mode=WebRtcMode.SENDRECV,
    rtc_configuration=RTC_CONFIGURATION,
    video_processor_factory=FruitNinjaProcessor,
    media_stream_constraints={
        "video": {
            "width": {"ideal": 640},
            "height": {"ideal": 480},
            "frameRate": {"ideal": 30}
        },
        "audio": False
    },
    async_processing=True
)

# --- LOGIKA RESTART GAME ---
if st.button("Restart Game"):
    processor = ctx.video_transformer or ctx.video_processor
    if processor:
        processor.score = 0
        processor.lives = 3
        processor.game_over = False
        processor.game_objects.clear()
        processor.cut_halves.clear()
        processor.particles.clear()
    st.rerun()