# VN Bank Advisor — Technical PRD 🧩

---

## 📌 Tóm tắt ngắn gọn
**Mục tiêu:** Tạo báo cáo PRD kỹ thuật để mô tả kiến trúc, framework, luồng dữ liệu và lifecycle mô hình cho dự án **VN Bank Advisor**. Tài liệu nhấn mạnh **frameworks, kiến trúc hệ thống, pipelines dữ liệu/ML**, và tiêu chí chấp nhận (acceptance criteria).

---

## ✅ 1) Phạm vi & Mục tiêu
- **Phạm vi:** Mô tả kỹ thuật cho hệ thống training & inference ML (XGBoost), API backend (FastAPI), và frontend (React + Vite). Bao gồm data ingestion, feature engineering, training, inference, lưu artifact, và tích hợp UI.
- **Mục tiêu:** Chuẩn hoá kiến trúc để:
  - Dễ reproduce pipeline training & inference
  - Rõ trách nhiệm giữa components (data, model, api, ui)
  - Hỗ trợ triển khai (dev → staging → prod), monitoring và CI/CD

---

## 🔧 2) Tech Stack chính
- **Backend:** FastAPI, Pydantic, SQLAlchemy
- **ML / Data:** Python 3.8+, pandas, numpy, scikit-learn, xgboost, joblib
- **Pipeline:** python modules (`pipeline/`)
- **Frontend:** React + Vite (TypeScript in `web/`), Tailwind, Radix UI
- **Artifacts:** `artifacts/` (models: `*.joblib`, `feature_cols.json`, `metrics.json`)
- **Dev tools:** uvicorn, npm, vite

---

## 🏗 3) Kiến trúc hệ thống (logical)
1. Data sources (CSV/Excel in `data/`) →
2. Data ingestion & ETL (`pipeline/data_loader.py`) →
3. Feature engineering (`pipeline/feature_engineering.py`) →
4. Training (`pipeline/train_pipeline.py`) → save artifacts in `artifacts/` →
5. Inference (`pipeline/inference.py`) → used by backend `/api/v1/advisor/consult` →
6. Frontend consumes API and displays recommendations

> Logical diagram: Data → Pipeline → Artifacts → API → Frontend

---

## ⚙ 4) Thành phần & trách nhiệm
- **pipeline/**
  - `data_loader.py`: load & standardize market, micro (fundamental+macro), sentiment
  - `feature_engineering.py`: build Group A..E features (market, technical, sentiment, macro, fundamentals)
  - `model_factory.py`: create XGBoost models with params from `config.py`
  - `train_pipeline.py`: merge, create targets, train models, save metrics/artifacts
  - `inference.py`: load models + `feature_cols.json`, prepare latest data, produce signals
- **backend/**
  - `main.py`: FastAPI app + route registration
  - `api/`: endpoints (advisor, market, signals, admin)
  - `database.py` / `models/`: DB access via SQLAlchemy
- **frontend/**
  - React components, pages, calls to API endpoints

---

## 💡 5) Data & Feature Management
- **Feature groups**: GROUP_A..E defined in `pipeline/config.py` (market, technical, sentiment, macro, bank)
- **Feature listing:** `artifacts/feature_cols.json` (exported after training)
- **Targets:** `log_return_21d`, plus proxies for direction/regime/risk
- **Cadence:** daily market + quarterly fundamentals; merge via `quarter_date`

---

## 🧠 6) ML Lifecycle & Ops
- **Training:** `python -m pipeline.train_pipeline` (time-based split 80/20)
- **Model format:** joblib XGBoost models in `artifacts/`
- **Inference:** `pipeline/inference.run_inference(symbol)` used by API
- **Metrics:** saved in `artifacts/metrics.json`, `comparison_data.json`
- **Gaps:** no orchestrator (Airflow), no model registry, no automated CI/CD detected

---

## 🔁 7) Deployment & Runtime
- Dev run API: `uvicorn backend.app.main:app --reload`
- Dev run frontend: `cd web && npm run dev`
- Recommendations for production:
  - Dockerize backend & frontend
  - Model registry (MLflow, DVC or S3 + manifest)
  - Hot-reload or graceful model reload strategy when artifacts update

---

## 📊 8) Monitoring, Logging & Testing
- Hiện trạng: logging minimal (print), no monitoring, no tests
- Đề xuất:
  - Structured logging (loguru/structlog)
  - Unit tests for `data_loader`, `feature_engineering`, `inference`
  - Basic metrics (inference latency, model confidence distribution, data schema drift)

---

## 🔒 9) Security & Configuration
- `.env` via `dotenv` (sensitive data not checked-in)
- CORS currently `*` — **thắt chặt** trong production
- Secrets (Groq API key) read from env — ensure not committed

---

## 🧪 10) Acceptance Criteria (MVP)
- [ ] PRD reviewed & agreed
- [ ] `train_pipeline` runs end-to-end and writes models to `artifacts/`
- [ ] `pipeline/inference.py` returns valid signals for sample symbol
- [ ] `POST /api/v1/advisor/consult` returns `AdvisorResponse` for sample symbol
- [ ] Frontend displays recommendation
- [ ] Add unit tests for critical ETL & inference functions

---

## ✅ 11) Short-term Recommendations (prioritized)
1. Add Dockerfiles and a `docker-compose` for reproducible deployments 🔧
2. Add CI (GitHub Actions) to run unit tests & lint on PRs ✅
3. Introduce model registry/versioning (MLflow or S3 + manifest) 📦
4. Add structured logging & basic monitoring (Prometheus/Grafana or cloud alternatives) 📈
5. Tighten CORS / pipeline secrets handling 🔐

---

## 📎 Appendix — Key files & commands
- Training: `pipeline/train_pipeline.py` → `python -m pipeline.train_pipeline`
- Inference: `pipeline/inference.py` → consumed by `backend/app/api/advisor.py`
- API run: `uvicorn backend.app.main:app --reload`
- Frontend: `cd web && npm run dev`
- Config: `pipeline/config.py`
- Artifacts: `artifacts/`

---

> Nếu bạn muốn, tôi có thể:
> - Chuyển PRD này thành PR và commit file `docs/technical_prd.md` (đã thực hiện),
> - Thêm sơ đồ kiến trúc (SVG) và flow chart ETL,
> - Viết Dockerfile mẫu hoặc GitHub Actions CI config.

*Created by GitHub Copilot — let me know which next task you want (diagram, Dockerfile, tests).*