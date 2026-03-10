# AIML-vlab

A web-based AI/ML Virtual Lab platform where users can explore, train, and experiment with machine learning models through an interactive UI.

---

## 🧱 Tech Stack

| Layer | Technology |
|---|---|
| **Frontend** | React.js (Create React App) |
| **Backend** | Python Flask (REST API) |
| **Database** | MongoDB |
| **Auth** | JWT (JSON Web Tokens) |
| **File Storage** | Local filesystem + Google Drive (optional) |
| **ML Frameworks** | scikit-learn, TensorFlow / Keras, PyTorch, Ultralytics YOLO |

---

## 📁 Project Structure

```
AIML-vlab/
├── frontend/               # React frontend
│   └── src/
│       ├── config.js       # ⚙️ All env variables exported from here
│       ├── constants/      # App-wide constants (API_URL, ROUTES, MODEL_CATEGORIES, COUNTRY_CODES)
│       ├── services/api.js # Centralized API client with JWT auth
│       ├── context/        # AuthContext, ThemeContext
│       └── components/     # Feature components (Auth, Models, Dataset, Studio, etc.)
├── backend/                # Flask backend
│   ├── config.py           # ⚙️ All env variables and constants exported from here
│   ├── app.py              # Flask app entry point
│   ├── auth/               # JWT auth routes and middleware
│   ├── models/             # ML model implementations + routes
│   ├── services/           # Dataset, Google Drive, hyperparameter services
│   ├── utils/              # File download, model saving utilities
│   └── mongoDb/            # MongoDB connection
└── server.bat              # Dev startup script (Windows)
```

---

## ⚙️ Environment Configuration

### Frontend — `frontend/.env`

Create a `.env` file inside `frontend/` (or set in your hosting provider):

```env
REACT_APP_API_URL=http://127.0.0.1:5050
```

All env variables are centralized in `frontend/src/config.js`. **Never use `process.env` directly outside `config.js`.**

### Backend — `backend/.env`

Copy `.env.example` to `.env` and fill in your values:

```bash
cp backend/.env.example backend/.env
```

Key variables:

| Variable | Description | Default |
|---|---|---|
| `MONGO_URI` | MongoDB connection string | `mongodb://localhost:27017/` |
| `DB_NAME` | Database name | `aiml-lab` |
| `JWT_SECRET` | Secret key for JWT signing | *(required)* |
| `JWT_EXPIRY_HOURS` | Token lifetime in hours | `24` |
| `FLASK_PORT` | Port to run Flask on | `5050` |
| `FLASK_DEBUG` | Enable debug mode | `true` |
| `ALLOWED_ORIGINS` | Comma-separated CORS origins | `http://localhost:3000,...` |
| `UPLOAD_DIR` | Directory for uploaded files | `static/uploads` |
| `TRAINED_MODELS_DIR` | Directory for saved models | `trainedModels` |
| `GOOGLE_CREDENTIALS_PATH` | Path to Google OAuth credentials JSON | `credentials.json` |
| `GOOGLE_TOKEN_PATH` | Path to Google OAuth token JSON | `token.json` |

All env variables are centralized in `backend/config.py`. **Never use `os.getenv` or `os.environ` directly outside `config.py`.**

---

## 🚀 Setup & Running

### Prerequisites
- Python 3.9+
- Node.js 18+
- MongoDB running locally (or Atlas URI in `.env`)

### 1. Backend

```bash
cd backend
pip install -r requirements.txt
python app.py
```

The API will be available at `http://127.0.0.1:5050`.

### 2. Frontend

```bash
cd frontend
npm install
npm start
```

The app will open at `http://localhost:3000`.

### 3. One-command (Windows)

```powershell
# Allow script execution (once)
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass

# Start both frontend and backend
./server.bat
```

---

## 🤖 Supported ML Models

| Category | Models |
|---|---|
| **Regression** | Simple Linear Regression, Multivariable Linear Regression |
| **Classification** | Logistic Regression, KNN, Decision Tree, Random Forest, SVM, Naive Bayes |
| **Clustering** | K-Means, DBSCAN |
| **Neural Networks** | ANN, CNN, ResNet, LSTM, YOLO (Object Detection), StyleGAN |
| **Other** | Gradient Boosting, XGBoost, Sentiment Analysis, Text Classification |

---

## 🔐 Authentication

- JWT-based authentication with token stored in `localStorage`.
- Tokens auto-expire and redirect to `/login` on 401 responses.
- Admin role (`role: 'admin'`) gets access to `/admin` dashboard.

---

## 📦 Frontend Constants Reference

All constants live in `frontend/src/constants/index.js`:

- `API_URL` — Backend base URL
- `ROUTES` — Route path strings
- `MODEL_CATEGORIES` — Model groupings with labels and icons
- `COUNTRY_CODES` — Phone country codes for signup form
