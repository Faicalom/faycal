# Ultra-fast Promo Code Monitor (PyQt5 + mss + OCR)

Desktop tool to monitor a **tiny screen region** at high FPS and detect promo codes like `Y3761P` from an Android emulator stream.

## Features

- **Transparent ROI selector** to capture only the red banner area.
- **High-speed grabbing** with `mss` (only selected ROI, not full screen).
- **OpenCV preprocessing before OCR**:
  - Grayscale conversion
  - Binary thresholding with adjustable threshold
- **Fast Tesseract OCR** tuned for single-line text (`--psm 7` by default).
- **Regex extraction** for alphanumeric promo format (`\b[A-Z0-9]{5,7}\b`).
- **Instant actions on match**:
  - copy code to clipboard (`pyperclip`)
  - play alert sound
  - show code in huge text
  - pause monitoring loop
- **Responsive GUI** using a background `QThread`.

## Project structure

```text
faycal/
├─ app.py
├─ requirements.txt
└─ README.md
```

## Requirements

- Python 3.9+
- Tesseract OCR engine installed on system:
  - Windows: install from UB Mannheim build or official installer
  - Linux: `sudo apt install tesseract-ocr`
- Pip dependencies from `requirements.txt`

## Setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

If `pytesseract` cannot find your Tesseract binary on Windows, add in `app.py` before OCR run:

```python
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
```

## Run

```bash
python app.py
```

## How to use

1. Click **Select ROI**.
2. Drag a rectangle tightly around the promo code location (red banner only).
3. (Optional) tune:
   - **Threshold** (default `170`)
   - **PSM** (`7` for line, `8` for single word)
   - **Regex** (default `\b[A-Z0-9]{5,7}\b`)
4. Click **Start Monitoring**.
5. When a match is found, the app copies code, alerts, shows huge text, and pauses.

## Performance notes

- Keep ROI **as small as possible** for max FPS.
- `interval_ms=15` in code is aggressive; increase if CPU usage is high.
- If OCR is noisy, adjust threshold and ROI tightness.

