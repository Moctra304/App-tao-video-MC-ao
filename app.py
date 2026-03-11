import streamlit as st
import requests
import time
import os
import tempfile
from gtts import gTTS
from PIL import Image

# --- CẤU HÌNH GIAO DIỆN ---
st.set_page_config(page_title="Tạo Video MC Ảo", layout="centered", page_icon="🎙️")

st.markdown("""
    <style>
    .stButton > button {
        width: 100%;
        border-radius: 12px;
        height: 3.5em;
        background-color: #28a745;
        color: white;
        font-weight: bold;
        font-size: 18px;
        border: none;
    }
    .stButton > button:hover {
        background-color: #218838;
        color: white;
    }
    </style>
    """, unsafe_allow_html=True)

# --- HÀM HỖ TRỢ HEYGEN API ---
def upload_heygen_asset(file_path, api_key, content_type):
    """Tải file lên HeyGen để lấy URL asset"""
    url = "https://api.heygen.com/v1/asset/upload"
    headers = {
        "X-Api-Key": api_key,
        "Content-Type": content_type
    }
    with open(file_path, "rb") as f:
        response = requests.post(url, headers=headers, data=f)
    
    if response.status_code == 200:
        return response.json().get("data", {}).get("url")
    else:
        st.error(f"Lỗi upload asset: {response.text}")
        return None

# --- GIAO DIỆN CHÍNH ---

# Dòng 1: Tiêu đề lớn
st.markdown("<h1 style='text-align: center;'>🎙️ Tạo Video MC Ảo</h1>", unsafe_allow_html=True)

# Dòng 2: Upload ảnh
st.write("### 1. Tải ảnh bạn muốn tạo video lên")
uploaded_image = st.file_uploader("Chọn file ảnh (jpg, png, webp)", type=["jpg", "png", "webp"])
image_path = None
if uploaded_image:
    temp_img = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
    temp_img.write(uploaded_image.read())
    image_path = temp_img.name
    st.image(Image.open(image_path), caption="Preview ảnh MC", width=250)

# Dòng 3: Hai cột ngang
st.write("### 2. Cấu hình âm thanh")
col1, col2 = st.columns(2)
audio_path = None

with col1:
    st.write("**Chuyển văn bản thành âm thanh**")
    script = st.text_area("Nhập script tiếng Việt", placeholder="Xin chào, tôi là MC ảo của bạn...", height=120)
    voice_gender = st.selectbox("Chọn giọng", ["Nữ (vi)", "Nam (vi)"])
    if st.button("Tạo giọng nói"):
        if script:
            with st.spinner("Đang tạo giọng nói gTTS..."):
                tts = gTTS(text=script, lang='vi')
                temp_aud = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
                tts.save(temp_aud.name)
                audio_path = temp_aud.name
                st.audio(audio_path)
                st.success("Đã tạo giọng nói thành công!")
                st.session_state['audio_path'] = audio_path
        else:
            st.error("Vui lòng nhập script!")

with col2:
    st.write("**Hoặc tải âm thanh lên**")
    uploaded_audio = st.file_uploader("Chọn file âm thanh (mp3, wav)", type=["mp3", "wav"])
    if uploaded_audio:
        temp_aud = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
        temp_aud.write(uploaded_audio.read())
        audio_path = temp_aud.name
        st.audio(audio_path)
        st.session_state['audio_path'] = audio_path

# Lấy audio_path từ session state nếu được tạo từ gTTS
if 'audio_path' in st.session_state and not audio_path:
    audio_path = st.session_state['audio_path']

# Dòng 4: Ghi chú nổi bật
st.info("💡 Tạo âm thanh và miệng phải khớp nhau (lip-sync). Sử dụng HeyGen Avatar IV cho chất lượng thật")

# Dòng 5: Chọn độ phân giải
res_option = st.selectbox("Chọn độ phân giải", ["1080p", "720p", "480p"])
res_map = {"1080p": 1080, "720p": 720, "480p": 480}

# Dòng 6: Chọn khung video
ratio_option = st.selectbox("Chọn khung video", ["9:16 (Portrait)", "16:9 (Landscape)", "1:1 (Square)"])
ratio_map = {
    "9:16 (Portrait)": {"w": 1080, "h": 1920},
    "16:9 (Landscape)": {"w": 1920, "h": 1080},
    "1:1 (Square)": {"w": 1080, "h": 1080}
}

# Dòng 7: Ô nhập HeyGen API Key
api_key = st.text_input("HeyGen API Key", type="password", placeholder="Nhập API Key để bắt đầu...")

# Nút cuối: TẠO VIDEO MC ẢO
if st.button("TẠO VIDEO MC ẢO"):
    if not api_key:
        st.error("Vui lòng nhập HeyGen API Key!")
    elif not image_path:
        st.error("Vui lòng tải ảnh lên!")
    elif not audio_path:
        st.error("Vui lòng cung cấp âm thanh!")
    else:
        with st.spinner("Đang tạo video MC ảo HeyGen... 30-60 giây"):
            try:
                # Bước 1: Upload Assets lên HeyGen
                st.write("⏳ Đang tải tài nguyên lên HeyGen...")
                img_url = upload_heygen_asset(image_path, api_key, "image/png")
                aud_url = upload_heygen_asset(audio_path, api_key, "audio/mpeg")
                
                if img_url and aud_url:
                    # Bước 2: Gọi API Generate Video v2
                    gen_url = "https://api.heygen.com/v2/video/generate"
                    headers = {
                        "X-Api-Key": api_key,
                        "Content-Type": "application/json"
                    }
                    
                    dim = ratio_map[ratio_option]
                    payload = {
                        "video_inputs": [{
                            "character": {
                                "type": "talking_photo",
                                "photo_url": img_url
                            },
                            "audio": {
                                "type": "audio_url",
                                "url": aud_url
                            }
                        }],
                        "dimension": {"width": dim["w"], "height": dim["h"]}
                    }
                    
                    response = requests.post(gen_url, headers=headers, json=payload)
                    res_json = response.json()
                    
                    if response.status_code == 200:
                        video_id = res_json.get("data", {}).get("video_id")
                        st.write(f"✅ Đã gửi yêu cầu! Video ID: {video_id}")
                        
                        # Bước 3: Polling kiểm tra trạng thái
                        status_url = f"https://api.heygen.com/v2/video/status/{video_id}"
                        while True:
                            status_resp = requests.get(status_url, headers=headers)
                            status_data = status_resp.json().get("data", {})
                            status = status_data.get("status")
                            
                            if status == "completed":
                                video_url = status_data.get("video_url")
                                st.success("🎉 Chúc mừng! Video của bạn đã sẵn sàng.")
                                st.video(video_url)
                                st.download_button("📥 Tải Video về máy", requests.get(video_url).content, "mc_ao.mp4", "video/mp4")
                                break
                            elif status == "failed":
                                st.error(f"Tạo video thất bại: {status_data.get('error')}")
                                break
                            else:
                                st.write(f"⏳ Đang xử lý... Trạng thái: {status}")
                                time.sleep(5)
                    else:
                        st.error(f"Lỗi API Generate: {response.text}")
                else:
                    st.error("Không thể tải tài nguyên lên HeyGen.")
            except Exception as e:
                st.error(f"Đã xảy ra lỗi: {str(e)}")

# Dọn dẹp file tạm khi kết thúc (tùy chọn)
# os.unlink(image_path) if image_path else None
# os.unlink(audio_path) if audio_path else None
