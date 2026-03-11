# 🧠 Psychomods Cyber Forensic Lab v3.0
### Advanced Image Manipulation Detection System

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python)](https://python.org)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.35%2B-red?logo=streamlit)](https://streamlit.io)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)
[![Website](https://img.shields.io/badge/Website-psychomods.infy.uk-00ff9c)](https://psychomods.infy.uk)

> A professional-grade, fully real (no demos) image forensics tool built with Python and Streamlit. Detects manipulation, AI generation, steganography, metadata tampering, and more — all locally on your machine.

---

## 🚀 Live Demo

Deploy instantly on **Streamlit Cloud** — see below.

---

## 🔬 Forensic Modules (20 Real Techniques)

| # | Module | What it detects |
|---|--------|----------------|
| 1 | **ELA** | JPEG compression inconsistencies — edited regions re-save differently |
| 2 | **ELA Heatmap** | Visual amplification of ELA signal |
| 3 | **Region Detection** | Bounding boxes around suspicious areas |
| 4 | **Clone / Copy-Move** | ORB keypoint matching for duplicated regions |
| 5 | **Noise Residual** | Gaussian residual map + noise sigma (σ) measurement |
| 6 | **Edge Analysis** | Canny edge density — unnatural edges = possible splice |
| 7 | **FFT Spectrum** | Frequency domain artifacts from editing tools |
| 8 | **DCT Block Analysis** | 8×8 block energy inconsistency — double-compression detection |
| 9 | **LBP Texture** | Local Binary Pattern — texture discontinuities |
| 10 | **JPEG Ghost** | Multi-quality re-save difference maps |
| 11 | **Luminance Gradient** | Sobel gradient — unnatural lighting transitions |
| 12 | **RGB Histogram** | Channel distribution analysis |
| 13 | **Steganography (LSB)** | Chi-square attack, bit-plane grid, entropy heatmap |
| 14 | **Metadata Timeline** | EXIF date cross-check, editing software detection, GPS flags |
| 15 | **Splicing Boundary** | Block-wise noise sigma + illumination gradient discontinuity |
| 16 | **GAN / AI Artifact** | Checkerboard FFT peaks, texture uniformity, color correlation, power spectrum slope |
| 17 | **Face Analysis** | Haar cascade detection, eye asymmetry, size ratio anomalies |
| 18 | **Blending Seam** | High-pass seam map for face-swap detection |
| 19 | **Pixel Diff** | Amplified absolute difference between two images |
| 20 | **Composite Score** | Weighted combination of all signals → single 0–100 verdict |

---

## 📸 Analysis Modes

- **🔁 Two-Image Compare** — Full side-by-side forensic investigation
- **📷 Single Image** — Complete pipeline on one image
- **📦 Batch Mode** — Analyse up to 10 images, ranked CSV output

---

## 📦 Installation

### 1. Clone the repo
```bash
git clone https://github.com/YOUR_USERNAME/psychomods-forensic-lab.git
cd psychomods-forensic-lab
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Run
```bash
streamlit run psychomods_forensic_lab_v3.py
```

Open your browser at `http://localhost:8501`

---

## ☁️ Deploy on Streamlit Cloud (Free)

1. Fork this repo on GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Click **"New app"**
4. Select your forked repo
5. Set **Main file path** to `psychomods_forensic_lab_v3.py`
6. Click **Deploy** ✅

---

## 📋 Requirements

```
streamlit>=1.35.0
Pillow>=10.0.0
opencv-python-headless>=4.9.0
numpy>=1.26.0
matplotlib>=3.8.0
reportlab>=4.1.0
scipy>=1.12.0
scikit-image>=0.22.0
plotly>=5.18.0
```

> **Note:** `mediapipe` is optional — the app works without it using OpenCV Haar cascades for face detection.

---

## 📤 Exports

| Format | Contents |
|--------|----------|
| **PDF Report** | File info, all forensic metrics, anomalies, custody log |
| **Text Report** | Plain text summary of all results |
| **ZIP Evidence Package** | All analysis images + PDF + text + chain-of-custody JSON |
| **Custody JSON** | Timestamped, SHA-256 hashed log of every analysis step |
| **CSV (Batch)** | Ranked results table for batch analysis |

---

## 🗂️ Project Structure

```
psychomods-forensic-lab/
├── psychomods_forensic_lab_v3.py   # Main app
├── requirements.txt                 # Dependencies
└── README.md                        # This file
```

---

## ⚠️ Disclaimer

Results are probabilistic indicators generated algorithmically.
Always validate findings with a certified digital forensics examiner before use in legal proceedings.

---

## 🌐 Links

- Website: [psychomods.infy.uk](https://psychomods.infy.uk)
- Tool: Psychomods Cyber Security Tools

---

## 📄 License

MIT License — free to use, modify, and distribute.
