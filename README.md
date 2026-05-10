# 主動式 ETF 偵測雷達 (ETF Radar)

量化「多位基金經理人同步加/減碼同一標的」的共識訊號系統。

> 完整產品規格：[`docs/product_plan.md`](docs/product_plan.md)

## 狀態

- **M1 基礎建設**：完成（6 container 骨架 + Alembic schema）
- **M2 核心分析引擎**：完成（三步驟主動加減碼計算 + 跨 ETF 彙總 + 訊號偵測，38 unit + 23 endpoint test）
- **M3 介面與通知**：完成（4 組 API 查詢 + Vue 3 SPA + Redis pub/sub SSE）
- **M4 回測模組**：未開始
- **M5 穩定化 / 真實爬蟲 Parser**：未開始

## 技術棧

FastAPI · Vue 3 · PostgreSQL 16 · Celery 5 · Redis 7 · httpx · Playwright · SQLAlchemy 2 · pandas 2 · Docker Compose

## 快速開始

```bash
cp .env.example .env
# 至少設定 POSTGRES_PASSWORD

docker compose build
docker compose up -d

# 套用 schema
docker compose exec web alembic upgrade head
```

存取：

- Web UI / API：<http://localhost:8080>
- API docs：<http://localhost:8080/docs>

production image 採 multi-stage build：Node 22 stage 編譯 Vue dist/，Python stage 由 FastAPI 直接服務，**單一 port 即可**（不需另開 Vite dev server）。

## Container 一覽

| 服務 | 用途 | Port |
|---|---|---|
| `web` | FastAPI + Vue 3 SPA（dist/ 內建） | 8080 → 8000 |
| `worker` | Celery Worker | 內部 |
| `beat` | Celery Beat 排程 | 內部 |
| `crawler` | httpx + Playwright 爬蟲 API | 內部 8001 |
| `db` | PostgreSQL 16 | 內部 5432 |
| `redis` | Celery broker / SSE pub/sub | 內部 6379 |

## 開發工作流

**後端**

```bash
cd services/web
pip install -r requirements.txt
python -m pytest          # 61 個測試
uvicorn app.main:app --reload  # 本機跑後端（需自行啟動 PG / Redis）
```

**前端 dev mode**（熱重載）

```bash
cd services/web/frontend
npm install
npm run dev               # http://localhost:5173，/api → 8080 proxy
```

**完整端到端**

```bash
docker compose up -d
docker compose exec web alembic upgrade head
# 開瀏覽器到 http://localhost:8080
# 1. /etf 新增追蹤 ETF
# 2. POST /api/admin/analyze/{date} 或等 18:30 排程
# 3. POST /api/admin/detect-signals/{date}
# 4. /  Dashboard 看排行 / /reduction 看警示
```

## 開發里程碑

- M1 基礎建設 ✅
- M2 核心分析引擎 ✅
- M3 介面與通知 ✅
- M4 回測模組
- M5 穩定化（含真實投信 Parser）

詳見規格書 §26。
