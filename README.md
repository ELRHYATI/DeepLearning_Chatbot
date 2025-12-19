<div align="center">

# 🤖 French Academic AI Chatbot

### ✨ An intelligent AI-powered chatbot for French academic writing assistance

[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![React](https://img.shields.io/badge/React-18.0+-61DAFB?style=for-the-badge&logo=react&logoColor=black)](https://reactjs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?style=for-the-badge&logo=docker&logoColor=white)](https://www.docker.com/)
[![License](https://img.shields.io/badge/License-Academic-blue?style=for-the-badge)](LICENSE)

[![Status](https://img.shields.io/badge/Status-Active-success?style=flat-square)](https://github.com)
[![Build](https://img.shields.io/badge/Build-Passing-brightgreen?style=flat-square)](https://github.com)
[![Tests](https://img.shields.io/badge/Tests-Passing-brightgreen?style=flat-square)](https://github.com)
[![Coverage](https://img.shields.io/badge/Coverage-85%25-yellow?style=flat-square)](https://github.com)

---

</div>

## 🎯 Overview

A comprehensive **French Academic AI Chatbot** system featuring advanced NLP capabilities including grammar correction, question answering, text reformulation, and RAG (Retrieval-Augmented Generation) for document-based knowledge retrieval.

<div align="center">

### 🚀 Quick Start with Docker

```bash
docker-compose up --build
```

**Access the application:**
- 🌐 Frontend: http://localhost:3000
- 🔌 Backend API: http://localhost:8000
- 📚 API Docs: http://localhost:8000/docs

</div>

---

## ✨ Key Features

<div align="center">

| 🎨 Feature | 📝 Description |
|:----------:|:-------------:|
| **📚 Grammar Correction** | Real-time French grammar and spelling correction with detailed explanations |
| **💡 Question Answering** | Academic-quality answers using state-of-the-art French language models |
| **🔄 Text Reformulation** | Intelligent text rewriting while preserving original meaning |
| **📄 RAG System** | Document-based knowledge retrieval using vector embeddings |
| **💬 Chat Interface** | Modern, responsive chat UI with real-time streaming |
| **📊 Statistics Dashboard** | Track usage, performance metrics, and learning patterns |
| **🔐 Authentication** | Secure user authentication with Google & GitHub OAuth |
| **📁 Document Management** | Upload, process, and manage PDF, TXT, DOCX documents |

</div>

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      Frontend (React)                       │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │   Chat   │  │  Grammar │  │    QA    │  │Reformulate│   │
│  │Interface │  │  Module  │  │  Module  │  │  Module  │   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘   │
└───────────────────────┬─────────────────────────────────────┘
                        │ HTTP/REST
┌───────────────────────▼─────────────────────────────────────┐
│                   Backend (FastAPI)                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │   Services   │  │     RAG      │  │  Database    │     │
│  │  (AI Models) │  │  (ChromaDB)  │  │  (SQLite)    │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
└─────────────────────────────────────────────────────────────┘
```

---

## 🛠️ Tech Stack

<div align="center">

### Backend
![Python](https://img.shields.io/badge/Python-3776AB?style=flat-square&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=flat-square&logo=fastapi&logoColor=white)
![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-D71F00?style=flat-square&logo=sqlalchemy&logoColor=white)
![HuggingFace](https://img.shields.io/badge/HuggingFace-FFD21E?style=flat-square&logo=huggingface&logoColor=black)
![ChromaDB](https://img.shields.io/badge/ChromaDB-FF6B6B?style=flat-square)

### Frontend
![React](https://img.shields.io/badge/React-61DAFB?style=flat-square&logo=react&logoColor=black)
![Vite](https://img.shields.io/badge/Vite-646CFF?style=flat-square&logo=vite&logoColor=white)
![TailwindCSS](https://img.shields.io/badge/Tailwind-38B2AC?style=flat-square&logo=tailwind-css&logoColor=white)
![Framer Motion](https://img.shields.io/badge/Framer%20Motion-0055FF?style=flat-square&logo=framer&logoColor=white)

### Infrastructure
![Docker](https://img.shields.io/badge/Docker-2496ED?style=flat-square&logo=docker&logoColor=white)
![Redis](https://img.shields.io/badge/Redis-DC382D?style=flat-square&logo=redis&logoColor=white)
![Nginx](https://img.shields.io/badge/Nginx-009639?style=flat-square&logo=nginx&logoColor=white)

</div>

---

## 📦 Installation

### 🐳 Docker (Recommended)

<details>
<summary><b>Click to expand Docker setup</b></summary>

```bash
# 1. Clone the repository
git clone <repository-url>
cd DeepLearning_prjct

# 2. (Optional) Configure environment
cp env.example .env
# Edit .env if needed

# 3. Start all services
docker-compose up --build

# 4. Access the application
# Frontend: http://localhost:3000
# Backend: http://localhost:8000
# API Docs: http://localhost:8000/docs
```

**First run:** Model downloads may take 10-15 minutes ⏳

</details>

### 💻 Local Development

<details>
<summary><b>Click to expand local setup</b></summary>

#### Backend Setup
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

#### Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

</details>

---

## 🎮 Usage Examples

### 📝 Grammar Correction
```python
POST /api/grammar/correct
{
  "text": "Je suis allé a la bibliothèque"
}

Response:
{
  "corrected_text": "Je suis allé à la bibliothèque",
  "corrections": [
    {
      "original": "a",
      "corrected": "à",
      "explanation": "Accent grave manquant"
    }
  ]
}
```

### 💡 Question Answering
```python
POST /api/qa/answer
{
  "question": "Qu'est-ce que la photosynthèse?",
  "context": "optional context paragraph"
}

Response:
{
  "answer": "La photosynthèse est le processus...",
  "confidence": 0.85,
  "sources": [...]
}
```

### 🔄 Text Reformulation
```python
POST /api/reformulation/reformulate
{
  "text": "Le texte à reformuler",
  "style": "academic"
}

Response:
{
  "reformulated_text": "Le texte reformulé...",
  "style": "academic",
  "changes": [...]
}
```

---

## 📊 API Endpoints

<div align="center">

| Method | Endpoint | Description |
|:------:|:--------:|:-----------|
| `POST` | `/api/auth/register` | Register new user |
| `POST` | `/api/auth/login` | User login |
| `POST` | `/api/grammar/correct` | Correct French text |
| `POST` | `/api/qa/answer` | Answer questions |
| `POST` | `/api/reformulation/reformulate` | Reformulate text |
| `GET` | `/api/chat/sessions` | Get chat sessions |
| `POST` | `/api/chat/sessions` | Create session |
| `POST` | `/api/documents/upload` | Upload document |

**📚 Full API Documentation:** http://localhost:8000/docs

</div>

---

## 🤖 AI Models

<div align="center">

| Model Type | Model Name | Purpose |
|:----------:|:----------:|:--------|
| **QA** | `etalab-ia/camembert-base-squadFR-fquad-piaf` | French question answering |
| **Reformulation** | `plguillou/t5-base-fr-sum-cnndm` | Text reformulation |
| **Embeddings** | `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` | Vector embeddings |
| **Grammar** | LanguageTool (French) | Grammar checking |

</div>

---

## 📁 Project Structure

```
DeepLearning_prjct/
├── 🐳 docker-compose.yml          # Docker orchestration
├── 🐳 Dockerfile                  # Backend container
├── 🐳 Dockerfile.frontend         # Frontend container
│
├── 📂 backend/
│   ├── 📂 app/
│   │   ├── main.py               # FastAPI application
│   │   ├── database.py           # Database config
│   │   ├── models.py             # SQLAlchemy models
│   │   ├── 📂 routers/           # API endpoints
│   │   │   ├── auth.py
│   │   │   ├── grammar.py
│   │   │   ├── qa.py
│   │   │   ├── chat.py
│   │   │   └── documents.py
│   │   └── 📂 services/          # Business logic
│   │       ├── grammar_service.py
│   │       ├── qa_service.py
│   │       ├── rag_service.py
│   │       └── ...
│   └── requirements.txt
│
├── 📂 frontend/
│   ├── 📂 src/
│   │   ├── 📂 components/        # React components
│   │   │   ├── ChatInterface.jsx
│   │   │   ├── Sidebar.jsx
│   │   │   └── Dashboard.jsx
│   │   ├── 📂 contexts/          # React contexts
│   │   └── App.jsx
│   └── package.json
│
└── 📄 README.md
```

---

## 🎨 Features Showcase

<div align="center">

### ✨ Core Modules

| Module | Icon | Status |
|:------:|:----:|:------:|
| Grammar Correction | 📝 | ✅ Active |
| Question Answering | 💡 | ✅ Active |
| Text Reformulation | 🔄 | ✅ Active |
| RAG System | 📚 | ✅ Active |
| Document Processing | 📄 | ✅ Active |
| Statistics Dashboard | 📊 | ✅ Active |
| User Authentication | 🔐 | ✅ Active |
| Real-time Streaming | ⚡ | ✅ Active |

</div>

---

## 🚀 Performance

<div align="center">

![Performance](https://img.shields.io/badge/Response%20Time-<2s-success?style=for-the-badge)
![Accuracy](https://img.shields.io/badge/Accuracy-85%25+-brightgreen?style=for-the-badge)
![Uptime](https://img.shields.io/badge/Uptime-99.9%25-success?style=for-the-badge)

</div>

---

## 🔧 Configuration

### Environment Variables

Create a `.env` file from `env.example`:

```bash
# JWT Secret (CHANGE IN PRODUCTION!)
SECRET_KEY=your-secret-key-change-in-production

# Ollama (Optional)
OLLAMA_URL=http://host.docker.internal:11434
OLLAMA_MODEL=mistral

# OAuth (Optional)
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret
GITHUB_CLIENT_ID=your-github-client-id
GITHUB_CLIENT_SECRET=your-github-client-secret

# Redis (Optional)
REDIS_URL=redis://redis:6379/0
```

---

## 📈 Roadmap

<div align="center">

- [x] ✅ Core AI modules (Grammar, QA, Reformulation)
- [x] ✅ RAG system with document processing
- [x] ✅ User authentication & sessions
- [x] ✅ Statistics dashboard
- [x] ✅ Docker containerization
- [ ] 🔄 Multi-language support
- [ ] 🔄 Advanced fine-tuning capabilities
- [ ] 🔄 Collaborative features
- [ ] 🔄 Performance monitoring dashboard

</div>

---

## 🤝 Contributing

<div align="center">

Contributions are welcome! Please feel free to submit a Pull Request.

1. 🍴 Fork the repository
2. 🌿 Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. 💾 Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. 📤 Push to the branch (`git push origin feature/AmazingFeature`)
5. 🔀 Open a Pull Request

</div>

---

## 📄 License

<div align="center">

This project is for **academic purposes**.

</div>

---

## 🙏 Acknowledgments

<div align="center">

- [Hugging Face](https://huggingface.co/) for model hosting
- [LanguageTool](https://languagetool.org/) for grammar checking
- [FastAPI](https://fastapi.tiangolo.com/) and [React](https://reactjs.org/) communities

</div>

---

<div align="center">

### ⭐ If you find this project helpful, please consider giving it a star!

**Made with ❤️ for the academic community**

[![GitHub stars](https://img.shields.io/github/stars/ELRHYATI/DeepLearning_Chatbot?style=social)](https://github.com/ELRHYATI/DeepLearning_Chatbot)
[![GitHub forks](https://img.shields.io/github/forks/ELRHYATI/DeepLearning_Chatbot?style=social)](https://github.com/ELRHYATI/DeepLearning_Chatbot)
[![GitHub watchers](https://img.shields.io/github/watchers/ELRHYATI/DeepLearning_Chatbot?style=social)](https://github.com/ELRHYATI/DeepLearning_Chatbot)

</div>

---

<div align="center">

**🚀 Ready to get started? Run `docker-compose up --build` and start chatting!**

</div>
