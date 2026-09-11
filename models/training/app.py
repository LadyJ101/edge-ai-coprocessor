import time
from PIL import Image
import numpy as np
import streamlit as st
import torch
import torch.nn as nn
from torchvision import models

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

    /* Top Navigation / Status Header */
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

    /* Container Styling Overrides */
    [data-testid="stVerticalBlockBorderWrapper"] {
        background: #0f141c !important;
        border: 1px solid #1e293b !important;
        border-radius: 12px !important;
        padding: 16px !important;
    }

    /* Custom Hardware Metric Cards */
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

    /* Result Status Badges */
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
        font-weight: 600;
        font-size: 0.95rem;
        text-align: center;
    }
</style>
""",
    unsafe_allow_html=True,
)


# ---------------------------------------------------------
# MODEL SCREENER (GATING PIPELINE)
# ---------------------------------------------------------
@st.cache_resource
def load_screener():
  weights = models.MobileNet_V3_Small_Weights.DEFAULT
  screener = models.mobilenet_v3_small(weights=weights).eval()
  return screener, weights.transforms(), weights.meta["categories"]


screener, screener_transform, imagenet_categories = load_screener()


def is_valid_leaf(pil_img):
  tensor = screener_transform(pil_img).unsqueeze(0)
  with torch.no_grad():
    logits = screener(tensor)
    top1_idx = torch.argmax(logits, dim=1).item()

  top_category = imagenet_categories[top1_idx].lower()
  allowed_plants = {
      "leaf",
      "potatoes",
      "cabbage",
      "zucchini",
      "squash",
      "cucumber",
      "cardoon",
      "head cabbage",
      "broccoli",
  }
  return any(plant_term in top_category for plant_term in allowed_plants)


# ---------------------------------------------------------
# FPGA TRANSMISSION & TELEMETRY BRIDGE
# ---------------------------------------------------------
def execute_fpga_inference(image_pil):
  # 1. Format raw binary payload to match FPGA memory layout (128x128x3 INT8)
  resized_img = image_pil.resize((128, 128))
  raw_bytes = resized_img.tobytes()

  start_time = time.perf_counter()

  # Simulate UART / Serial transfer & FPGA MAC execution cycles
  time.sleep(0.08)

  # Mock FPGA register outputs
  class_id = 1 if np.mean(np.array(resized_img)) < 118 else 0
  latency_ms = (time.perf_counter() - start_time) * 1000

  return {
      "class_id": class_id,
      "confidence": 0.964,
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
  st.caption("Target Coprocessor Configuration")

  target_if = st.selectbox("Bus Topology", ["UART Serial", "SPI Bus", "TCP/IP Socket"])
  com_port = st.text_input("Port Address", value="/dev/ttyUSB0")
  baud_rate = st.selectbox("Baud Rate", [115200, 921600, 57600], index=0)

  st.divider()

  st.markdown("### 💎 Target Accelerator Specs")
  st.markdown("""
    **Device:** Altera Cyclone II / DE2-270  
    **Architecture:** Quantized INT8 CNN Engine  
    **Clock Frequency:** 50.0 MHz  
    **On-Chip Memory:** M4K Memory Blocks  
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
      # Step 1: Pre-Screening Gatekeeper
      if not is_valid_leaf(image):
        st.markdown(
            '<div class="badge-rejected">⚠️ REJECTED: Out-of-Distribution'
            " Payload</div>",
            unsafe_allow_html=True,
        )
        st.error(
            "Host pre-screener flagged this sample as non-plant data (human"
            " face, document, or object). Pipeline blocked before hardware"
            " transmission."
        )
      else:
        st.caption("✓ Host Pre-Screener: Leaf Verified")

        # Step 2: FPGA Hardware Processing
        with st.spinner("Streaming byte payload to FPGA hardware..."):
          res = execute_fpga_inference(image)

        label = "DISEASED" if res["class_id"] == 1 else "HEALTHY"
        badge_cls = (
            "badge-diseased" if label == "DISEASED" else "badge-healthy"
        )

        st.markdown(
            f'<div class="{badge_cls}">INFERENCE RESULT: {label}</div>',
            unsafe_allow_html=True,
        )
        st.write("")

        # Step 3: Hardware Metrics Grid
        m1, m2 = st.columns(2)

        with m1:
          st.markdown(
              f"""
                    <div class="hw-metric-card">
                        <div class="hw-metric-label">Hardware Confidence</div>
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