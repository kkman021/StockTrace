from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

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
