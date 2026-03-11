"""
╔══════════════════════════════════════════════════════════════════════╗
║        PSYCHOMODS CYBER FORENSIC LAB  –  v3.0                       ║
║        Advanced Image Manipulation Detection System                  ║
║        https://psychomods.infy.uk                                    ║
╠══════════════════════════════════════════════════════════════════════╣
║  Install:                                                            ║
║    pip install streamlit pillow opencv-python-headless numpy         ║
║                matplotlib reportlab scipy scikit-image plotly        ║
║                mediapipe                                             ║
╚══════════════════════════════════════════════════════════════════════╝
"""

# ── stdlib ─────────────────────────────────────────────────────────────
import io, math, time, hashlib, zipfile, json, os, struct, re
from datetime import datetime, timezone
from collections import defaultdict

# ── third-party ────────────────────────────────────────────────────────
import cv2
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.gridspec import GridSpec
import plotly.graph_objects as go
import plotly.express as px
from PIL import Image, ImageChops, ImageEnhance, ImageFilter, ExifTags
from scipy.ndimage import uniform_filter, gaussian_filter
# scipy.stats unused imports removed
from skimage.feature import local_binary_pattern
# estimate_sigma replaced with pure-numpy version for compatibility
# skimage.measure unused
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table,
    TableStyle, HRFlowable, KeepTogether
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors as rl_colors
from reportlab.lib.units import mm
from reportlab.lib.pagesizes import A4
import streamlit as st
import streamlit.components.v1 as components

# ── optional mediapipe ─────────────────────────────────────────────────
try:
    import mediapipe as mp
    MP_AVAILABLE = True
except ImportError:
    MP_AVAILABLE = False

