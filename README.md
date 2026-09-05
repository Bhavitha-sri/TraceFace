# 🔎 TraceFace    

### ** is in live⚡: trace-face-dlb9emuv0-bhavitha-sris-projects.vercel.app**
### **AI Face Matching × Public Web Discovery × Blockchain Verification**

<p align="center">
  <b>Trace. Match. Verify.</b><br>
  An end-to-end AI pipeline for discovering and verifying potential facial matches across publicly available web content.
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.11-blue?style=for-the-badge&logo=python" />
  <img src="https://img.shields.io/badge/OpenCV-Computer%20Vision-green?style=for-the-badge&logo=opencv" />
  <img src="https://img.shields.io/badge/SFace-Face%20Matching-purple?style=for-the-badge" />
  <img src="https://img.shields.io/badge/Flask-Backend-black?style=for-the-badge&logo=flask" />
  <img src="https://img.shields.io/badge/Blockchain-Verification-orange?style=for-the-badge" />
</p>

---

## 🌐 What is TraceFace?

**TraceFace** is an AI-powered face matching and public-web discovery system designed to connect multiple technologies into a single verification pipeline.

Instead of treating **computer vision, web discovery, and blockchain** as separate components, TraceFace combines them into one workflow:

> **Upload a face → Discover public web content → Compare faces with AI → Identify potential matches → Verify the discovery using blockchain**

---

## ⚡ The TraceFace Pipeline

```text
                    TRACEFACE
                       │
                       ▼
              ┌─────────────────┐
              │   📷 FACE INPUT  │
              │   Upload Image   │
              └────────┬────────┘
                       │
                       ▼
              ┌─────────────────┐
              │  👁️ FACE        │
              │    DETECTION    │
              └────────┬────────┘
                       │
                       ▼
              ┌─────────────────┐
              │  🌐 PUBLIC WEB  │
              │    DISCOVERY    │
              └────────┬────────┘
                       │
                       ▼
              ┌─────────────────┐
              │  🧠 SFace AI    │
              │  FACE MATCHING  │
              └────────┬────────┘
                       │
                       ▼
              ┌─────────────────┐
              │  🎯 POTENTIAL    │
              │     MATCH       │
              └────────┬────────┘
                       │
                       ▼
              ┌─────────────────┐
              │  ⛓️ BLOCKCHAIN  │
              │   VERIFICATION  │
              └─────────────────┘
```

---

# ✨ Key Features

<table>
<tr>
<td width="50%">

### 🧑‍💻 Face Detection

Detects and extracts facial information from the uploaded image using computer-vision techniques.

</td>
<td width="50%">

### 🧠 AI Face Matching

Uses **SFace-based facial embeddings** to compare the input face with candidate images.

</td>
</tr>

<tr>
<td>

### 🌐 Public Web Discovery

Searches publicly accessible web content to discover potentially relevant images.

</td>
<td>

### 🎯 Match Identification

Produces traceable match records for potentially corresponding web content.

</td>
</tr>

<tr>
<td>

### ⛓️ Blockchain Verification

Adds a verification layer for discovered-data integrity and traceability.

</td>
<td>

### 📊 Interactive Dashboard

Presents detection, discovery, matching and verification results in a unified interface.

</td>
</tr>
</table>

---

# 🧠 How It Works

### 01 — Upload

The user provides an image containing a face.

### 02 — Detect

TraceFace detects the face and prepares it for comparison.

### 03 — Discover

The system searches publicly available web content for potentially relevant images.

### 04 — Compare

Candidate images are analyzed using **SFace facial representations**.

### 05 — Match

The system identifies potential visual matches and generates a unique match reference.

### 06 — Verify

Relevant discovery information is prepared for blockchain-based verification.

---

# 📸 Result Preview

> **TraceFace can produce a result similar to:**

```text
╭─────────────────────────────────────────────╮
│              ✓ FACE DETECTED                │
│                                             │
│   Public Web Images Found: 60               │
│                                             │
│              ✓ MATCH FOUND                  │
│                                             │
│   Match ID: WEB-006                         │
│                                             │
│   Chennai: At an event in                   │
│   Ethiraj College for Women, Tamil ...      │
│                                             │
│   AI Model: SFace                           │
│   Status: Potential Web Match               │
╰─────────────────────────────────────────────╯
```

### 🖼️ Application Screenshot

**Add the project screenshot here:**

```text
screenshots/traceface-result.png
```

