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

# --- HÀM UPLOAD ASSET (ĐÚNG TỪ DOCS 2026) ---
def upload_heygen_asset(file_path, api_key):
    """Upload file lên HeyGen và trả về asset_id"""
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
                st.error(f"Upload OK nhưng không có asset_id: {resp_json}")
                return None
        else:
            st.error(f"Lỗi upload ({response.status_code}): {response.text}")
            return None
    except Exception as e:
        st.error(f"Lỗi mở/đọc file: {str(e)}")
        return None

# --- HÀM TẠO PHOTO AVATAR TỪ ASSET (BƯỚC QUAN TRỌNG BỊ THIẾU TRƯỚC ĐÂY) ---
def create_photo_avatar(photo_asset_id, api_key):
    """Tạo avatar từ photo asset_id để dùng trong video"""
    url = "https://api.heygen.com/v1/avatar/create"
    
    headers = {
        "X-Api-Key": api_key,
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    
    payload = {
        "assets": [photo_asset_id],
        "type": "photo"  # Hoặc "talking_photo" nếu docs yêu cầu
    }
    
    response = requests.post(url, headers=headers, json=payload)
    
    if response.status_code in (200, 201):
        resp_json = response.json()
        avatar_id = resp_json.get("data", {}).get("avatar_id")
        if avatar_id:
            return avatar_id
        else:
            st.error(f"Tạo avatar OK nhưng không có avatar_id: {resp_json}")
            return None
    else:
        st.error(f"Lỗi tạo avatar ({response.status_code}): {response.text}")
        return None

# --- GIAO DIỆN CHÍNH ---
st.markdown("<h1 style='text-align: center;'>🎙️ Tạo Video MC Ảo</h1>", unsafe_allow_html=True)

# 1. Upload ảnh
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

# 2. Âm thanh
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

# Cài đặt video
res_option = st.selectbox("Độ phân giải", ["1080p", "720p", "480p"])
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
        with st.spinner("Đang xử lý (upload + create avatar + generate, 60-180 giây)..."):
            try:
                st.write("⏳ Bước 1: Upload ảnh & âm thanh lên HeyGen...")
                img_asset_id = upload_heygen_asset(image_path, api_key)
                aud_asset_id = upload_heygen_asset(audio_path, api_key)
                
                if not img_asset_id or not aud_asset_id:
                    st.error("Upload thất bại. Kiểm tra key/file/mạng.")
                else:
                    st.write("✅ Upload xong. Bước 2: Tạo photo avatar từ ảnh...")
                    avatar_id = create_photo_avatar(img_asset_id, api_key)
                    
                    if not avatar_id:
                        st.error("Tạo avatar thất bại.")
                    else:
                        st.write("✅ Avatar tạo xong. Bước 3: Generate video...")
                        
                        gen_url = "https://api.heygen.com/v2/video/generate"
                        headers = {
                            "X-Api-Key": api_key,
                            "Content-Type": "application/json",
                            "Accept": "application/json"
                        }
                        
                        payload = {
                            "video_inputs": [{
                                "character": {
                                    "type": "avatar",
                                    "avatar_id": avatar_id,
                                    "avatar_style": "normal"  # Hoặc "closeUp" nếu cần
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
                                st.success(f"Yêu cầu gửi OK! Video ID: {video_id}")
                                
                                # Polling status
                                status_url = f"https://api.heygen.com/v2/video/status/{video_id}"
                                progress = st.progress(0)
                                status_placeholder = st.empty()
                                
                                for attempt in range(90):  # max ~7.5 phút
                                    status_resp = requests.get(status_url, headers=headers)
                                    if status_resp.status_code != 200:
                                        st.error(f"Lỗi check status: {status_resp.text}")
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
                                        st.error(f"Thất bại: {s_data.get('error', 'Không rõ lý do')}")
                                        break
                                    else:
                                        status_placeholder.text(f"Đang
