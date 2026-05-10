import os

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.routers import admin, backtest, config, consensus, etf, signals


app = FastAPI(
    title="ETF Radar",
    version="0.1.0",
    description="主動式 ETF 偵測雷達 - 共識訊號量化系統",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(etf.router, prefix="/api/etf", tags=["etf"])
app.include_router(consensus.router, prefix="/api/consensus", tags=["consensus"])
app.include_router(signals.router, prefix="/api/signals", tags=["signals"])
app.include_router(config.router, prefix="/api/config", tags=["config"])
app.include_router(backtest.router, prefix="/api/backtest", tags=["backtest"])
app.include_router(admin.router, prefix="/api/admin", tags=["admin"])


@app.get("/health")
def health():
    return {"status": "ok"}


# 在 production image 中，前端 dist/ 已透過 multi-stage build 複製到 /app/static
# dev 環境下此目錄不存在，跳過靜態服務（前端用 npm run dev 走 Vite proxy）
STATIC_DIR = os.environ.get("STATIC_DIR", "/app/static")
ASSETS_DIR = os.path.join(STATIC_DIR, "assets")
INDEX_HTML = os.path.join(STATIC_DIR, "index.html")


if os.path.isdir(STATIC_DIR) and os.path.isfile(INDEX_HTML):
    if os.path.isdir(ASSETS_DIR):
        app.mount("/assets", StaticFiles(directory=ASSETS_DIR), name="assets")

    # SPA fallback：所有未匹配 API 的路徑都回 index.html，讓 vue-router 接手。
    # /api/* 已由 include_router 註冊在前，會優先命中。
    @app.get("/{full_path:path}", include_in_schema=False)
    async def spa_fallback(full_path: str):
        if full_path.startswith("api/"):
            raise HTTPException(status_code=404, detail="Not found")
        # 嘗試先當靜態檔案（favicon、icons 等）
        candidate = os.path.join(STATIC_DIR, full_path)
        if full_path and os.path.isfile(candidate):
            return FileResponse(candidate)
        return FileResponse(INDEX_HTML)