# ══════════════════════════════════════════════════════════════════════
# PAGE CONFIG
# ══════════════════════════════════════════════════════════════════════
st.set_page_config(
    page_title="Psychomods Cyber Forensic Lab v3",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ══════════════════════════════════════════════════════════════════════
# MATRIX RAIN
# ══════════════════════════════════════════════════════════════════════
components.html("""
<canvas id="mx"></canvas>
<style>
  #mx{position:fixed;top:0;left:0;width:100vw;height:100vh;
      z-index:-1;pointer-events:none;background:#000;}
</style>
<script>
  const c=document.getElementById("mx"),ctx=c.getContext("2d");
  function rs(){c.width=innerWidth;c.height=innerHeight;}
  rs(); window.addEventListener("resize",rs);
  const CH="01アイウエオカキサシスセソABCDEF01";
  let drops=[];
  function init(){drops=Array(Math.ceil(c.width/13)).fill(1);}
  init(); window.addEventListener("resize",init);
  function draw(){
    ctx.fillStyle="rgba(0,0,0,0.05)";
    ctx.fillRect(0,0,c.width,c.height);
    ctx.font="13px monospace";
    drops.forEach((y,i)=>{
      ctx.fillStyle=i%5===0?"#ffffff":"#00ff9c";
      ctx.fillText(CH[Math.floor(Math.random()*CH.length)],i*13,y*13);
      if(y*13>c.height&&Math.random()>.975)drops[i]=0;
      drops[i]++;
    });
  }
  setInterval(draw,35);
</script>
""", height=0, width=0)

# ══════════════════════════════════════════════════════════════════════
# GLOBAL CSS
# ══════════════════════════════════════════════════════════════════════
st.markdown("""
<style>
html,body,[data-testid="stAppViewContainer"]{background:transparent!important;}
[data-testid="stAppViewContainer"]>.main{background:rgba(0,0,0,0.6);}
[data-testid="stSidebar"]{background:rgba(0,0,0,0.88)!important;}
::-webkit-scrollbar{width:5px;}
::-webkit-scrollbar-thumb{background:#00ff9c;border-radius:3px;}

.hdr{background:rgba(0,0,0,0.85);backdrop-filter:blur(20px);
  border-bottom:1px solid rgba(0,255,156,.5);padding:24px 30px 18px;
  border-radius:0 0 20px 20px;margin-bottom:24px;text-align:center;}
.hdr-t{font-size:38px;font-weight:900;letter-spacing:4px;color:#00ff9c;
  text-shadow:0 0 24px #00ff9c99;font-family:'Courier New',monospace;}
.hdr-s{color:#9affd7;font-size:12px;letter-spacing:2px;margin-top:4px;}

.sec{font-size:15px;font-weight:700;color:#00ff9c;letter-spacing:2px;
  border-left:4px solid #00ff9c;padding:6px 0 6px 14px;margin:28px 0 12px;
  background:rgba(0,255,156,.06);border-radius:0 8px 8px 0;
  font-family:'Courier New',monospace;}

.glass{background:rgba(0,0,0,.45);backdrop-filter:blur(18px);
  border:1px solid rgba(0,255,156,.3);border-radius:14px;padding:20px;margin-bottom:12px;}

.vcard{text-align:center;padding:18px;border-radius:12px;
  border:1px solid rgba(0,255,156,.3);background:rgba(0,0,0,.5);}

.mrow{display:flex;gap:8px;flex-wrap:wrap;margin:8px 0;}
.pill{background:rgba(0,255,156,.08);border:1px solid rgba(0,255,156,.3);
  border-radius:8px;padding:6px 12px;font-family:'Courier New',monospace;
  font-size:12px;color:#9affd7;}
.pill b{color:#00ff9c;}

.warn{background:rgba(255,100,0,.12);border:1px solid rgba(255,100,0,.4);
  border-radius:8px;padding:10px 14px;color:#ffaa66;font-size:13px;}
.ok{background:rgba(0,200,100,.1);border:1px solid rgba(0,200,100,.4);
  border-radius:8px;padding:10px 14px;color:#66ffaa;font-size:13px;}

div[data-testid="stFileUploader"]{
  border:1px dashed rgba(0,255,156,.4)!important;
  border-radius:12px;padding:8px;background:rgba(0,0,0,.3);}
div.stButton>button{
  background:linear-gradient(135deg,#00ff9c22,#00cc7a33);
  color:#00ff9c;border:1px solid #00ff9c;border-radius:10px;
  font-weight:700;font-family:'Courier New',monospace;
  letter-spacing:1px;padding:10px 26px;transition:all .25s;}
div.stButton>button:hover{background:#00ff9c;color:#000;box-shadow:0 0 18px #00ff9c88;}
div[data-testid="stProgress"]>div>div{
  background:linear-gradient(90deg,#00ff9c,#00cc7a)!important;}
label,.stMarkdown p{color:#c8ffe8!important;}
div[data-testid="stExpander"]{
  border:1px solid rgba(0,255,156,.25)!important;
  border-radius:10px;background:rgba(0,0,0,.35);}
.stTabs [data-baseweb="tab"]{color:#9affd7;font-family:'Courier New',monospace;}
.stTabs [aria-selected="true"]{color:#00ff9c!important;}
[data-testid="stMetric"]{
  background:rgba(0,255,156,.06);border:1px solid rgba(0,255,156,.2);
  border-radius:10px;padding:10px;}
[data-testid="stMetricValue"]{color:#00ff9c!important;}
[data-testid="stMetricLabel"]{color:#9affd7!important;}

.footer{position:fixed;bottom:0;left:0;width:100%;
  background:rgba(0,0,0,.82);backdrop-filter:blur(15px);
  border-top:1px solid rgba(0,255,156,.35);padding:9px;
  text-align:center;color:#00ff9c;font-size:11px;
  font-family:'Courier New',monospace;z-index:9999;}
html{scroll-behavior:smooth;}
</style>
<div class="hdr">
  <div class="hdr-t">🧠 PSYCHOMODS CYBER FORENSIC LAB</div>
  <div class="hdr-s">⚡ v3.0 · Advanced Image Manipulation Detection System ⚡</div>
</div>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════
# UTILITIES
# ══════════════════════════════════════════════════════════════════════
def sec(title: str):
    st.markdown(f'<div class="sec">▶ {title}</div>', unsafe_allow_html=True)

def pill_row(pairs: list):
    html = '<div class="mrow">'
    for k, v in pairs:
        html += f'<div class="pill">{k} <b>{v}</b></div>'
    html += '</div>'
    st.markdown(html, unsafe_allow_html=True)

def pil_to_cv(img: Image.Image) -> np.ndarray:
    return cv2.cvtColor(np.array(img.convert("RGB")), cv2.COLOR_RGB2BGR)

def cv_to_pil(img: np.ndarray) -> Image.Image:
    if len(img.shape) == 2:
        return Image.fromarray(img)
    return Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))

def fig_to_pil(fig) -> Image.Image:
    buf = io.BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight", facecolor="#000", dpi=110)
    buf.seek(0); plt.close(fig)
    return Image.open(buf).copy()

def dark_fig(w=5, h=3):
    fig, ax = plt.subplots(figsize=(w, h), facecolor="#000")
    ax.set_facecolor("#000")
    for sp in ax.spines.values(): sp.set_edgecolor("#00ff9c33")
    ax.tick_params(colors="#9affd7", labelsize=8)
    ax.xaxis.label.set_color("#9affd7")
    ax.yaxis.label.set_color("#9affd7")
    return fig, ax

def hash_bytes(data: bytes):
    return hashlib.sha256(data).hexdigest(), hashlib.md5(data).hexdigest()


# ══════════════════════════════════════════════════════════════════════
# ── MODULE 1 · ELA ────────────────────────────────────────────────────
# ══════════════════════════════════════════════════════════════════════
def ela(img: Image.Image, quality=92, scale=20) -> Image.Image:
    rgb = img.convert("RGB")
    buf = io.BytesIO()
    rgb.save(buf, "JPEG", quality=quality); buf.seek(0)
    diff = ImageChops.difference(rgb, Image.open(buf))
    return ImageEnhance.Brightness(diff).enhance(scale)

def ela_heatmap(e: Image.Image) -> Image.Image:
    gray = cv2.cvtColor(np.array(e.convert("RGB")), cv2.COLOR_RGB2GRAY)
    return cv_to_pil(cv2.applyColorMap(gray, cv2.COLORMAP_JET))

def ela_stats(e: Image.Image):
    a = np.array(e.convert("RGB")).astype(float)
    mean = float(np.mean(a)); std = float(np.std(a))
    p95  = float(np.percentile(a, 95))
    prob = min(100.0, mean * 2.2)
    if   mean < 8:  v,c = "LIKELY AUTHENTIC",      "#22c55e"
    elif mean < 18: v,c = "MINOR EDITING POSSIBLE", "#84cc16"
    elif mean < 30: v,c = "POSSIBLY EDITED",        "#facc15"
    elif mean < 45: v,c = "SUSPICIOUS / EDITED",    "#f97316"
    else:           v,c = "LIKELY MANIPULATED",     "#ef4444"
    return mean, std, p95, prob, v, c

def ela_region_detect(img: Image.Image, e: Image.Image,
                      thresh=20, min_area=300):
    out  = pil_to_cv(img)
    gray = cv2.cvtColor(np.array(e.convert("RGB")), cv2.COLOR_RGB2GRAY)
    _, th = cv2.threshold(gray, thresh, 255, cv2.THRESH_BINARY)
    k    = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
    th   = cv2.morphologyEx(th, cv2.MORPH_CLOSE, k, iterations=2)
    cnts, _ = cv2.findContours(th, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    n = 0
    for c in cnts:
        if cv2.contourArea(c) > min_area:
            x,y,w,h = cv2.boundingRect(c)
            cv2.rectangle(out,(x,y),(x+w,y+h),(0,0,255),2)
            cv2.putText(out,f"#{n+1}",(x+4,y+18),
                        cv2.FONT_HERSHEY_SIMPLEX,.55,(0,0,255),1)
            n += 1
    cv2.putText(out,f"Suspicious: {n}",(8,22),
                cv2.FONT_HERSHEY_SIMPLEX,.6,(0,255,156),2)
    return cv_to_pil(out), n


# ══════════════════════════════════════════════════════════════════════
# ── MODULE 2 · CLONE / COPY-MOVE ─────────────────────────────────────
# ══════════════════════════════════════════════════════════════════════
def clone_detect(img: Image.Image):
    gray = cv2.cvtColor(np.array(img.convert("RGB")), cv2.COLOR_RGB2GRAY)
    orb  = cv2.ORB_create(nfeatures=8000)
    kp, des = orb.detectAndCompute(gray, None)
    out  = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)
    if des is None or len(kp) < 10:
        return cv_to_pil(out), 0
    bf   = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
    seen = set(); n = 0
    for m in sorted(bf.match(des,des), key=lambda x:x.distance):
        qi, ti = m.queryIdx, m.trainIdx
        if qi == ti: continue
        key = (min(qi,ti),max(qi,ti))
        if key in seen: continue
        seen.add(key)
        p1 = tuple(map(int, kp[qi].pt))
        p2 = tuple(map(int, kp[ti].pt))
        if math.hypot(p1[0]-p2[0],p1[1]-p2[1]) > 20:
            cv2.line(out, p1, p2, (0,255,100), 1)
            cv2.circle(out, p1, 3, (0,200,255), -1)
            cv2.circle(out, p2, 3, (255,80,0),  -1)
            n += 1
        if n >= 40: break
    cv2.putText(out,f"Clone pairs: {n}",(8,22),
                cv2.FONT_HERSHEY_SIMPLEX,.6,(0,255,156),2)
    return cv_to_pil(out), n


# ══════════════════════════════════════════════════════════════════════
# ── MODULE 3 · NOISE RESIDUAL ─────────────────────────────────────────
# ══════════════════════════════════════════════════════════════════════
def _noise_sigma_mad(arr: np.ndarray) -> float:
    """Estimate noise sigma via Median Absolute Deviation on the Laplacian.
    Pure numpy — no skimage.restoration dependency."""
    sigmas = []
    for c in range(arr.shape[2]):
        lap = cv2.Laplacian(arr[:,:,c], cv2.CV_32F)
        mad = float(np.median(np.abs(lap - np.median(lap))))
        sigmas.append(mad / 0.6745)
    return float(np.mean(sigmas))

def noise_residual(img: Image.Image):
    arr  = np.array(img.convert("RGB")).astype(np.float32)
    blur = cv2.GaussianBlur(arr,(5,5),0)
    res  = np.clip(np.abs(arr-blur)*4,0,255).astype(np.uint8)
    sig  = _noise_sigma_mad(arr)
    heat = cv2.applyColorMap(cv2.cvtColor(res,cv2.COLOR_RGB2GRAY), cv2.COLORMAP_HOT)
    cv2.putText(heat,f"σ={sig:.2f}",(8,22),cv2.FONT_HERSHEY_SIMPLEX,.6,(0,255,156),2)
    return cv_to_pil(heat), sig


# ══════════════════════════════════════════════════════════════════════
# ── MODULE 4 · EDGE ANALYSIS ─────────────────────────────────────────
# ══════════════════════════════════════════════════════════════════════
def edge_analysis(img: Image.Image):
    gray  = cv2.cvtColor(np.array(img.convert("RGB")),cv2.COLOR_RGB2GRAY)
    edges = cv2.Canny(cv2.GaussianBlur(gray,(3,3),0), 80, 180)
    density = float(np.count_nonzero(edges))/edges.size*100
    out   = np.zeros((*edges.shape,3),dtype=np.uint8)
    out[edges>0] = [0,255,156]
    cv2.putText(out,f"Density: {density:.1f}%",(8,22),
                cv2.FONT_HERSHEY_SIMPLEX,.6,(255,200,0),2)
    return cv_to_pil(out), density


# ══════════════════════════════════════════════════════════════════════
# ── MODULE 5 · FFT FREQUENCY SPECTRUM ────────────────────────────────
# ══════════════════════════════════════════════════════════════════════
def fft_analysis(img: Image.Image) -> Image.Image:
    gray = cv2.cvtColor(np.array(img.convert("RGB")),cv2.COLOR_RGB2GRAY).astype(np.float32)
    mag  = 20*np.log1p(np.abs(np.fft.fftshift(np.fft.fft2(gray))))
    norm = cv2.normalize(mag,None,0,255,cv2.NORM_MINMAX).astype(np.uint8)
    return cv_to_pil(cv2.applyColorMap(norm, cv2.COLORMAP_INFERNO))


# ══════════════════════════════════════════════════════════════════════
# ── MODULE 6 · DCT BLOCK ANALYSIS ────────────────────────────────────
# ══════════════════════════════════════════════════════════════════════
def dct_analysis(img: Image.Image):
    gray = cv2.cvtColor(np.array(img.convert("RGB")),cv2.COLOR_RGB2GRAY).astype(np.float32)
    h,w  = gray.shape
    bh,bw = h-h%8, w-w%8
    gray  = gray[:bh,:bw]
    emap  = np.zeros_like(gray)
    bmeans = []
    for r in range(0,bh,8):
        for cc in range(0,bw,8):
            blk = gray[r:r+8,cc:cc+8]
            d   = cv2.dct(blk)
            e   = float(np.log1p(np.abs(d)).mean())
            emap[r:r+8,cc:cc+8] = e
            bmeans.append(e)
    score = float(np.std(bmeans))
    norm  = cv2.normalize(emap,None,0,255,cv2.NORM_MINMAX).astype(np.uint8)
    heat  = cv2.applyColorMap(norm, cv2.COLORMAP_PLASMA)
    cv2.putText(heat,f"DCT inconsistency: {score:.2f}",(8,22),
                cv2.FONT_HERSHEY_SIMPLEX,.55,(0,255,156),2)
    return cv_to_pil(heat), score


# ══════════════════════════════════════════════════════════════════════
# ── MODULE 7 · LBP TEXTURE ───────────────────────────────────────────
# ══════════════════════════════════════════════════════════════════════
def lbp_analysis(img: Image.Image) -> Image.Image:
    gray = cv2.cvtColor(np.array(img.convert("RGB")),cv2.COLOR_RGB2GRAY)
    lbp  = local_binary_pattern(gray, P=8, R=1.0, method="uniform")
    norm = cv2.normalize(lbp,None,0,255,cv2.NORM_MINMAX).astype(np.uint8)
    return cv_to_pil(cv2.applyColorMap(norm, cv2.COLORMAP_TWILIGHT_SHIFTED))


# ══════════════════════════════════════════════════════════════════════
# ── MODULE 8 · JPEG GHOST ────────────────────────────────────────────
# ══════════════════════════════════════════════════════════════════════
def jpeg_ghost(img: Image.Image, qualities=(50,70,85,95)) -> Image.Image:
    orig = np.array(img.convert("RGB")).astype(np.float32)
    maps = []
    for q in qualities:
        buf = io.BytesIO()
        img.convert("RGB").save(buf,"JPEG",quality=q); buf.seek(0)
        comp = np.array(Image.open(buf)).astype(np.float32)
        maps.append(np.abs(orig-comp).mean(axis=2))
    norm = cv2.normalize(np.mean(maps,axis=0),None,0,255,cv2.NORM_MINMAX).astype(np.uint8)
    return cv_to_pil(cv2.applyColorMap(norm, cv2.COLORMAP_OCEAN))


# ══════════════════════════════════════════════════════════════════════
# ── MODULE 9 · LUMINANCE GRADIENT ────────────────────────────────────
# ══════════════════════════════════════════════════════════════════════
def luminance_gradient(img: Image.Image) -> Image.Image:
    gray = cv2.cvtColor(np.array(img.convert("RGB")),cv2.COLOR_RGB2GRAY).astype(np.float32)
    mag  = cv2.magnitude(cv2.Sobel(gray,cv2.CV_32F,1,0,ksize=3),
                         cv2.Sobel(gray,cv2.CV_32F,0,1,ksize=3))
    norm = cv2.normalize(mag,None,0,255,cv2.NORM_MINMAX).astype(np.uint8)
    return cv_to_pil(cv2.applyColorMap(norm, cv2.COLORMAP_MAGMA))


# ══════════════════════════════════════════════════════════════════════
# ── MODULE 10 · RGB HISTOGRAM ────────────────────────────────────────
# ══════════════════════════════════════════════════════════════════════
def histogram_plot(img: Image.Image) -> Image.Image:
    arr = np.array(img.convert("RGB"))
    fig, ax = dark_fig(5,3)
    for name,idx,col in [("R",0,"#ff4444"),("G",1,"#44ff88"),("B",2,"#4488ff")]:
        ax.plot(cv2.calcHist([arr],[idx],None,[256],[0,256]).flatten(),
                color=col, alpha=.85, lw=1.2, label=name)
    ax.legend(facecolor="#111",edgecolor="#00ff9c",labelcolor="#fff",fontsize=8)
    ax.set_xlim(0,255); ax.set_title("RGB Histogram",color="#00ff9c",fontsize=10)
    return fig_to_pil(fig)


# ══════════════════════════════════════════════════════════════════════
# ── MODULE 11 · STEGANOGRAPHY DETECTION ──────────────────────────────
# ══════════════════════════════════════════════════════════════════════
def steg_lsb_planes(img: Image.Image):
    """Extract all 8 bit-planes per channel and visualise the LSB plane."""
    arr  = np.array(img.convert("RGB"))
    # LSB plane (bit 0)
    lsb  = (arr & 1) * 255
    out  = lsb.astype(np.uint8)
    return Image.fromarray(out)

def steg_chi_square(img: Image.Image):
    """
    Chi-square attack on LSB steganography.
    Returns (score, p_value, is_suspicious, message).
    High chi-square score → uniform LSB distribution → hidden data likely.
    """
    arr  = np.array(img.convert("RGB")).flatten()
    # pair of value groups: (0,1),(2,3),(4,5),...
    scores = []
    for ch_start in range(0, len(arr), len(arr)//3):
        ch = arr[ch_start:ch_start+len(arr)//3]
        observed = np.bincount(ch, minlength=256).astype(float)
        # Chi-square on even/odd pairs
        pairs_obs = []
        pairs_exp = []
        for i in range(0, 256, 2):
            total = observed[i]+observed[i+1]
            pairs_obs.extend([observed[i], observed[i+1]])
            pairs_exp.extend([total/2, total/2])
        pairs_obs = np.array(pairs_obs)
        pairs_exp = np.array(pairs_exp)
        mask = pairs_exp > 0
        chi2 = float(np.sum((pairs_obs[mask]-pairs_exp[mask])**2/pairs_exp[mask]))
        scores.append(chi2)
    avg_chi2 = float(np.mean(scores))
    # normalise to 0-100 suspicion score (lower chi2 = more suspicious)
    susp = max(0.0, 100.0 - min(avg_chi2/5000*100, 100))
    suspicious = susp > 60
    return avg_chi2, susp, suspicious

def steg_entropy_map(img: Image.Image) -> Image.Image:
    """Local entropy map — high entropy blobs in LSB plane indicate hidden data."""
    gray = cv2.cvtColor(np.array(img.convert("RGB")),cv2.COLOR_RGB2GRAY)
    lsb  = (gray & 1).astype(np.float32)
    # sliding window entropy via uniform filter on squared values
    emap = np.zeros_like(lsb)
    win  = 16
    p    = uniform_filter(lsb, size=win)
    p    = np.clip(p, 1e-7, 1.0 - 1e-7)  # keep away from 0/1 boundaries
    with np.errstate(divide="ignore", invalid="ignore"):
        emap = -(p * np.log2(p) + (1 - p) * np.log2(1 - p))
    emap = np.nan_to_num(emap, nan=0.0, posinf=0.0, neginf=0.0).astype(np.float32)
    norm = cv2.normalize(emap, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)
    heat = cv2.applyColorMap(norm, cv2.COLORMAP_VIRIDIS)
    return cv_to_pil(heat)

def steg_bit_planes(img: Image.Image) -> Image.Image:
    """Show all 8 bit-planes of the grayscale image in a grid."""
    gray = cv2.cvtColor(np.array(img.convert("RGB")),cv2.COLOR_RGB2GRAY)
    fig, axes = plt.subplots(2,4,figsize=(10,5),facecolor="#000")
    for bit in range(8):
        ax = axes[bit//4][bit%4]
        plane = ((gray >> bit) & 1)*255
        ax.imshow(plane, cmap="gray", vmin=0, vmax=255)
        ax.set_title(f"Bit {bit}", color="#00ff9c", fontsize=9)
        ax.axis("off")
        ax.set_facecolor("#000")
    fig.patch.set_facecolor("#000")
    plt.tight_layout()
    return fig_to_pil(fig)


# ══════════════════════════════════════════════════════════════════════
# ── MODULE 12 · METADATA TAMPERING TIMELINE ──────────────────────────
# ══════════════════════════════════════════════════════════════════════
def extract_exif_full(img: Image.Image) -> dict:
    try:
        raw = img._getexif()
        if not raw: return {}
        out = {}
        for tid, val in raw.items():
            tag = ExifTags.TAGS.get(tid, str(tid))
            if isinstance(val, bytes):
                try:    val = val.decode("utf-8","replace")
                except: val = val.hex()
            out[tag] = str(val)[:300]
        return out
    except Exception:
        return {}

def metadata_timeline(exif: dict) -> tuple:
    """
    Cross-check EXIF dates and software fields for inconsistencies.
    Returns (events list, anomalies list, risk_score 0-100).
    """
    DATE_TAGS   = ["DateTime","DateTimeOriginal","DateTimeDigitized",
                   "GPSDateStamp","CreateDate","ModifyDate"]
    SW_TAGS     = ["Software","ProcessingSoftware","HostComputer"]
    EDITING_KW  = ["photoshop","lightroom","gimp","affinity","capture",
                   "adobe","snapseed","vsco","pixelmator","paint.net",
                   "darktable","rawtherapee","luminar","canva"]

    events    = []
    anomalies = []
    dates     = {}
    software  = []

    for tag in DATE_TAGS:
        if tag in exif:
            val = exif[tag].strip()
            events.append({"tag": tag, "value": val, "type": "date"})
            try:
                # EXIF datetime: "YYYY:MM:DD HH:MM:SS"
                dt = datetime.strptime(val[:19], "%Y:%m:%d %H:%M:%S")
                dates[tag] = dt
            except Exception:
                pass

    for tag in SW_TAGS:
        if tag in exif:
            val = exif[tag].strip()
            software.append(val)
            events.append({"tag": tag, "value": val, "type": "software"})

    # GPS
    if "GPSInfo" in exif:
        events.append({"tag":"GPSInfo","value":"GPS coordinates present","type":"gps"})

    # Anomaly: editing software detected
    for sw in software:
        for kw in EDITING_KW:
            if kw in sw.lower():
                anomalies.append(f"Editing software detected: '{sw}'")
                break

    # Anomaly: date inconsistencies
    if len(dates) >= 2:
        vals = list(dates.values())
        for i in range(len(vals)):
            for j in range(i+1, len(vals)):
                diff = abs((vals[i]-vals[j]).total_seconds())
                if diff > 86400:  # >1 day difference
                    anomalies.append(
                        f"Date mismatch: {list(dates.keys())[i]} vs "
                        f"{list(dates.keys())[j]} differ by "
                        f"{diff/3600:.1f} hours")

    # Anomaly: future dates
    now_naive = datetime.now()  # naive, matches EXIF parsed datetimes
    for tag, dt in dates.items():
        if dt > now_naive:
            anomalies.append(f"Future date in {tag}: {dt}")

    # Anomaly: year 1970 / epoch
    for tag, dt in dates.items():
        if dt.year < 2000:
            anomalies.append(f"Suspicious early date in {tag}: {dt.year}")

    # Risk score
    risk = min(100, len(anomalies)*25 + (10 if software else 0))
    return events, anomalies, risk


# ══════════════════════════════════════════════════════════════════════
# ── MODULE 13 · SPLICING BOUNDARY DETECTION ──────────────────────────
# ══════════════════════════════════════════════════════════════════════
def splicing_boundary(img: Image.Image) -> tuple:
    """
    Detect splicing boundaries using:
    1. Noise inconsistency map (block-wise σ)
    2. Illumination gradient discontinuity
    3. Combined heatmap
    Returns (heatmap_pil, splice_score 0-100)
    """
    arr  = np.array(img.convert("RGB")).astype(np.float32)
    gray = cv2.cvtColor(arr.astype(np.uint8), cv2.COLOR_RGB2GRAY).astype(np.float32)
    h, w = gray.shape

    # ── Block-wise noise sigma map ──────────────────────────────────
    bsize  = 32
    nmap   = np.zeros((h, w), dtype=np.float32)
    sigmas = []
    for r in range(0, h-bsize, bsize//2):
        for cc in range(0, w-bsize, bsize//2):
            blk = gray[r:r+bsize, cc:cc+bsize]
            # noise estimate: median absolute deviation of Laplacian
            lap = cv2.Laplacian(blk, cv2.CV_32F)
            s   = float(np.median(np.abs(lap - np.median(lap)))) / 0.6745
            nmap[r:r+bsize, cc:cc+bsize] = s
            sigmas.append(s)

    # ── Illumination map (local mean luminance) ─────────────────────
    illum  = cv2.GaussianBlur(gray, (31,31), 0)
    # gradient of illumination
    gx = cv2.Sobel(illum, cv2.CV_32F, 1, 0, ksize=5)
    gy = cv2.Sobel(illum, cv2.CV_32F, 0, 1, ksize=5)
    illum_grad = cv2.magnitude(gx, gy)

    # ── Combine ─────────────────────────────────────────────────────
    noise_norm  = cv2.normalize(nmap,       None, 0, 1, cv2.NORM_MINMAX)
    illum_norm  = cv2.normalize(illum_grad, None, 0, 1, cv2.NORM_MINMAX)
    combined    = (noise_norm * 0.6 + illum_norm * 0.4)
    combined_n  = cv2.normalize(combined,   None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)
    heat        = cv2.applyColorMap(combined_n, cv2.COLORMAP_JET)

    # splice score: std of block sigmas (high std = inconsistent noise = spliced)
    splice_score = min(100.0, float(np.std(sigmas)) * 15)

    cv2.putText(heat, f"Splice score: {splice_score:.1f}",
                (8,22), cv2.FONT_HERSHEY_SIMPLEX, .6, (0,255,156), 2)
    return cv_to_pil(heat), splice_score


# ══════════════════════════════════════════════════════════════════════
# ── MODULE 14 · GAN / AI ARTIFACT DETECTION ──────────────────────────
# ══════════════════════════════════════════════════════════════════════
def gan_checkerboard(img: Image.Image):
    """
    Detect checkerboard artifacts in FFT — hallmark of transposed-convolution
    GAN generators (DCGAN, StyleGAN upsampling artefacts).
    Returns (annotated_fft_pil, cb_score 0-100, peaks_found int).
    """
    gray = cv2.cvtColor(np.array(img.convert("RGB")),cv2.COLOR_RGB2GRAY).astype(np.float32)
    f    = np.fft.fftshift(np.fft.fft2(gray))
    mag  = np.log1p(np.abs(f))
    h, w = mag.shape
    cx, cy = w//2, h//2

    # Normalise for display
    disp = cv2.normalize(mag,None,0,255,cv2.NORM_MINMAX).astype(np.uint8)
    heat = cv2.applyColorMap(disp, cv2.COLORMAP_INFERNO)

    # Look for periodic peaks at N/2, N/4 frequencies (GAN checkerboard)
    # Sample horizontal and vertical lines through centre
    h_line = mag[cy, :]
    v_line = mag[:, cx]
    peaks_found = 0
    cb_score    = 0.0

    for line in [h_line, v_line]:
        half  = len(line)//2
        # Check N/2 frequency spike
        n2    = half//2
        local = line[max(0,n2-3):n2+3]
        surr  = np.concatenate([line[max(0,n2-20):max(0,n2-4)],
                                 line[n2+4:n2+20]])
        if len(surr) > 0 and local.max() > surr.mean()*1.5:
            peaks_found += 1
            cv2.line(heat,(0,cy),(w,cy),(0,255,156),1)
            cv2.line(heat,(cx,0),(cx,h),(0,255,156),1)

    cb_score = min(100.0, peaks_found * 35.0 + float(np.std(mag))*0.5)
    cv2.putText(heat,f"GAN CB score: {cb_score:.1f}",
                (8,22),cv2.FONT_HERSHEY_SIMPLEX,.55,(0,255,156),2)
    return cv_to_pil(heat), cb_score, peaks_found

def gan_texture_variance(img: Image.Image):
    """
    GAN-generated images tend to have unnaturally uniform texture.
    Measure local variance map and its global std.
    Very low global std → suspiciously uniform → possible GAN.
    """
    gray  = cv2.cvtColor(np.array(img.convert("RGB")),cv2.COLOR_RGB2GRAY).astype(np.float32)
    # Local variance via box filter
    mu    = uniform_filter(gray,    size=15)
    mu2   = uniform_filter(gray**2, size=15)
    var   = np.clip(mu2 - mu**2, 0, None)
    gstd  = float(np.std(var))
    norm  = cv2.normalize(var,None,0,255,cv2.NORM_MINMAX).astype(np.uint8)
    heat  = cv2.applyColorMap(norm, cv2.COLORMAP_COOL)
    # GAN score: low gstd = uniform texture = suspicious
    gan_score = max(0.0, min(100.0, 100.0 - gstd * 0.8))
    cv2.putText(heat,f"Texture uniformity: {gan_score:.1f}",
                (8,22),cv2.FONT_HERSHEY_SIMPLEX,.55,(0,255,156),2)
    return cv_to_pil(heat), gan_score

def gan_color_inconsistency(img: Image.Image):
    """
    Detect unnatural colour distribution — GAN images often have
    shifted chrominance histograms and low inter-channel correlation.
    """
    arr = np.array(img.convert("RGB")).astype(np.float32)
    r, g, b = arr[:,:,0].flatten(), arr[:,:,1].flatten(), arr[:,:,2].flatten()
    # Correlation between channels (real photos tend to be highly correlated)
    corr_rg = float(np.corrcoef(r,g)[0,1])
    corr_rb = float(np.corrcoef(r,b)[0,1])
    corr_gb = float(np.corrcoef(g,b)[0,1])
    avg_corr = (corr_rg+corr_rb+corr_gb)/3

    # Build colour histogram plot
    fig, axes = plt.subplots(1,3,figsize=(9,2.5),facecolor="#000")
    for ax,(ch,col,name) in zip(axes,[(r,"#ff4444","R"),(g,"#44ff88","G"),(b,"#4488ff","B")]):
        ax.hist(ch, bins=64, color=col, alpha=.8, histtype="stepfilled")
        ax.set_facecolor("#000"); ax.set_title(name,color=col,fontsize=9)
        for sp in ax.spines.values(): sp.set_edgecolor("#333")
        ax.tick_params(colors="#9affd7",labelsize=7)
    fig.suptitle(f"Channel correlation: {avg_corr:.3f}",color="#00ff9c",fontsize=10)
    plt.tight_layout()

    # Score: very low or very high correlation can indicate GAN
    gan_score = max(0.0, min(100.0, (1.0-abs(avg_corr))*120))
    return fig_to_pil(fig), gan_score, avg_corr

def gan_frequency_fingerprint(img: Image.Image):
    """
    Real images follow a 1/f power spectrum.
    GAN images deviate — check slope of radially averaged power spectrum.
    """
    gray = cv2.cvtColor(np.array(img.convert("RGB")),cv2.COLOR_RGB2GRAY).astype(np.float32)
    f    = np.fft.fftshift(np.fft.fft2(gray))
    power= np.abs(f)**2
    h,w  = power.shape
    cy,cx= h//2, w//2
    max_r= min(cx,cy)
    radial_power = []
    for r in range(1,max_r,2):
        mask = np.zeros((h,w),dtype=bool)
        cv2.circle(mask.view(np.uint8),( cx,cy),r,1,-1)
        cv2.circle(mask.view(np.uint8),(cx,cy),max(0,r-2),0,-1)
        if mask.sum()>0:
            radial_power.append(float(power[mask].mean()))

    if len(radial_power) < 10:
        return None, 0.0

    rp   = np.array(radial_power)
    freq = np.arange(1,len(rp)+1,dtype=float)
    log_f= np.log10(freq); log_p = np.log10(rp+1)
    # Linear fit — slope should be ~-2 to -3 for natural images
    slope,intercept = np.polyfit(log_f, log_p, 1)

    fig, ax = dark_fig(5,3)
    ax.plot(log_f, log_p, color="#00ff9c", lw=1.5, label="Power spectrum")
    ax.plot(log_f, slope*log_f+intercept, "--",color="#ff4444",lw=1,label=f"Fit slope={slope:.2f}")
    ax.set_xlabel("log10(frequency)"); ax.set_ylabel("log10(power)")
    ax.set_title("Radial Power Spectrum",color="#00ff9c",fontsize=10)
    ax.legend(facecolor="#111",edgecolor="#00ff9c",labelcolor="#fff",fontsize=8)

    # GAN score: slope significantly different from natural range (-1.5 to -3.5)
    gan_score = 0.0
    if slope > -1.0 or slope < -5.0:
        gan_score = min(100.0, abs(slope + 2.5)*30)
    return fig_to_pil(fig), gan_score


# ══════════════════════════════════════════════════════════════════════
# ── MODULE 15 · FACE / FACIAL LANDMARK ANALYSIS ──────────────────────
# ══════════════════════════════════════════════════════════════════════
def face_analysis_cv(img: Image.Image):
    """
    Face detection + eye asymmetry check using OpenCV Haar cascades.
    Works without mediapipe or dlib.
    Returns (annotated_pil, results_dict).
    """
    out  = pil_to_cv(img)
    gray = cv2.cvtColor(out, cv2.COLOR_BGR2GRAY)

    face_cascade = cv2.CascadeClassifier(
        cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
    eye_cascade  = cv2.CascadeClassifier(
        cv2.data.haarcascades + "haarcascade_eye.xml")

    faces = face_cascade.detectMultiScale(gray,1.1,5,minSize=(60,60))
    results = {"faces":len(faces),"eyes_per_face":[],"asymmetry_scores":[],
               "anomalies":[]}

    for (fx,fy,fw,fh) in faces:
        cv2.rectangle(out,(fx,fy),(fx+fw,fy+fh),(0,255,156),2)
        roi_gray = gray[fy:fy+fh, fx:fx+fw]
        roi_col  = out [fy:fy+fh, fx:fx+fw]
        eyes = eye_cascade.detectMultiScale(roi_gray,1.1,5,minSize=(20,20))
        results["eyes_per_face"].append(len(eyes))

        eye_centers = []
        for (ex,ey,ew,eh) in eyes:
            cv2.rectangle(roi_col,(ex,ey),(ex+ew,ey+eh),(255,100,0),1)
            eye_centers.append((ex+ew//2, ey+eh//2))

        # Eye asymmetry: vertical position difference
        if len(eye_centers)==2:
            ydiff = abs(eye_centers[0][1]-eye_centers[1][1])
            norm_ydiff = ydiff/fh*100
            results["asymmetry_scores"].append(norm_ydiff)
            if norm_ydiff > 8:
                results["anomalies"].append(
                    f"Eye vertical asymmetry: {norm_ydiff:.1f}% of face height")
            # Eye size comparison
            if len(eyes)==2:
                area0 = eyes[0][2]*eyes[0][3]
                area1 = eyes[1][2]*eyes[1][3]
                size_ratio = max(area0,area1)/max(min(area0,area1),1)
                if size_ratio > 1.6:
                    results["anomalies"].append(
                        f"Eye size ratio: {size_ratio:.2f}x (unusual)")

        cv2.putText(out,f"Face: {len(eyes)} eyes",
                    (fx,fy-8),cv2.FONT_HERSHEY_SIMPLEX,.5,(0,255,156),1)

    if len(faces)==0:
        cv2.putText(out,"No faces detected",(8,22),
                    cv2.FONT_HERSHEY_SIMPLEX,.6,(255,200,0),2)

    return cv_to_pil(out), results

def face_blending_boundary(img: Image.Image):
    """
    Detect face-swap blending seams using:
    - Local colour variance discontinuity around detected face boundary
    - High-pass filtered difference map
    """
    arr  = np.array(img.convert("RGB")).astype(np.float32)
    gray = cv2.cvtColor(arr.astype(np.uint8),cv2.COLOR_RGB2GRAY)

    # High-pass via unsharp masking
    blurred    = cv2.GaussianBlur(arr,(15,15),0)
    high_pass  = np.abs(arr - blurred)
    hp_gray    = high_pass.mean(axis=2)

    # Local std map
    local_mean = uniform_filter(hp_gray, size=20)
    local_sq   = uniform_filter(hp_gray**2, size=20)
    local_std  = np.sqrt(np.clip(local_sq-local_mean**2, 0, None))

    norm = cv2.normalize(local_std,None,0,255,cv2.NORM_MINMAX).astype(np.uint8)
    heat = cv2.applyColorMap(norm, cv2.COLORMAP_HOT)

    seam_score = min(100.0, float(np.std(local_std))*8)
    cv2.putText(heat,f"Seam score: {seam_score:.1f}",
                (8,22),cv2.FONT_HERSHEY_SIMPLEX,.6,(0,255,156),2)
    return cv_to_pil(heat), seam_score


# ══════════════════════════════════════════════════════════════════════
# ── MODULE 16 · PIXEL DIFF (single-image & two-image) ────────────────
# ══════════════════════════════════════════════════════════════════════
def pixel_diff(imgA: Image.Image, imgB: Image.Image, amplify=5):
    """Absolute pixel difference between two images (resized to match)."""
    sz = (min(imgA.width,imgB.width), min(imgA.height,imgB.height))
    a  = np.array(imgA.convert("RGB").resize(sz)).astype(np.int16)
    b  = np.array(imgB.convert("RGB").resize(sz)).astype(np.int16)
    diff = np.abs(a-b).astype(np.uint8)
    diff_amp = np.clip(diff*amplify,0,255).astype(np.uint8)
    mean_diff = float(np.mean(diff))
    heat = cv2.applyColorMap(
        cv2.cvtColor(diff_amp,cv2.COLOR_RGB2GRAY), cv2.COLORMAP_JET)
    cv2.putText(heat,f"Mean diff: {mean_diff:.2f}",
                (8,22),cv2.FONT_HERSHEY_SIMPLEX,.6,(0,255,156),2)
    return cv_to_pil(heat), mean_diff


# ══════════════════════════════════════════════════════════════════════
# ── MODULE 17 · FILE INFO & METADATA ─────────────────────────────────
# ══════════════════════════════════════════════════════════════════════
def file_info(uf, img: Image.Image) -> dict:
    data = uf.getvalue()
    sha, md5 = hash_bytes(data)
    return {
        "Filename"   : uf.name,
        "File size"  : f"{len(data)/1024:.1f} KB",
        "Format"     : img.format or "Unknown",
        "Mode"       : img.mode,
        "Resolution" : f"{img.width} × {img.height} px",
        "Megapixels" : f"{img.width*img.height/1e6:.2f} MP",
        "SHA-256"    : sha,
        "MD5"        : md5,
    }


# ══════════════════════════════════════════════════════════════════════
# ── MODULE 18 · COMPOSITE SCORE + RADAR CHART ────────────────────────
# ══════════════════════════════════════════════════════════════════════
def composite_score(ela_prob, clone_pairs, dct_score,
                    noise_sigma, edge_density, splice_score,
                    steg_susp, gan_cb, face_seam):
    w = {
        "ELA":       (0.25, min(ela_prob,       100)),
        "Clone":     (0.15, min(clone_pairs*2.5,100)),
        "DCT":       (0.12, min(dct_score*1.5,  100)),
        "Noise":     (0.08, min(noise_sigma*2,  100)),
        "Splice":    (0.15, min(splice_score,   100)),
        "Steg":      (0.10, min(steg_susp,      100)),
        "GAN":       (0.08, min(gan_cb,         100)),
        "FaceSeam":  (0.07, min(face_seam,      100)),
    }
    score = sum(wt*val for wt,val in w.values())
    return min(100.0, score), {k: v[1] for k,v in w.items()}

def verdict_from_score(s):
    if   s < 15: return "AUTHENTIC",          "#22c55e"
    elif s < 35: return "LIKELY AUTHENTIC",   "#84cc16"
    elif s < 55: return "INCONCLUSIVE",        "#facc15"
    elif s < 75: return "SUSPICIOUS",          "#f97316"
    else:        return "LIKELY MANIPULATED",  "#ef4444"

def radar_chart(scores: dict, label: str) -> go.Figure:
    cats = list(scores.keys())
    vals = [scores[k] for k in cats]
    vals_closed = vals + [vals[0]]
    cats_closed = cats + [cats[0]]
    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=vals_closed, theta=cats_closed,
        fill="toself",
        fillcolor="rgba(0,255,156,0.15)",
        line=dict(color="#00ff9c", width=2),
        name=label,
    ))
    fig.update_layout(
        polar=dict(
            radialaxis=dict(visible=True, range=[0,100],
                            tickfont=dict(color="#9affd7",size=9),
                            gridcolor="rgba(0,255,156,0.2)"),
            angularaxis=dict(tickfont=dict(color="#00ff9c",size=10),
                             gridcolor="rgba(0,255,156,0.13)"),
            bgcolor="#000",
        ),
        paper_bgcolor="#000",
        plot_bgcolor="#000",
        showlegend=False,
        margin=dict(l=30,r=30,t=40,b=30),
        title=dict(text=label,font=dict(color="#00ff9c",size=13)),
    )
    return fig


# ══════════════════════════════════════════════════════════════════════
# ── MODULE 19 · CHAIN-OF-CUSTODY LOG ─────────────────────────────────
# ══════════════════════════════════════════════════════════════════════
class CustodyLog:
    def __init__(self):
        self.entries = []

    def add(self, action: str, detail: str = ""):
        self.entries.append({
            "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S.%f UTC"),
            "action":    action,
            "detail":    detail,
        })

    def to_text(self) -> str:
        lines = ["╔══ CHAIN OF CUSTODY LOG ══════════════════════════════════╗",
                 "║  Psychomods Cyber Forensic Lab v3.0                      ║",
                 "╚══════════════════════════════════════════════════════════╝",""]
        for e in self.entries:
            lines.append(f"[{e['timestamp']}]  {e['action']}")
            if e["detail"]:
                lines.append(f"    ↳ {e['detail']}")
        return "\n".join(lines)

    def to_json(self) -> str:
        return json.dumps(self.entries, indent=2)


# ══════════════════════════════════════════════════════════════════════
# ── MODULE 20 · PDF REPORT ────────────────────────────────────────────
# ══════════════════════════════════════════════════════════════════════
def build_pdf(label_a, label_b, info_a, info_b,
              stats_a, stats_b, anomalies_a, anomalies_b,
              custody_log: str) -> io.BytesIO:
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4,
                            leftMargin=18*mm, rightMargin=18*mm,
                            topMargin=18*mm, bottomMargin=18*mm)
    G   = rl_colors.HexColor("#007744")
    BK  = rl_colors.HexColor("#111")
    styles = getSampleStyleSheet()
    T  = ParagraphStyle("T",  fontName="Helvetica-Bold",   fontSize=20, textColor=G,   alignment=1, spaceAfter=4)
    S  = ParagraphStyle("S",  fontName="Helvetica",        fontSize=10, textColor=rl_colors.grey, alignment=1, spaceAfter=12)
    H2 = ParagraphStyle("H2", fontName="Helvetica-Bold",   fontSize=13, textColor=G,   spaceBefore=10, spaceAfter=4)
    BD = ParagraphStyle("BD", fontName="Helvetica",        fontSize=9,  textColor=BK,  spaceAfter=3,   leading=13)
    WN = ParagraphStyle("WN", fontName="Helvetica-Oblique",fontSize=9,  textColor=rl_colors.HexColor("#cc5500"), spaceAfter=3)
    OK = ParagraphStyle("OK", fontName="Helvetica-Oblique",fontSize=9,  textColor=rl_colors.HexColor("#007744"), spaceAfter=3)

    story = []
    story.append(Paragraph("🧠 PSYCHOMODS CYBER FORENSIC LAB", T))
    story.append(Paragraph("Advanced Image Manipulation Detection Report — v3.0", S))
    story.append(Paragraph(f"Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}", S))
    story.append(HRFlowable(width="100%", thickness=1, color=G))
    story.append(Spacer(1,8))

    def img_section(label, info, stats, anomalies):
        story.append(Paragraph(f"► {label}", H2))
        story.append(HRFlowable(width="60%", thickness=.5, color=G))
        story.append(Spacer(1,4))
        # Info table (skip if empty — single-image mode)
        if info:
            td = [[Paragraph(f"<b>{k}</b>",BD), Paragraph(v,BD)] for k,v in info.items()]
            t  = Table(td, colWidths=[55*mm,115*mm])
            t.setStyle(TableStyle([
                ("BACKGROUND",(0,0),(0,-1),rl_colors.HexColor("#e8fff5")),
                ("GRID",(0,0),(-1,-1),.3,rl_colors.HexColor("#aaddcc")),
                ("ROWBACKGROUNDS",(0,0),(-1,-1),[rl_colors.HexColor("#f0fff8"),rl_colors.white]),
            ])); story.append(t); story.append(Spacer(1,8))
        # Stats table (skip if empty)
        if stats:
            story.append(Paragraph("Forensic Metrics", H2))
            sd = [[Paragraph(f"<b>{k}</b>",BD), Paragraph(str(v),BD)] for k,v in stats.items()]
            t2 = Table(sd, colWidths=[75*mm,95*mm])
            t2.setStyle(TableStyle([
                ("BACKGROUND",(0,0),(0,-1),rl_colors.HexColor("#e8fff5")),
                ("GRID",(0,0),(-1,-1),.3,rl_colors.HexColor("#aaddcc")),
                ("ROWBACKGROUNDS",(0,0),(-1,-1),[rl_colors.HexColor("#f0fff8"),rl_colors.white]),
            ])); story.append(t2); story.append(Spacer(1,8))
        # Anomalies
        if anomalies:
            story.append(Paragraph("⚠️ Anomalies Detected", H2))
            for a in anomalies:
                story.append(Paragraph(f"• {a}", WN))
        else:
            story.append(Paragraph("✓ No anomalies detected", OK))
        story.append(Spacer(1,12))

    img_section(label_a, info_a, stats_a, anomalies_a)
    img_section(label_b, info_b, stats_b, anomalies_b)

    # Custody log (truncated)
    story.append(HRFlowable(width="100%",thickness=1,color=G))
    story.append(Paragraph("Chain of Custody Log", H2))
    for line in custody_log.split("\n")[:40]:
        story.append(Paragraph(line or " ", BD))

    story.append(Spacer(1,8))
    story.append(HRFlowable(width="100%",thickness=.5,color=G))
    story.append(Paragraph(
        "DISCLAIMER: Algorithmic results only. Validate with a certified examiner before legal use.",
        ParagraphStyle("disc",fontName="Helvetica-Oblique",fontSize=8,textColor=rl_colors.grey)))
    story.append(Paragraph(
        "Psychomods Cyber Security Tools | https://psychomods.infy.uk",
        ParagraphStyle("foot",fontName="Helvetica",fontSize=8,textColor=G,alignment=1)))

    doc.build(story); buf.seek(0)
    return buf


# ══════════════════════════════════════════════════════════════════════
# ── MODULE 21 · ZIP EVIDENCE PACKAGE ─────────────────────────────────
# ══════════════════════════════════════════════════════════════════════
def build_zip(pdf_buf, txt_report, custody_json, images: dict) -> io.BytesIO:
    zb = io.BytesIO()
    with zipfile.ZipFile(zb, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("forensic_report.pdf",  pdf_buf.getvalue())
        zf.writestr("forensic_report.txt",  txt_report)
        zf.writestr("chain_of_custody.json",custody_json)
        for name, pil_img in images.items():
            ib = io.BytesIO()
            pil_img.save(ib,"PNG"); ib.seek(0)
            zf.writestr(f"analysis_images/{name}.png", ib.getvalue())
    zb.seek(0); return zb


# ══════════════════════════════════════════════════════════════════════
# SIDEBAR
# ══════════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("### ⚙️ Settings")
    mode = st.radio("Analysis Mode",
                    ["🔁 Two-Image Compare","📷 Single Image","📦 Batch (up to 10)"],
                    index=0)
    st.markdown("---")
    ela_q   = st.slider("ELA JPEG Quality",   60, 98, 92)
    ela_s   = st.slider("ELA Amplification",   5, 40, 20)
    ela_t   = st.slider("Region Threshold",    5, 80, 20)
    min_a   = st.slider("Min Region Area px", 50,2000,300,50)
    diff_amp= st.slider("Pixel Diff Amplify",  1, 20,  5)
    st.markdown("---")
    st.markdown("""
**v3.0 Modules**
1. ELA + Heatmap
2. Region Detection
3. Clone/Copy-Move
4. Noise Residual
5. Edge Analysis
6. FFT Spectrum
7. DCT Block Analysis
8. LBP Texture
9. JPEG Ghost
10. Luminance Gradient
11. Histogram
12. **Steganography (LSB)**
13. **Metadata Timeline**
14. **Splicing Boundary**
15. **GAN/AI Artifact**
16. **Face Analysis**
17. **Pixel Diff**
18. **Composite + Radar**
19. **Chain of Custody**
20. **ZIP Evidence Export**

[🌐 psychomods.infy.uk](https://psychomods.infy.uk)
""")


# ══════════════════════════════════════════════════════════════════════
# HELPER: run full pipeline on a single image
# ══════════════════════════════════════════════════════════════════════
def run_pipeline(img: Image.Image, label: str, uf=None,
                 log: CustodyLog = None, prog=None, base=0, span=100):

    def tick(pct, msg):
        if prog: prog.progress(base + int(pct*span/100), msg)
        if log:  log.add(msg, label)

    results = {}
    imgs    = {}

    tick(2,  "ELA…")
    e   = ela(img, ela_q, ela_s)
    em  = ela_heatmap(e)
    er, n_regions = ela_region_detect(img, e, ela_t, min_a)
    mean,std,p95,prob,verdict,color = ela_stats(e)
    results["ela"]    = dict(mean=mean,std=std,p95=p95,prob=prob,
                              verdict=verdict,color=color,n_regions=n_regions)
    imgs["ela"] = e; imgs["ela_heat"] = em; imgs["ela_regions"] = er

    tick(12, "Clone detection…")
    cl_img, cp = clone_detect(img)
    results["clone"] = dict(pairs=cp)
    imgs["clone"] = cl_img

    tick(22, "Noise residual…")
    nr_img, sig = noise_residual(img)
    results["noise"] = dict(sigma=sig)
    imgs["noise"] = nr_img

    tick(30, "Edge analysis…")
    ed_img, dens = edge_analysis(img)
    results["edge"] = dict(density=dens)
    imgs["edge"] = ed_img

    tick(36, "FFT…")
    imgs["fft"] = fft_analysis(img)

    tick(42, "DCT…")
    dct_img, dct_s = dct_analysis(img)
    results["dct"] = dict(score=dct_s)
    imgs["dct"] = dct_img

    tick(48, "LBP texture…")
    imgs["lbp"] = lbp_analysis(img)

    tick(52, "JPEG ghost…")
    imgs["jpeg_ghost"] = jpeg_ghost(img)

    tick(56, "Luminance gradient…")
    imgs["lum_grad"] = luminance_gradient(img)

    tick(60, "Histogram…")
    imgs["histogram"] = histogram_plot(img)

    tick(64, "Steganography…")
    steg_lsb = steg_lsb_planes(img)
    steg_ent = steg_entropy_map(img)
    steg_bp  = steg_bit_planes(img)
    chi2, steg_susp, steg_flag = steg_chi_square(img)
    results["steg"] = dict(chi2=chi2,susp=steg_susp,flag=steg_flag)
    imgs["steg_lsb"] = steg_lsb; imgs["steg_entropy"] = steg_ent
    imgs["steg_bitplanes"] = steg_bp

    tick(70, "Metadata timeline…")
    exif_data    = extract_exif_full(img)
    events, anomalies, meta_risk = metadata_timeline(exif_data)
    results["meta"] = dict(events=events,anomalies=anomalies,risk=meta_risk)

    tick(76, "Splicing boundary…")
    spl_img, spl_s = splicing_boundary(img)
    results["splice"] = dict(score=spl_s)
    imgs["splicing"] = spl_img

    tick(82, "GAN/AI artifact detection…")
    gan_fft_img, cb_score, cb_peaks = gan_checkerboard(img)
    gan_tex_img, tex_score          = gan_texture_variance(img)
    gan_col_img, col_score, ch_corr = gan_color_inconsistency(img)
    gan_pow_img, pow_score          = gan_frequency_fingerprint(img)
    gan_score = (cb_score*0.35 + tex_score*0.25 +
                 col_score*0.20 + (pow_score or 0)*0.20)
    results["gan"] = dict(cb=cb_score,texture=tex_score,
                           color=col_score,power=pow_score or 0,
                           score=gan_score,corr=ch_corr)
    imgs["gan_fft"] = gan_fft_img; imgs["gan_tex"] = gan_tex_img
    imgs["gan_col"] = gan_col_img
    if gan_pow_img: imgs["gan_pow"] = gan_pow_img

    tick(90, "Face analysis…")
    face_img, face_res     = face_analysis_cv(img)
    seam_img, seam_score   = face_blending_boundary(img)
    results["face"]  = dict(data=face_res, seam=seam_score)
    imgs["face"] = face_img; imgs["face_seam"] = seam_img

    tick(95, "Composite score…")
    comp, sub = composite_score(
        prob, cp, dct_s, sig, dens,
        spl_s, steg_susp, cb_score, seam_score)
    fv, fc = verdict_from_score(comp)
    results["composite"] = dict(score=comp,sub=sub,verdict=fv,color=fc)

    if uf:
        info = file_info(uf, img)
    else:
        info = {"Label": label}
    results["info"] = info

    tick(100, "Done.")
    return results, imgs, exif_data, anomalies


# ══════════════════════════════════════════════════════════════════════
# DISPLAY PIPELINE RESULTS
# ══════════════════════════════════════════════════════════════════════
def display_results(label: str, R: dict, imgs: dict, exif: dict):
    """Render all analysis sections for one image."""

    sec(f"ELA + REGION DETECTION — {label}")
    c1,c2,c3 = st.columns(3)
    c1.image(imgs["ela"],        caption="ELA",            width="stretch")
    c2.image(imgs["ela_heat"],   caption="ELA Heatmap",    width="stretch")
    c3.image(imgs["ela_regions"],caption="Region Detection",width="stretch")
    ela = R["ela"]
    pill_row([("ELA Mean",f"{ela['mean']:.1f}"),("Std",f"{ela['std']:.1f}"),
              ("P95",f"{ela['p95']:.1f}"),("Regions",ela['n_regions']),
              ("Prob",f"{ela['prob']:.1f}%"),("Verdict",ela['verdict'])])

    sec(f"CLONE · NOISE · EDGE · FFT — {label}")
    c1,c2,c3,c4 = st.columns(4)
    c1.image(imgs["clone"],    caption=f"Clone ({R['clone']['pairs']} pairs)",width="stretch")
    c2.image(imgs["noise"],    caption=f"Noise σ={R['noise']['sigma']:.2f}",  width="stretch")
    c3.image(imgs["edge"],     caption=f"Edges {R['edge']['density']:.1f}%",  width="stretch")
    c4.image(imgs["fft"],      caption="FFT Spectrum",                         width="stretch")

    sec(f"DCT · LBP · JPEG GHOST · GRADIENT — {label}")
    c1,c2,c3,c4 = st.columns(4)
    c1.image(imgs["dct"],      caption=f"DCT (score={R['dct']['score']:.2f})",width="stretch")
    c2.image(imgs["lbp"],      caption="LBP Texture",                          width="stretch")
    c3.image(imgs["jpeg_ghost"],caption="JPEG Ghost",                          width="stretch")
    c4.image(imgs["lum_grad"], caption="Luminance Gradient",                   width="stretch")

    sec(f"RGB HISTOGRAM — {label}")
    st.image(imgs["histogram"], width="stretch")

    sec(f"STEGANOGRAPHY DETECTION — {label}")
    st_r = R["steg"]
    flag_html = (
        '<span style="color:#ef4444;font-weight:bold;">⚠️ HIDDEN DATA SUSPECTED</span>'
        if st_r["flag"] else
        '<span style="color:#22c55e;font-weight:bold;">✓ No Hidden Data Detected</span>'
    )
    st.markdown(flag_html, unsafe_allow_html=True)
    pill_row([("Chi² avg",f"{st_r['chi2']:.1f}"),
              ("Suspicion",f"{st_r['susp']:.1f}%")])
    c1,c2,c3 = st.columns(3)
    c1.image(imgs["steg_lsb"],     caption="LSB Plane",         width="stretch")
    c2.image(imgs["steg_entropy"], caption="Entropy Map (LSB)",  width="stretch")
    c3.image(imgs["steg_bitplanes"],caption="All Bit Planes",    width="stretch")

    sec(f"METADATA TAMPERING TIMELINE — {label}")
    meta = R["meta"]
    if meta["events"]:
        rows = [["Tag","Value","Type"]] + [
            [e["tag"],e["value"][:60],e["type"]] for e in meta["events"]]
        st.table(rows)
    else:
        st.info("No EXIF metadata found.")
    if meta["anomalies"]:
        for a in meta["anomalies"]:
            st.markdown(f'<div class="warn">⚠️ {a}</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="ok">✓ No metadata anomalies detected</div>',
                    unsafe_allow_html=True)
    pill_row([("Metadata Risk",f"{meta['risk']}/100")])

    sec(f"SPLICING BOUNDARY DETECTION — {label}")
    c1, c2 = st.columns([1,2])
    c1.image(imgs["splicing"], caption="Splicing Heatmap", width="stretch")
    spl_s = R["splice"]["score"]
    if spl_s > 50:
        c2.markdown('<div class="warn">⚠️ Potential splice boundary detected.'
                    ' Noise / illumination inconsistency is high.</div>',
                    unsafe_allow_html=True)
    else:
        c2.markdown('<div class="ok">✓ Noise and illumination appear consistent.'
                    ' Low splicing signal.</div>', unsafe_allow_html=True)
    pill_row([("Splice Score",f"{spl_s:.1f}/100")])

    sec(f"GAN / AI ARTIFACT DETECTION — {label}")
    gan = R["gan"]
    gc1,gc2,gc3 = st.columns(3)
    gc1.image(imgs["gan_fft"], caption=f"CB Score {gan['cb']:.1f}", width="stretch")
    gc2.image(imgs["gan_tex"], caption=f"Texture {gan['texture']:.1f}", width="stretch")
    gc3.image(imgs["gan_col"], caption=f"Color (corr={gan['corr']:.3f})", width="stretch")
    if "gan_pow" in imgs:
        st.image(imgs["gan_pow"], width="stretch")
    pill_row([("Checkerboard",f"{gan['cb']:.1f}"),("Texture Uniformity",f"{gan['texture']:.1f}"),
              ("Color",f"{gan['color']:.1f}"),("Power Spectrum",f"{gan['power']:.1f}"),
              ("GAN Score",f"{gan['score']:.1f}/100")])
    if gan["score"] > 50:
        st.markdown('<div class="warn">⚠️ Elevated GAN/AI artifact signals detected.</div>',
                    unsafe_allow_html=True)
    else:
        st.markdown('<div class="ok">✓ No strong GAN/AI artifact fingerprints.</div>',
                    unsafe_allow_html=True)

    sec(f"FACE & BLENDING SEAM ANALYSIS — {label}")
    f1,f2 = st.columns(2)
    f1.image(imgs["face"],      caption="Face Detection",      width="stretch")
    f2.image(imgs["face_seam"], caption="Blending Seam Map",   width="stretch")
    fd = R["face"]
    pill_row([("Faces Detected",fd["data"]["faces"]),
              ("Seam Score",f"{fd['seam']:.1f}/100")])
    if fd["data"]["anomalies"]:
        for a in fd["data"]["anomalies"]:
            st.markdown(f'<div class="warn">⚠️ {a}</div>', unsafe_allow_html=True)
    if fd["seam"] > 45:
        st.markdown('<div class="warn">⚠️ High blending seam score. Possible face swap or composite.</div>',
                    unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════
# MAIN APP — TWO IMAGE MODE
# ══════════════════════════════════════════════════════════════════════
if "🔁 Two" in mode:
    sec("IMAGE INPUT")
    c1,c2 = st.columns(2)
    with c1: fA = st.file_uploader("Upload Image A",
                  type=["jpg","jpeg","png","bmp","tiff","webp"],
                  label_visibility="collapsed")
    with c2: fB = st.file_uploader("Upload Image B",
                  type=["jpg","jpeg","png","bmp","tiff","webp"],
                  label_visibility="collapsed")

    if fA and fB:
        imgA = Image.open(fA); imgB = Image.open(fB)
        sec("ORIGINAL IMAGES")
        p1,p2 = st.columns(2)
        p1.image(imgA,caption=f"A — {fA.name}",width="stretch")
        p2.image(imgB,caption=f"B — {fB.name}",width="stretch")

        sec("FILE METADATA")
        m1,m2 = st.columns(2)
        infoA = file_info(fA,imgA); infoB = file_info(fB,imgB)
        with m1:
            for k,v in infoA.items(): st.markdown(f"`{k}` → **{v}**")
        with m2:
            for k,v in infoB.items(): st.markdown(f"`{k}` → **{v}**")

        st.markdown("---")
        go_btn = st.columns([1,2,1])[1].button(
            "🚀  START FULL FORENSIC INVESTIGATION v3.0", width="stretch")

        if go_btn:
            log  = CustodyLog()
            log.add("Investigation started", f"Images: {fA.name}, {fB.name}")
            log.add("File hash A", infoA["SHA-256"])
            log.add("File hash B", infoB["SHA-256"])

            prog = st.progress(0, "Initialising…")

            RA, imgsA, exifA, anomA = run_pipeline(imgA,"Image A",fA,log,prog,0, 48)
            RB, imgsB, exifB, anomB = run_pipeline(imgB,"Image B",fB,log,prog,50,48)

            # ── PIXEL DIFF ──────────────────────────────────────────
            prog.progress(97,"Pixel diff…")
            diff_img, mean_diff = pixel_diff(imgA, imgB, diff_amp)

            prog.progress(99,"Rendering…")

            # ── TABS ─────────────────────────────────────────────────
            tabs = st.tabs(["📷 Image A","📷 Image B","🔄 Comparison","📊 Results","🔐 Custody"])

            with tabs[0]:
                display_results("Image A", RA, imgsA, exifA)

            with tabs[1]:
                display_results("Image B", RB, imgsB, exifB)

            with tabs[2]:
                sec("PIXEL DIFFERENCE MAP")
                st.image(diff_img, caption=f"Pixel Diff (mean={mean_diff:.2f})",
                         width="stretch")
                pill_row([("Mean Pixel Diff",f"{mean_diff:.2f}"),
                          ("Amplify",f"{diff_amp}x")])

                sec("SIDE-BY-SIDE COMPARISON")
                c1,c2 = st.columns(2)
                for label,R in [("Image A",RA),("Image B",RB)]:
                    col = c1 if label=="Image A" else c2
                    ela_r = R["ela"]
                    comp  = R["composite"]
                    col.markdown(f"""
<div class="vcard">
  <div style="font-size:12px;color:#9affd7;letter-spacing:2px;">{label}</div>
  <div style="font-size:20px;font-weight:900;color:{ela_r['color']};margin:6px 0;">
    {ela_r['verdict']}</div>
  <div style="font-size:11px;color:#9affd7;">COMPOSITE</div>
  <div style="font-size:24px;font-weight:900;color:{comp['color']};">{comp['verdict']}</div>
</div>""", unsafe_allow_html=True)

            with tabs[3]:
                sec("FORENSIC RESULTS DASHBOARD")
                r1,r2 = st.columns(2)
                for col,(label,R) in zip([r1,r2],[("Image A",RA),("Image B",RB)]):
                    with col:
                        comp = R["composite"]; ela_r = R["ela"]
                        st.markdown(f"""
<div class="vcard">
  <div style="font-size:11px;color:#9affd7;letter-spacing:2px;">{label} · ELA</div>
  <div style="font-size:18px;font-weight:900;color:{ela_r['color']}">{ela_r['verdict']}</div>
  <div style="font-size:11px;color:#9affd7;margin-top:8px;">COMPOSITE</div>
  <div style="font-size:22px;font-weight:900;color:{comp['color']}">{comp['verdict']}</div>
</div>""", unsafe_allow_html=True)
                        st.markdown(f"**Manipulation Prob (ELA):** {ela_r['prob']:.1f}%")
                        st.progress(int(ela_r["prob"]))
                        st.markdown(f"**Composite Score:** {comp['score']:.1f}%")
                        st.progress(int(comp["score"]))
                        st.plotly_chart(radar_chart(comp["sub"], label), use_container_width=True)
                        pill_row([
                            ("ELA Mean",    f"{ela_r['mean']:.1f}"),
                            ("Std",         f"{ela_r['std']:.1f}"),
                            ("Clone pairs", R["clone"]["pairs"]),
                            ("DCT score",   f"{R['dct']['score']:.1f}"),
                            ("Noise σ",     f"{R['noise']['sigma']:.2f}"),
                            ("Steg susp",   f"{R['steg']['susp']:.1f}%"),
                            ("GAN score",   f"{R['gan']['score']:.1f}"),
                            ("Splice",      f"{R['splice']['score']:.1f}"),
                        ])

                # ── TEXT REPORT ──────────────────────────────────────
                sec("FORENSIC OVERVIEW TEXT")
                def stats_dict(R, name):
                    return {
                        "ELA Mean":           f"{R['ela']['mean']:.2f}",
                        "ELA Std Dev":        f"{R['ela']['std']:.2f}",
                        "ELA 95th pct":       f"{R['ela']['p95']:.2f}",
                        "ELA Verdict":        R["ela"]["verdict"],
                        "Manipulation Prob":  f"{R['ela']['prob']:.1f}%",
                        "Clone Pairs":        str(R["clone"]["pairs"]),
                        "DCT Inconsistency":  f"{R['dct']['score']:.2f}",
                        "Noise Sigma":        f"{R['noise']['sigma']:.2f}",
                        "Edge Density":       f"{R['edge']['density']:.1f}%",
                        "Splicing Score":     f"{R['splice']['score']:.1f}",
                        "Steg Suspicion":     f"{R['steg']['susp']:.1f}%",
                        "Steg Chi²":          f"{R['steg']['chi2']:.1f}",
                        "GAN Score":          f"{R['gan']['score']:.1f}",
                        "Face Seam Score":    f"{R['face']['seam']:.1f}",
                        "Metadata Risk":      f"{R['meta']['risk']}/100",
                        "Composite Score":    f"{R['composite']['score']:.1f}%",
                        "Composite Verdict":  R["composite"]["verdict"],
                    }

                sA = stats_dict(RA,"A"); sB = stats_dict(RB,"B")

                txt = f"""
╔══════════════════════════════════════════════════════════════╗
║   PSYCHOMODS CYBER FORENSIC LAB v3.0  –  Report              ║
║   {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}                             ║
╚══════════════════════════════════════════════════════════════╝

IMAGE A  [{fA.name}]
""" + "\n".join(f"  {k:<26}: {v}" for k,v in sA.items()) + """

IMAGE B  [""" + fB.name + """]
""" + "\n".join(f"  {k:<26}: {v}" for k,v in sB.items()) + """

METADATA ANOMALIES — A
""" + ("\n".join(f"  ⚠ {a}" for a in anomA) or "  ✓ None") + """

METADATA ANOMALIES — B
""" + ("\n".join(f"  ⚠ {a}" for a in anomB) or "  ✓ None") + """

──────────────────────────────────────────────────────────────
Psychomods Cyber Security Tools | https://psychomods.infy.uk
"""
                st.code(txt, language="text")

                # ── DOWNLOADS ─────────────────────────────────────
                log.add("Report generated", "PDF + ZIP")
                prog.progress(100,"Generating downloads…")

                pdf = build_pdf(
                    f"Image A – {fA.name}", f"Image B – {fB.name}",
                    infoA, infoB, sA, sB, anomA, anomB,
                    log.to_text())

                all_imgs = {}
                for k,v in imgsA.items(): all_imgs[f"A_{k}"] = v
                for k,v in imgsB.items(): all_imgs[f"B_{k}"] = v
                all_imgs["pixel_diff"] = diff_img

                zp = build_zip(pdf, txt, log.to_json(), all_imgs)
                pdf.seek(0)

                d1,d2,d3 = st.columns(3)
                d1.download_button("📄 PDF Report", data=pdf,
                    file_name=f"psychomods_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.pdf",
                    mime="application/pdf", width="stretch")
                d2.download_button("📋 Text Report", data=txt,
                    file_name=f"psychomods_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.txt",
                    mime="text/plain", width="stretch")
                d3.download_button("📦 ZIP Evidence Package", data=zp,
                    file_name=f"psychomods_evidence_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.zip",
                    mime="application/zip", width="stretch")

                prog.empty()

            with tabs[4]:
                sec("CHAIN OF CUSTODY LOG")
                st.code(log.to_text(), language="text")
                st.download_button("⬇️ Download Custody JSON",
                    data=log.to_json(),
                    file_name=f"custody_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.json",
                    mime="application/json")

    elif fA or fB:
        st.info("⬆️ Please upload **both** Image A and Image B.")
    else:
        st.markdown("""
<div class="glass" style="text-align:center;padding:40px;">
  <div style="font-size:48px">🔬</div>
  <div style="font-size:20px;color:#00ff9c;margin:10px 0;font-family:monospace;">
    FORENSIC SYSTEM READY — v3.0</div>
  <div style="color:#9affd7;font-size:14px;">
    Upload two images above to begin the investigation.<br>
    20 real forensic modules · Chain of custody · ZIP evidence export
  </div>
</div>""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════
# SINGLE IMAGE MODE
# ══════════════════════════════════════════════════════════════════════
elif "📷 Single" in mode:
    sec("SINGLE IMAGE INPUT")
    uf = st.file_uploader("Upload Image",
         type=["jpg","jpeg","png","bmp","tiff","webp"],
         label_visibility="collapsed")
    if uf:
        img = Image.open(uf)
        st.image(img, caption=uf.name, width="stretch")
        info = file_info(uf, img)
        for k,v in info.items(): st.markdown(f"`{k}` → **{v}**")
        st.markdown("---")
        if st.columns([1,2,1])[1].button("🚀 ANALYSE IMAGE",width="stretch"):
            log  = CustodyLog()
            log.add("Single image analysis started", uf.name)
            log.add("SHA-256", info["SHA-256"])
            prog = st.progress(0,"Initialising…")
            R, imgs, exif, anom = run_pipeline(img, uf.name, uf, log, prog, 0, 95)
            display_results(uf.name, R, imgs, exif)

            sec("FORENSIC VERDICT")
            comp = R["composite"]; ela_r = R["ela"]
            st.markdown(f"""
<div class="vcard">
  <div style="font-size:12px;color:#9affd7">ELA VERDICT</div>
  <div style="font-size:22px;font-weight:900;color:{ela_r['color']}">{ela_r['verdict']}</div>
  <div style="font-size:12px;color:#9affd7;margin-top:8px">COMPOSITE VERDICT</div>
  <div style="font-size:26px;font-weight:900;color:{comp['color']}">{comp['verdict']}</div>
</div>""",unsafe_allow_html=True)
            st.progress(int(comp["score"]))
            st.plotly_chart(radar_chart(comp["sub"], uf.name), use_container_width=True)

            # Downloads
            prog.progress(98,"Building downloads…")
            sdict = {
                "ELA Mean":        f"{ela_r['mean']:.2f}",
                "ELA Verdict":     ela_r["verdict"],
                "Composite Score": f"{comp['score']:.1f}%",
                "Composite Verdict": comp["verdict"],
            }
            pdf = build_pdf(uf.name,"—",info,{}
                            ,sdict,{},anom,[],log.to_text())
            zp  = build_zip(pdf,"","",imgs)
            pdf.seek(0)
            d1,d2 = st.columns(2)
            d1.download_button("📄 PDF Report",data=pdf,
                file_name=f"psychomods_single_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.pdf",
                mime="application/pdf",width="stretch")
            d2.download_button("📦 ZIP Evidence",data=zp,
                file_name=f"psychomods_evidence_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.zip",
                mime="application/zip",width="stretch")
            prog.empty()


# ══════════════════════════════════════════════════════════════════════
# BATCH MODE
# ══════════════════════════════════════════════════════════════════════
elif "📦 Batch" in mode:
    sec("BATCH IMAGE INPUT")
    files = st.file_uploader("Upload up to 10 images",
            type=["jpg","jpeg","png","bmp","tiff","webp"],
            accept_multiple_files=True, label_visibility="collapsed")
    files = files[:10] if files else []
    if files:
        st.write(f"**{len(files)} image(s) loaded.** Click below to run.")
        if st.columns([1,2,1])[1].button("🚀 RUN BATCH ANALYSIS",width="stretch"):
            results_table = []
            prog = st.progress(0,"Starting batch…")
            for i, uf in enumerate(files):
                prog.progress(int(i/len(files)*95), f"Analysing {uf.name}…")
                img = Image.open(uf)
                try:
                    R, _, _, anom = run_pipeline(img, uf.name, uf)
                    comp = R["composite"]; ela_r = R["ela"]
                    results_table.append({
                        "File":             uf.name,
                        "ELA Verdict":      ela_r["verdict"],
                        "ELA Prob%":        f"{ela_r['prob']:.1f}",
                        "Composite%":       f"{comp['score']:.1f}",
                        "Composite Verdict":comp["verdict"],
                        "Clone Pairs":      R["clone"]["pairs"],
                        "GAN Score":        f"{R['gan']['score']:.1f}",
                        "Steg Susp%":       f"{R['steg']['susp']:.1f}",
                        "Metadata Anomalies":len(anom),
                    })
                except Exception as ex:
                    results_table.append({"File":uf.name,"ELA Verdict":f"ERROR: {ex}"})
            prog.progress(100,"Done.")
            prog.empty()

            sec("BATCH RESULTS")
            # Sort by composite score descending
            results_table.sort(key=lambda x: float(x.get("Composite%","0")), reverse=True)
            st.table(results_table)

            # Download CSV
            csv_lines = [",".join(results_table[0].keys())]
            for row in results_table:
                csv_lines.append(",".join(str(v) for v in row.values()))
            st.download_button("📋 Download CSV",
                data="\n".join(csv_lines),
                file_name=f"batch_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",width="stretch")


# ══════════════════════════════════════════════════════════════════════
# FOOTER
# ══════════════════════════════════════════════════════════════════════
st.markdown("""
<div class="footer">
  🔐 Psychomods Cyber Security Tools &nbsp;|&nbsp;
  🌐 <a href="https://psychomods.infy.uk" style="color:#00ff9c;">psychomods.infy.uk</a>
  &nbsp;|&nbsp; v3.0 &nbsp;|&nbsp; All rights reserved
</div>
<div style="height:46px;"></div>
""", unsafe_allow_html=True)
