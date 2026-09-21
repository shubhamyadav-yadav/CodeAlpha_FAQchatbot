# FAQ Chatbot Using NLP

A production-ready, intelligent FAQ Chatbot application built with **Python (FastAPI)** and a modern **white-themed responsive frontend**. The chatbot understands user inquiries through structured **Natural Language Processing (NLP)** preprocessing, sublinear **TF-IDF n-gram vectorization**, and dual-representation **Cosine Similarity** matching—returning precise answers, confidence metrics, and helpful follow-up recommendations.

---

## 1. Project Overview

Traditional keyword-search bots frequently fail when users phrase questions using natural language synonyms, inverted sentence structures, or colloquial terms. This project implements a dedicated NLP QA pipeline that:
1. Cleans and normalizes raw user inquiries.
2. Performs linguistic lemmatization and morphological derivation.
3. Maps input questions to continuous vector spaces using unigram and bigram TF-IDF representations.
4. Compares user vectors against knowledge-base FAQ representations via Cosine Similarity.
5. Applies an empirically calibrated confidence threshold (`0.30`) to distinguish valid inquiries from out-of-domain questions and trigger polite fallback guidance.
6. Renders answers inside an executive-styled, accessible, white-themed chat interface protected against Cross-Site Scripting (XSS).

---

## 2. Key Features

- **Dual-Representation NLP Similarity Matching**: Combines direct question-to-question similarity (ensuring 100% confidence on direct matches) and question-to-keywords/category similarity (capturing rephrased queries).
- **Sub-Millisecond Inference**: Precomputes and caches the FAQ TF-IDF matrix at application startup, enabling queries to complete in `< 2 ms`.
- **Intelligent Fallback & Suggestions**: When user queries fall below the confidence threshold, the chatbot avoids hallucinations and politely falls back, offering relevant question suggestions.
- **Enterprise-Grade Security**:
  - Strict XSS protection using DOM `textContent` rendering.
  - Pydantic v2 input validation (`min_length=1`, `max_length=500`, whitespace stripping).
  - Rate limiting via `slowapi` (`60/minute` default).
  - Security headers middleware (`X-Content-Type-Options`, `X-Frame-Options`, `X-XSS-Protection`, `Content-Security-Policy`).
  - Safe error masking: No python tracebacks or system filepaths leaked to clients.
- **Modern White/Light UI Theme**:
  - Apple/Linear-inspired light aesthetic with subtle borders and shadows.
  - Interactive suggested topic chips for 1-click query testing.
  - Real-time character counter and input feedback alerts.
  - Clipboard copy button with instant checkmark feedback.
  - Interactive Knowledge Base Directory Modal to browse all categorized FAQs.
  - Responsive across desktop, laptop, tablet, and mobile devices.
- **Single-Server Deployment**: FastAPI serves both `/api/v1/*` endpoints and static frontend files at `/`, avoiding CORS issues during local usage while keeping CORS open for decoupled architectures.

---

## 3. Technology Stack

