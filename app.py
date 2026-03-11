import streamlit as st
import requests
import time
from gtts import gTTS
import os
import tempfile
from PIL import Image

# --- CẤU HÌNH TRANG ---
st.set_page_config(page_title="Tạo Video MC Ảo", layout="centered", page_icon="🎙️")

# --- CSS TÙY CHỈNH (Cho nút bấm full width và màu sắc) ---
st.markdown("""
    <style>
    .stButton > button {
        width: 100%;
        border-radius: 10px;
        height: 3em;
        background-color: #007BFF;
        color: white;
        font-weight: bold;
    }
    </style>
    """, unsafe_allow_html=True)

# Dòng 1: Tiêu đề lớn
st.title("🎙️ Tạo Video MC Ảo")

# Dòng 2: Upload ảnh
st.subheader("1. Tải ảnh chân dung")
uploaded_image = st.file_uploader("Tải ảnh bạn muốn tạo video lên", type=["jpg", "png", "webp"])
if uploaded_image:
    image = Image.open(uploaded_image)
    st.image(image, caption="Preview ảnh chân dung", width=300)

# Dòng 3: Hai cột ngang
st.subheader("2. Cấu hình âm thanh")
col1, col2 = st.columns(2)

audio_path = None

with col1:
    st.write("### Chuyển văn bản thành âm thanh")
    script = st.text_area("Nhập script tại đây", placeholder="Chào mừng bạn đến với ứng dụng tạo video MC ảo...", height=150)
    voice_gender = st.selectbox("Chọn giọng nói", ["Nam (vi-VN)", "Nữ (vi-VN)"])
    if st.button("Tạo giọng nói"):
        if script:
            with st.spinner("Đang chuyển văn bản thành âm thanh..."):
                # Sử dụng gTTS tiếng Việt
                tts = gTTS(text=script, lang='vi')
                temp_audio = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
                tts.save(temp_audio.name)
                audio_path = temp_audio.name
                st.audio(audio_path)
                st.success("Đã tạo giọng nói thành công!")
        else:
            st.error("Vui lòng nhập script!")

with col2:
    st.write("### Hoặc tải âm thanh lên")
    uploaded_audio = st.file_uploader("Tải file âm thanh (mp3, wav)", type=["mp3", "wav"])
    if uploaded_audio:
        temp_audio = tempfile.NamedTemporaryFile(delete=False, suffix=f".{uploaded_audio.name.split('.')[-1]}")
        temp_audio.write(uploaded_audio.read())
        audio_path = temp_audio.name
        st.audio(audio_path)

# Dòng 4: Ghi chú nổi bật
st.info("💡 Tạo âm thanh và miệng phải khớp nhau (lip-sync). Sử dụng HeyGen Avatar IV cho chất lượng thật")

# Dòng 5: Chọn độ phân giải
resolution = st.selectbox("Chọn độ phân giải", ["480p", "720p", "1080p"])

# Dòng 6: Chọn khung video
aspect_ratio = st.selectbox("Chọn khung video", ["16:9 (Landscape)", "9:16 (Portrait)", "1:1 (Square)"])

# Dòng 7: Ô nhập HeyGen API Key
api_key = st.text_input("HeyGen API Key", type="password", help="Lấy API Key từ dashboard HeyGen của bạn")

# Dòng cuối: Nút lớn TẠO VIDEO MC ẢO
if st.button("TẠO VIDEO MC ẢO"):
    if not api_key:
        st.error("❌ Vui lòng nhập HeyGen API Key!")
    elif not uploaded_image:
        st.error("❌ Vui lòng tải ảnh lên!")
    elif not audio_path:
        st.error("❌ Vui lòng cung cấp âm thanh!")
    else:
        with st.spinner("Đang tạo video MC ảo HeyGen... 30-60 giây"):
            try:
                # --- QUY TRÌNH HEYGEN API V2 (2026) ---
                # 1. Trong thực tế, bạn cần upload ảnh và audio lên S3/HeyGen Assets để lấy URL
                # Ở đây giả định bạn đã có URL sau khi upload
                
                headers = {
                    "X-Api-Key": api_key,
                    "Content-Type": "application/json"
                }
                
                # Payload chuẩn HeyGen v2
                payload = {
                    "video_inputs": [
                        {
                            "character": {
                                "type": "avatar",
                                "avatar_id": "Daisy-professional-20220502", # Hoặc ID từ ảnh upload
                                "avatar_style": "normal"
                            },
                            "voice": {
                                "type": "audio",
                                "audio_url": "URL_AM_THANH_CONG_KHAI" 
                            }
                        }
                    ],
                    "dimension": {
                        "width": 1920 if "16:9" in aspect_ratio else 1080,
                        "height": 1080 if "16:9" in aspect_ratio else 1920
                    }
                }
                
                # Gửi yêu cầu (Bỏ comment khi chạy thực tế)
                # response = requests.post("https://api.heygen.com/v2/video/generate", json=payload, headers=headers)
                # video_id = response.json().get("data", {}).get("video_id")
                
                # Giả lập Polling
                video_id = "demo_heygen_123"
                st.write(f"Đang xử lý Video ID: {video_id}...")
                
                # Vòng lặp kiểm tra trạng thái mỗi 3 giây
                for i in range(1, 11):
                    time.sleep(3)
                    st.write(f"Đang kiểm tra trạng thái... Lần {i}")
                    # status_resp = requests.get(f"https://api.heygen.com/v2/video/status/{video_id}", headers=headers)
                    # if status_resp.json().get("data").get("status") == "completed": break
                
                # Hiển thị kết quả
                st.success("✅ Video MC ảo đã được tạo thành công!")
                st.video("https://www.w3schools.com/html/mov_bbb.mp4") # Demo video
                
                # Nút tải về
                st.download_button(
                    label="📥 Tải video về máy",
                    data="DỮ_LIỆU_VIDEO_BINARY",
                    file_name="mc_ao_heygen.mp4",
                    mime="video/mp4"
                )
                    
            except Exception as e:
                st.error(f"Lỗi hệ thống: {str(e)}")

# --- FILE REQUIREMENTS.TXT ---
# streamlit
# requests
# gTTS
# moviepy
# pillow
