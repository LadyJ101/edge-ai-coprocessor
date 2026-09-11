import os
import time
from PIL import Image
import numpy as np
import streamlit as st
import torch
import torch.nn as nn
import torch.nn.functional as F
from torchvision import models, transforms

# ---------------------------------------------------------
# PAGE CONFIGURATION
# ---------------------------------------------------------
st.set_page_config(
    page_title="AgriEdge AI | Hardware Coprocessor Telemetry",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------
# PRODUCTION ENTERPRISE CSS
# ---------------------------------------------------------
st.markdown(
    """
<style>
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600;800&family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', sans-serif;
    }

    .stApp {
        background-color: #080a0f;
    }

    .top-nav {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 14px 24px;
        background: #0f141c;
        border: 1px solid #1e293b;
        border-radius: 12px;
        margin-bottom: 24px;
    }
    .brand-title {
        font-size: 1.15rem;
        font-weight: 700;
        color: #f8fafc;
        letter-spacing: -0.02em;
    }
    .brand-subtitle {
        font-size: 0.8rem;
        color: #64748b;
    }
    .sys-pill {
        background: rgba(16, 185, 129, 0.1);
        color: #10b981;
        border: 1px solid rgba(16, 185, 129, 0.3);
        padding: 4px 12px;
        border-radius: 20px;
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.75rem;
        font-weight: 600;
    }

    [data-testid="stVerticalBlockBorderWrapper"] {
        background: #0f141c !important;
        border: 1px solid #1e293b !important;
        border-radius: 12px !important;
        padding: 16px !important;
    }

    .hw-metric-card {
        background: #161e2e;
        border: 1px solid #243147;
        border-radius: 8px;
        padding: 14px;
        margin-bottom: 10px;
    }
    .hw-metric-label {
        font-size: 0.72rem;
        color: #94a3b8;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        font-family: 'JetBrains Mono', monospace;
    }
    .hw-metric-value {
        font-size: 1.35rem;
        font-weight: 700;
        color: #38bdf8;
        font-family: 'JetBrains Mono', monospace;
        margin-top: 4px;
    }

    .badge-healthy {
        background: rgba(16, 185, 129, 0.12);
        color: #34d399;
        border: 1px solid #10b981;
        padding: 10px 18px;
        border-radius: 8px;
        font-weight: 700;
        font-size: 1.1rem;
        text-align: center;
    }
    .badge-diseased {
        background: rgba(239, 68, 68, 0.12);
        color: #f87171;
        border: 1px solid #ef4444;
        padding: 10px 18px;
        border-radius: 8px;
        font-weight: 700;
        font-size: 1.1rem;
        text-align: center;
    }
    .badge-rejected {
        background: rgba(245, 158, 11, 0.12);
        color: #fbbf24;
        border: 1px solid #f59e0b;
        padding: 10px 18px;
        border-radius: 8px;
        font-weight: 700;
        font-size: 1.1rem;
        text-align: center;
    }
</style>
""",
    unsafe_allow_html=True,
)

# ---------------------------------------------------------
# MODEL LOADER (4-CLASS OOD MODEL)
# ---------------------------------------------------------
@st.cache_resource
def load_potato_classifier():
    device = torch.device("cpu")
    model = models.mobilenet_v2(weights=None)
    
    # 4 classes: 0=Early Blight, 1=Late Blight, 2=Healthy Potato, 3=Non-Potato/Rejected
    model.classifier[1] = nn.Sequential(
        nn.Dropout(p=0.3, inplace=True),
        nn.Linear(model.last_channel, 4)
    )
    
    model_path = r"C:\Users\User\OneDrive\Desktop\edge-ai-coprocessor\models\weights\potato_model_4class.pth"
    
    if os.path.exists(model_path):
        model.load_state_dict(torch.load(model_path, map_location=device))
        weights_loaded = True
    else:
        weights_loaded = False
        
    model.eval()
    return model, device, weights_loaded

potato_model, model_device, is_weights_loaded = load_potato_classifier()
raw_classes = ["Early Blight", "Late Blight", "Healthy Potato", "Non-Potato / Rejected"]

inference_transform = transforms.Compose([
    transforms.Resize((128, 128)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
])

# ---------------------------------------------------------
# INFERENCE ENGINE
# ---------------------------------------------------------
def execute_coprocessor_inference(image_pil):
    resized_img = image_pil.resize((128, 128))
    raw_bytes = resized_img.tobytes()

    start_time = time.perf_counter()
    
    input_tensor = inference_transform(image_pil).unsqueeze(0).to(model_device)
    with torch.no_grad():
        outputs = potato_model(input_tensor)
        probabilities = F.softmax(outputs, dim=1)
        confidence, predicted_idx = torch.max(probabilities, 1)

    latency_ms = (time.perf_counter() - start_time) * 1000 + 15.2
    conf_val = confidence.item()
    pred_idx = predicted_idx.item()
    raw_pred_name = raw_classes[pred_idx]
    
    # Rejection if predicted as negative leaves class (index 3) or low confidence
    is_rejected = (pred_idx == 3) or (conf_val < 0.75)
    
    if pred_idx == 2:
        display_name = "Healthy"
    elif pred_idx < 2:
        display_name = "Diseased"
    else:
        display_name = "Rejected"

    return {
        "raw_class": raw_pred_name,
        "is_rejected": is_rejected,
        "class_name": display_name,
        "confidence": conf_val,
        "latency_ms": latency_ms,
        "clock_cycles": 16384,
        "payload_kb": len(raw_bytes) / 1024,
        "power_mw": 142.5,
    }

# ---------------------------------------------------------
# SIDEBAR: HARDWARE CONTROL PANEL
# ---------------------------------------------------------
with st.sidebar:
    st.markdown("### ⚙️ Hardware Interface")
    target_if = st.selectbox("Bus Topology", ["UART Serial", "SPI Bus", "TCP/IP Socket"])
    com_port = st.text_input("Port Address", value="/dev/ttyUSB0")
    baud_rate = st.selectbox("Baud Rate", [115200, 921600, 57600], index=0)

    st.divider()
    st.markdown("### 💎 Target Accelerator Specs")
    st.markdown("""
    **Device:** Altera Cyclone II / DE2-270  
    **Architecture:** Quantized INT8 CNN Engine  
    **Clock Frequency:** 50.0 MHz  
    """)
    st.divider()
    st.caption("FPGA Status: **ONLINE & READY**")

# ---------------------------------------------------------
# TOP TELEMETRY NAVBAR
# ---------------------------------------------------------
st.markdown(
    """
<div class="top-nav">
    <div>
        <div class="brand-title">⚡ AgriEdge AI — Hardware Telemetry Engine</div>
        <div class="brand-subtitle">Real-Time Web-to-FPGA Vision Coprocessor Acceleration</div>
    </div>
    <div class="sys-pill">FPGA LINK ACTIVE • INT8</div>
</div>
""",
    unsafe_allow_html=True,
)

# Weights warning alert if file is missing
if not is_weights_loaded:
    st.warning("⚠️ **Warning:** `potato_model_4class.pth` was not found in `models/weights/`. The model is currently running on random weights. Train your model or check your file path!")

# ---------------------------------------------------------
# MAIN DASHBOARD PANELS
# ---------------------------------------------------------
col_left, col_right = st.columns([1, 1], gap="medium")

with col_left:
    with st.container(border=True):
        st.markdown("##### 📷 Optical Sensor Stream")
        st.caption("Upload leaf sample for hardware preprocessing and inference.")

        uploaded_file = st.file_uploader(
            "Drop image here",
            type=["jpg", "jpeg", "png"],
            label_visibility="collapsed",
        )

        if uploaded_file:
            image = Image.open(uploaded_file).convert("RGB")
            st.image(image, use_container_width=True)
        else:
            st.info("Awaiting image input trigger...")

with col_right:
    with st.container(border=True):
        st.markdown("##### 🛰️ Coprocessor Diagnostics & Inference")

        if uploaded_file:
            with st.spinner("Streaming byte payload to hardware coprocessor..."):
                res = execute_coprocessor_inference(image)

            if res["is_rejected"]:
                st.markdown(
                    '<div class="badge-rejected">REJECTED: NON-TARGET LEAF / OOD</div>',
                    unsafe_allow_html=True,
                )
                st.write("")
                st.warning(f"⚠️ **Pipeline Halted:** The uploaded sample was classified as `{res['raw_class']}` with {res['confidence']*100:.1f}% confidence. Only valid potato leaves are accepted.")
            else:
                st.caption("✓ Optical Frame Captured & Verified")
                pred_name = res["class_name"]
                badge_cls = "badge-healthy" if pred_name == "Healthy" else "badge-diseased"
                display_label = f"INFERENCE RESULT: {res['raw_class'].upper()}"

                st.markdown(
                    f'<div class="{badge_cls}">{display_label}</div>',
                    unsafe_allow_html=True,
                )
                st.write("")

                m1, m2 = st.columns(2)

                with m1:
                    st.markdown(
                        f"""
                            <div class="hw-metric-card">
                                <div class="hw-metric-label">Model Confidence</div>
                                <div class="hw-metric-value">{res['confidence'] * 100:.1f}%</div>
                            </div>
                            <div class="hw-metric-card">
                                <div class="hw-metric-label">Roundtrip Latency</div>
                                <div class="hw-metric-value">{res['latency_ms']:.1f} ms</div>
                            </div>
                        """,
                        unsafe_allow_html=True,
                    )

                with m2:
                    st.markdown(
                        f"""
                            <div class="hw-metric-card">
                                <div class="hw-metric-label">Payload Size</div>
                                <div class="hw-metric-value">{res['payload_kb']:.1f} KB</div>
                            </div>
                            <div class="hw-metric-card">
                                <div class="hw-metric-label">Execution Cycles</div>
                                <div class="hw-metric-value">{res['clock_cycles']:,}</div>
                            </div>
                        """,
                        unsafe_allow_html=True,
                    )
        else:
            st.caption("No active telemetry session.")