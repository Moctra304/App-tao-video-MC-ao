import streamlit as st
import requests
import time
import os
import tempfile
import mimetypes
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

# --- HÀM UPLOAD ASSET ---
def upload_heygen_asset(file_path, api_key):
    url = "https://upload.heygen.com/v1/asset"
    
    content_type, _ = mimetypes.guess_type(file_path)
    if not content_type:
        content_type = "application/octet-stream"
    
    headers = {
        "X-Api-Key": api_key,
        "Content-Type": content_type,
        "Accept": "application/json"
    }
    
    try:
        with open(file_path, "rb") as f:
            data = f.read()
        
        response = requests.post(url, headers=headers, data=data)
        
        if response.status_code == 200:
            resp_json = response.json()
            asset_id = resp_json.get("data", {}).get("asset_id")
            if asset_id:
                return asset_id
            else:
                st.error("Upload thành công nhưng không tìm thấy asset_id trong response.")
                return None
        else:
            st.error(f"Lỗi upload ({response.status_code}): {response.text}")
            return None
    except Exception as e:
        st.error(f"Lỗi khi upload file: {str(e)}")
        return None

# --- GIAO DIỆN CHÍNH ---
st.markdown("<h1 style='text-align: center;'>🎙️ Tạo Video MC Ảo</h1>", unsafe_allow_html=True)

st.subheader("1. Tải ảnh MC lên")
uploaded_image = st.file_uploader("Chọn file ảnh (jpg, png, webp)", type=["jpg", "png", "webp"])
image_path = None
if uploaded_image is not None:
    ext = os.path.splitext(uploaded_image.name)[1] or ".png"
    temp_img = tempfile.NamedTemporaryFile(delete=False, suffix=ext)
    temp_img.write(uploaded_image.getvalue())
    temp_img.close()
    image_path = temp_img.name
    st.image(image_path, caption="Preview ảnh MC", width=250)

st.subheader("2. Cấu hình âm thanh")
col1, col2 = st.columns(2)
audio_path = None

with col1:
    st.markdown("**Chuyển văn bản thành giọng nói**")
    script = st.text_area("Nhập script tiếng Việt", placeholder="Xin chào, tôi là MC ảo của bạn...", height=120)
    if st.button("Tạo giọng nói"):
        if script.strip():
            with st.spinner("Đang tạo giọng nói bằng gTTS..."):
                tts = gTTS(text=script, lang='vi')
                temp_aud = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
                tts.save(temp_aud.name)
                temp_aud.close()
                audio_path = temp_aud.name
                st.audio(audio_path)
                st.success("Giọng nói đã tạo!")
                st.session_state['audio_path'] = audio_path
        else:
            st.error("Vui lòng nhập script!")

with col2:
    st.markdown("**Hoặc tải file âm thanh lên**")
    uploaded_audio = st.file_uploader("Chọn file (mp3, wav)", type=["mp3", "wav"])
    if uploaded_audio is not None:
        ext = os.path.splitext(uploaded_audio.name)[1] or ".mp3"
        temp_aud = tempfile.NamedTemporaryFile(delete=False, suffix=ext)
        temp_aud.write(uploaded_audio.getvalue())
        temp_aud.close()
        audio_path = temp_aud.name
        st.audio(audio_path)
        st.session_state['audio_path'] = audio_path

if 'audio_path' in st.session_state and audio_path is None:
    audio_path = st.session_state['audio_path']

st.info("💡 Âm thanh và miệng phải khớp (lip-sync). HeyGen Avatar IV cho chất lượng cao nhất!")

ratio_option = st.selectbox("Khung hình", ["9:16 (Portrait)", "16:9 (Landscape)", "1:1 (Square)"])
ratio_map = {
    "9:16 (Portrait)": {"width": 1080, "height": 1920},
    "16:9 (Landscape)": {"width": 1920, "height": 1080},
    "1:1 (Square)": {"width": 1080, "height": 1080}
}
dim = ratio_map[ratio_option]

api_key = st.text_input("HeyGen API Key", type="password", placeholder="Nhập key từ dashboard HeyGen...")

if st.button("TẠO VIDEO MC ẢO", type="primary"):
    if not api_key:
        st.error("Nhập HeyGen API Key!")
    elif not image_path or not os.path.exists(image_path):
        st.error("Tải ảnh lên trước!")
    elif not audio_path or not os.path.exists(audio_path):
        st.error("Tạo hoặc tải âm thanh lên!")
    else:
        with st.spinner("Đang xử lý (upload + generate, 30-120 giây)..."):
            try:
                st.write("⏳ Bước 1: Upload ảnh & âm thanh lên HeyGen...")
                img_asset_id = upload_heygen_asset(image_path, api_key)
                aud_asset_id = upload_heygen_asset(audio_path, api_key)
                
                if not img_asset_id or not aud_asset_id:
                    st.error("Upload thất bại. Kiểm tra API key, file hoặc mạng.")
                else:
                    st.write("✅ Upload xong. Bước 2: Tạo video...")
                    
                    gen_url = "https://api.heygen.com/v2/video/generate"
                    headers = {
                        "X-Api-Key": api_key,
                        "Content-Type": "application/json",
                        "Accept": "application/json"
                    }
                    
                    payload = {
                        "video_inputs": [{
                            "character": {
                                "type": "talking_photo",
                                "photo_asset_id": img_asset_id
                            },
                            "voice": {
                                "type": "audio",
                                "audio_asset_id": aud_asset_id
                            }
                        }],
                        "dimension": {"width": dim["width"], "height": dim["height"]}
                    }
                    
                    resp = requests.post(gen_url, headers=headers, json=payload)
                    
                    if resp.status_code in (200, 201):
                        data = resp.json()
                        video_id = data.get("data", {}).get("video_id")
                        if video_id:
                            st.success("Yêu cầu gửi OK! Video ID: " + video_id)
                            
                            status_url = "https://api.heygen.com/v2/video/status/" + video_id
                            progress = st.progress(0)
                            status_placeholder = st.empty()
                            
                            for attempt in range(60):
                                status_resp = requests.get(status_url, headers=headers)
                                if status_resp.status_code != 200:
                                    st.error("Lỗi check status: " + status_resp.text)
                                    break
                                
                                s_data = status_resp.json().get("data", {})
                                status = s_data.get("status")
                                
                                if status == "completed":
                                    video_url = s_data.get("video_url") or s_data.get("download_url")
                                    if video_url:
                                        st.success("🎉 Video sẵn sàng!")
                                        st.video(video_url)
                                        vid_data = requests.get(video_url).content
                                        st.download_button("📥 Tải video", vid_data, "mc_ao.mp4", "video/mp4")
                                    break
                                elif status in ("failed", "error"):
                                    st.error("Thất bại: " + s_data.get('error', 'Không rõ lý do'))
                                    break
                                else:
                                    status_placeholder.text("Đang xử lý... " + status + " (thử " + str(attempt+1) + "/60)")
                                    progress.progress(min((attempt + 1) / 60.0, 1.0))
                                    time.sleep(5)
                            else:
                                st.warning("Timeout chờ video. Kiểm tra dashboard HeyGen.")
                        else:
                            st.error("Không có video_id trong response: " + str(data))
                    else:
                        st.error("Lỗi generate (" + str(resp.status_code) + "): " + resp.text)
            except Exception as ex:
                st.error("Lỗi tổng: " + str(ex))
