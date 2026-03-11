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

# Hàm upload asset lên HeyGen (photo hoặc audio)
def upload_asset(file_path, api_key, is_image=False):
    url = "https://upload.heygen.com/v1/asset"
    
    # Detect MIME type chính xác
    if is_image:
        img = Image.open(file_path)
        format_lower = img.format.lower()
        if format_lower == 'png':
            content_type = "image/png"
        elif format_lower in ('jpeg', 'jpg'):
            content_type = "image/jpeg"
        elif format_lower == 'webp':
            content_type = "image/webp"
        else:
            st.error("Format ảnh không hỗ trợ.")
            return None
    else:
        ext = os.path.splitext(file_path)[1].lower()
        if ext == '.mp3':
            content_type = "audio/mpeg"
        elif ext == '.wav':
            content_type = "audio/wav"
        else:
            st.error("Format âm thanh không hỗ trợ.")
            return None
    
    headers = {
        "X-Api-Key": api_key,
        "Content-Type": content_type,
        "Accept": "application/json"
    }
    
    with open(file_path, "rb") as f:
        data = f.read()
    
    response = requests.post(url, headers=headers, data=data)
    
    if response.status_code == 200:
        resp_json = response.json()
        asset_id = resp_json.get("data", {}).get("asset_id")
        if asset_id:
            return asset_id
        else:
            st.error(f"Upload thành công nhưng không có asset_id: {resp_json}")
            return None
    else:
        st.error(f"Lỗi upload ({response.status_code}): {response.text}")
        return None

# Dòng 1: Tiêu đề lớn
st.title("🎙️ Tạo Video MC Ảo")

# Dòng 2: Upload ảnh
st.subheader("1. Tải ảnh chân dung")
uploaded_image = st.file_uploader("Tải ảnh bạn muốn tạo video lên", type=["jpg", "png", "webp"])
image_path = None
if uploaded_image:
    ext = os.path.splitext(uploaded_image.name)[1]
    temp_img = tempfile.NamedTemporaryFile(delete=False, suffix=ext)
    temp_img.write(uploaded_image.read())
    temp_img.close()
    image_path = temp_img.name
    image = Image.open(image_path)
    st.image(image, caption="Preview ảnh chân dung", width=300)

# Dòng 3: Hai cột ngang
st.subheader("2. Cấu hình âm thanh")
col1, col2 = st.columns(2)

audio_path = None

with col1:
    st.write("### Chuyển văn bản thành âm thanh")
    script = st.text_area("Nhập script tại đây", placeholder="Chào mừng bạn đến với ứng dụng tạo video MC ảo...", height=150)
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
        ext = os.path.splitext(uploaded_audio.name)[1]
        temp_audio = tempfile.NamedTemporaryFile(delete=False, suffix=ext)
        temp_audio.write(uploaded_audio.read())
        temp_audio.close()
        audio_path = temp_audio.name
        st.audio(audio_path)

# Dòng 4: Ghi chú nổi bật
st.info("💡 Tạo âm thanh và miệng phải khớp nhau (lip-sync). Sử dụng HeyGen Avatar IV cho chất lượng thật")

# Dòng 5: Chọn độ phân giải
resolution = st.selectbox("Chọn độ phân giải", ["480p", "720p", "1080p"])
res_map = {"480p": 480, "720p": 720, "1080p": 1080}

# Dòng 6: Chọn khung video
aspect_ratio = st.selectbox("Chọn khung video", ["16:9 (Landscape)", "9:16 (Portrait)", "1:1 (Square)"])

# Dòng 7: Ô nhập HeyGen API Key
api_key = st.text_input("HeyGen API Key", type="password", help="Lấy API Key từ dashboard HeyGen của bạn")

# Dòng cuối: Nút lớn TẠO VIDEO MC Ảo
if st.button("TẠO VIDEO MC Ảo"):
    if not api_key:
        st.error("❌ Vui lòng nhập HeyGen API Key!")
    elif not image_path:
        st.error("❌ Vui lòng tải ảnh lên!")
    elif not audio_path:
        st.error("❌ Vui lòng cung cấp âm thanh!")
    else:
        with st.spinner("Đang tạo video MC ảo HeyGen... 30-60 giây"):
            try:
                # 1. Upload ảnh và audio để lấy asset_id
                photo_asset_id = upload_asset(image_path, api_key, is_image=True)
                audio_asset_id = upload_asset(audio_path, api_key, is_image=False)
                
                if not photo_asset_id or not audio_asset_id:
                    st.error("Upload asset thất bại.")
                    raise Exception("Asset upload failed")
                
                # 2. Xác định dimension dựa resolution và aspect_ratio
                base_height = res_map[resolution]
                if "16:9" in aspect_ratio:
                    width, height = int(base_height * 16 / 9), base_height
                elif "9:16" in aspect_ratio:
                    width, height = base_height, int(base_height * 16 / 9)
                else:  # 1:1
                    width, height = base_height, base_height
                
                # 3. Payload cho generate video
                headers = {
                    "X-Api-Key": api_key,
                    "Content-Type": "application/json"
                }
                
                payload = {
                    "video_inputs": [
                        {
                            "character": {
                                "type": "talking_photo",
                                "photo_asset_id": photo_asset_id
                            },
                            "voice": {
                                "type": "audio",
                                "audio_asset_id": audio_asset_id
                            }
                        }
                    ],
                    "dimension": {
                        "width": width,
                        "height": height
                    }
                }
                
                response = requests.post("https://api.heygen.com/v2/video/generate", json=payload, headers=headers)
                
                if response.status_code != 200:
                    st.error(f"Lỗi generate video: {response.text}")
                    raise Exception("Generate failed")
                
                video_id = response.json().get("data", {}).get("video_id")
                st.write(f"Đang xử lý Video ID: {video_id}...")
                
                # 4. Polling trạng thái
                status_url = f"https://api.heygen.com/v2/video/status/{video_id}"
                while True:
                    status_resp = requests.get(status_url, headers=headers)
                    status_data = status_resp.json().get("data", {})
                    status = status_data.get("status")
                    
                    if status == "completed":
                        video_url = status_data.get("video_url")
                        st.success("✅ Video MC ảo đã được tạo thành công!")
                        st.video(video_url)
                        
                        # Nút tải về
                        video_data = requests.get(video_url).content
                        st.download_button(
                            label="📥 Tải video về máy",
                            data=video_data,
                            file_name="mc_ao_heygen.mp4",
                            mime="video/mp4"
                        )
                        break
                    elif status == "failed":
                        st.error(f"Tạo video thất bại: {status_data.get('error')}")
                        break
                    else:
                        st.write(f"⏳ Trạng thái: {status}. Đợi 5 giây...")
                        time.sleep(5)
                    
            except Exception as e:
                st.error(f"Lỗi hệ thống: {str(e)}")
            finally:
                # Dọn dẹp file tạm
                if image_path and os.path.exists(image_path):
                    os.unlink(image_path)
                if audio_path and os.path.exists(audio_path):
                    os.unlink(audio_path)

# --- FILE REQUIREMENTS.TXT ---
# streamlit
# requests
# gTTS
# pillow
# moviepy  # Tùy chọn nếu cần ghép video local