Then display it in this README using:

```markdown
<p align="center">
  <img src="screenshots/traceface-result.png" width="900">
</p>
```

---

# 🏗️ Architecture

```text
                    ┌──────────────────┐
                    │   User / Client  │
                    └────────┬─────────┘
                             │
                             ▼
                    ┌──────────────────┐
                    │   Flask Web App  │
                    └────────┬─────────┘
                             │
             ┌───────────────┼────────────────┐
             ▼               ▼                ▼
      ┌────────────┐  ┌─────────────┐  ┌─────────────┐
      │   OpenCV   │  │ Web Search  │  │ Blockchain  │
      │ Face Detect│  │  Discovery  │  │ Verification│
      └─────┬──────┘  └──────┬──────┘  └──────┬──────┘
            │                │                │
            └────────────────┼────────────────┘
                             ▼
                    ┌──────────────────┐
                    │   SFace Matcher  │
                    └────────┬─────────┘
                             │
                             ▼
                    ┌──────────────────┐
                    │  Verified Result │
                    └──────────────────┘
```

---

# 🛠️ Technology Stack

| Layer               | Technology                  |
| ------------------- | --------------------------- |
| 🐍 Language         | **Python**                  |
| 👁️ Computer Vision | **OpenCV**                  |
| 🧠 Face Recognition | **SFace**                   |
| 🌐 Discovery        | **Public Web Search**       |
| ⚙️ Backend          | **Flask**                   |
| 🎨 Frontend         | **HTML • CSS • JavaScript** |
| ⛓️ Verification     | **Blockchain**              |
| 📦 Dependencies     | **Python / pip**            |
| 🔧 Version Control  | **Git + GitHub**            |

---

# 📂 Project Structure

```text
TraceFace/
│
├── 📄 app.py
├── 📄 requirements.txt
├── 📄 README.md
│
├── 📁 src/
│   ├── face_detection/
│   ├── face_matching/
│   ├── web_discovery/
│   └── blockchain/
│
├── 📁 templates/
│   └── *.html
│
├── 📁 static/
│   ├── css/
│   ├── js/
│   └── images/
│
├── 📁 screenshots/
│   └── traceface-result.png
│
└── 📁 data/
    └── *
```

---

# 🚀 Getting Started

## 1. Clone the repository

```bash
git clone https://github.com/Bhavitha-sri/TraceFace.git
cd TraceFace
```

## 2. Create a virtual environment

```bash
python -m venv .venv
```

## 3. Activate it

### Windows PowerShell

```powershell
.venv\Scripts\Activate.ps1
```

## 4. Install dependencies

```bash
pip install -r requirements.txt
```

## 5. Run TraceFace

```bash
python app.py
```

Open:

```text
http://127.0.0.1:5000
```

---

# 🔐 Responsible AI & Privacy

TraceFace is intended for **research, educational, and authorized applications**.

The system works with publicly accessible web content. It should not be used for harassment, stalking, unauthorized surveillance, or privacy-invasive activities.

### ⚠️ Important

A facial similarity result **does not prove a person's identity**.

Results should be treated as **potential matches** and independently reviewed before making conclusions.

Blockchain verification provides an integrity/traceability layer for recorded information; it does **not** independently establish that the underlying web discovery is factually correct.

---

# 🎯 Why TraceFace?

Most systems solve only one part of the problem.

**TraceFace connects the complete journey:**

```text
        AI
        │
        ▼
   FACE MATCHING
        │
        ▼
  WEB DISCOVERY
        │
        ▼
    POTENTIAL
      MATCH
        │
        ▼
   BLOCKCHAIN
   VERIFICATION
```

### One pipeline.

### Multiple technologies.

### One verifiable workflow.

---

# 🏆 Hackathon Project

### **Hacker House Goa 2026**

**Track:** AI × Crypto

TraceFace demonstrates how **Artificial Intelligence, Computer Vision, Web Discovery, and Blockchain** can work together to build a modern verification-oriented application.

---

# 👩‍💻 Developer

## Bhavitha Sri

**B.Tech — Information Technology**

### Interests

`Artificial Intelligence` · `Machine Learning` · `Computer Vision` · `Cybersecurity` · `Full-Stack Development` · `Blockchain`

---

<p align="center">

### ⭐ If you find TraceFace interesting, consider starring the repository!

**Built with Python • AI • Computer Vision • Blockchain**

</p>