- **Backend Framework**: Python 3.10+ / 3.14+, [FastAPI](https://fastapi.tiangolo.com/), [Uvicorn](https://www.uvicorn.org/)
- **Data Validation & Settings**: [Pydantic v2](https://docs.pydantic.dev/)
- **NLP Engine**:
  - [NLTK](https://www.nltk.org/): WordNetLemmatizer, WordNet derivational morphology & pertainyms, tokenization, contextual stopwords
  - [scikit-learn](https://scikit-learn.org/): `TfidfVectorizer` (unigrams + bigrams, sublinear TF scaling)
  - [NumPy](https://numpy.org/) & [SciPy](https://scipy.org/): Cosine similarity matrix operations
- **Security & Rate Limiting**: [SlowAPI](https://github.com/laurentS/slowapi)
- **Testing**: [pytest](https://docs.pytest.org/), [httpx](https://www.python-httpx.org/) TestClient
- **Frontend**: HTML5 (Semantic, ARIA-accessible), Modern CSS3 (CSS Variables, Flexbox/Grid), Vanilla JavaScript (ES6+, zero build bloat)

---

## 4. NLP Pipeline Architecture

```text
                     User Question
                           ↓
┌─────────────────────────────────────────────────────────┐
│               1. Text Cleaning & Normalization          │
│  - Lowercasing                                          │
│  - Contraction expansion ("can't" -> "cannot")          │
│  - Non-alphanumeric punctuation removal                 │
└──────────────────────────┬──────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────┐
│               2. NLP Preprocessing                      │
│  - Tokenization                                         │
│  - Contextual stop-word filtering (keeps question words)│
│  - WordNet Lemmatization (nouns, verbs, adjectives)     │
│  - Morphological Derivation & Pertainym Resolution      │
│    ("payment" -> "pay", "internationally" -> "intl")    │
└──────────────────────────┬──────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────┐
│               3. Vector Space Transformation            │
│  - TF-IDF Vectorizer with n-gram range (1, 2)           │
│  - Sublinear term frequency scaling (1 + log(tf))       │
└──────────────────────────┬──────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────┐
│               4. Dual Cosine Similarity Scoring         │
│  - Sim_Q: Direct match against FAQ Questions            │
│  - Sim_C: Match against Question + Keywords + Category  │
│  - Blended Score = max(Sim_Q, Sim_C * 0.95)             │
└──────────────────────────┬──────────────────────────────┘
                           ↓
                    Score >= 0.30 ?
                   /               \
                [YES]              [NO]
                 /                   \
        Return Best FAQ Answer   Return Polite Fallback
       + Confidence & Category   + Suggested Alternative
```

### Why WordNet Derivational Forms & Pertainyms?
In standard lemmatization, `"payment"` remains `"payment"` (a noun) while `"pay"` remains `"pay"` (a verb). By querying WordNet's `derivationally_related_forms()`, our preprocessor automatically connects `"payment"` with `"pay"`, `"shipping"` with `"ship"`, and `"cancellation"` with `"cancel"`. Furthermore, WordNet's `pertainyms()` links adverbs like `"internationally"` directly to their adjective `"international"`. This allows rephrased queries (e.g., *"Which methods can I use to pay?"*) to naturally match the canonical FAQ (*"What payment methods do you accept?"*).

---

## 5. Project Folder Structure

```text
ChatBot/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── config.py              # Application settings, threshold, rate limits
│   │   ├── main.py                # FastAPI app, security middleware, static mount
│   │   ├── data/
│   │   │   └── faqs.json          # Curated FAQ dataset with categories & keywords
│   │   ├── models/
│   │   │   └── schemas.py         # Pydantic models for chat requests & responses
│   │   ├── nlp/
│   │   │   ├── __init__.py
│   │   │   ├── preprocessor.py    # Cleaning, tokenization, lemmatization
│   │   │   └── matcher.py         # TF-IDF & Cosine Similarity matching engine
│   │   ├── routers/
│   │   │   ├── __init__.py
│   │   │   ├── chat.py            # POST /api/v1/chat endpoint
│   │   │   └── faqs.py            # GET /api/v1/faqs and /api/v1/health endpoints
│   │   └── utils/
│   │       ├── __init__.py
│   │       └── logger.py          # Structured logging utility
│   ├── tests/
│   │   ├── __init__.py
│   │   ├── test_preprocessor.py   # Unit tests for text cleaning and NLP
│   │   ├── test_matcher.py        # Unit tests for similarity engine & thresholds
│   │   ├── test_api.py            # Integration tests for FastAPI endpoints
│   │   ├── test_benchmark.py      # Benchmark matrix across 24 test inquiries
│   │   └── live_test.py           # Live E2E testing script against running server
│   └── requirements.txt           # Production and test dependencies
├── frontend/
│   ├── index.html                 # Semantic, accessible HTML5 structure
│   ├── css/
│   │   └── style.css              # Executive white-themed CSS stylesheet
│   └── js/
│       └── app.js                 # Frontend chat client & XSS-safe DOM renderer
├── .env.example
├── .gitignore
└── README.md
```

---

## 6. Installation & Setup

### Prerequisites
- Python 3.10+ (tested on Python 3.14.3)
- pip

### 1. Clone or Open the Repository
```bash
cd c:\Users\shubh\Downloads\Projects\ChatBot
```

### 2. Install Dependencies
```bash
pip install -r backend/requirements.txt
```

### 3. Download Required NLTK Corpora (One-time)
```bash
python -c "import nltk; nltk.download('punkt'); nltk.download('punkt_tab'); nltk.download('wordnet'); nltk.download('stopwords')"
```

---

## 7. Running the Application

Start the FastAPI application server with Uvicorn:

```bash
python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000
```

*(If port 8000 is occupied on your system, run on port 8001: `--port 8001`)*

### Open the Application
- **Chatbot Web UI**: [http://127.0.0.1:8000/](http://127.0.0.1:8000/)
- **Interactive OpenAPI Documentation**: [http://127.0.0.1:8000/api/docs](http://127.0.0.1:8000/api/docs)
- **Health Check**: [http://127.0.0.1:8000/api/v1/health](http://127.0.0.1:8000/api/v1/health)

---

## 8. Running Automated Tests

Run the complete test suite using `pytest`:

```bash
python -m pytest backend/tests -v --ignore=backend/tests/live_test.py
```

### Test Suite Summary
- `test_preprocessor.py`: Tests lowercasing, punctuation removal, contraction expansion, lemmatization, and derivation forms.
- `test_matcher.py`: Tests exact question match, rephrased queries, out-of-domain rejection, case/punctuation insensitivity, and empty inputs.
- `test_api.py`: Tests health endpoint, FAQ listings, query validation, max length limits (500 chars), XSS payloads, and security headers.
- `test_benchmark.py`: Evaluates a 24-question benchmark matrix (direct, rephrased, and out-of-domain) ensuring >= 85% accuracy.

### Live Server Integration Test
While the server is running:
```bash
python backend/tests/live_test.py
```

---

## 9. Security Review

- [x] **XSS Prevention**: Frontend strictly renders user and bot messages using `document.createElement()` and `.textContent`. No raw HTML injection is permitted.
- [x] **Input Validation**: Rejects empty strings, whitespace-only queries, and queries exceeding 500 characters with HTTP 422.
- [x] **Rate Limiting**: Protects against denial-of-service and flooding using SlowAPI token limits (`60/minute` default).
- [x] **Information Disclosure**: Unhandled backend errors log full tracebacks to server-side logs while returning generic error messages to clients.
- [x] **Security Headers**: Injects `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `X-XSS-Protection: 1; mode=block`, and Content Security Policy headers.

---

## 10. System Limitations

- **Knowledge Boundary**: The chatbot is specifically designed for FAQ question-answering based on the supplied knowledge base (`backend/app/data/faqs.json`). It does not generate conversational dialogue outside this scope.
- **Extreme Paraphrasing**: Queries with heavily distorted misspellings or abstract metaphors not present in the vocabulary may fall below the 0.30 similarity threshold, safely triggering the fallback response.
- **Multilingual Support**: The current NLP preprocessor is optimized for the English language using NLTK WordNet and English stopword dictionaries.
