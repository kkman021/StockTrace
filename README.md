# 主動式 ETF 偵測雷達 (ETF Radar)

量化「多位基金經理人同步加/減碼同一標的」的共識訊號系統。

> 完整產品規格：[`docs/product_plan.md`](docs/product_plan.md)

## 狀態

骨架 (Skeleton) — 各 container / 路由 / 任務 / 前端頁面框架已建立，業務邏輯標 `TODO` 待實作。

## 技術棧

FastAPI · Vue 3 · PostgreSQL 16 · Celery 5 · Redis 7 · httpx · Playwright · SQLAlchemy 2 · pandas 2 · Docker Compose

## 快速開始

```bash
cp .env.example .env
# 編輯 .env，至少設定 POSTGRES_PASSWORD

docker compose build
docker compose up -d

# 套用 schema
docker compose exec web alembic upgrade head
```

存取點：

- Web UI / API：<http://localhost:8080>
- API docs：<http://localhost:8080/docs>

## Container 一覽

| 服務 | 用途 | Port |
|---|---|---|
| `web` | FastAPI + Vue 3 SPA | 8080 → 8000 |
| `worker` | Celery Worker | 內部 |
| `beat` | Celery Beat 排程 | 內部 |
| `crawler` | httpx + Playwright 爬蟲 API | 內部 8001 |
| `db` | PostgreSQL 16 | 內部 5432 |
| `redis` | Celery broker / backend | 內部 6379 |

## 開發里程碑

- M1 基礎建設（骨架已完成本階段一部分）
- M2 核心分析引擎
- M3 介面與通知
- M4 回測模組
- M5 穩定化

詳見規格書 §26。
