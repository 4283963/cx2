from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routers.simulation_router import router as simulation_router


app = FastAPI(
    title="音视频会议丢包补偿模拟评估工具",
    description="基于FEC前向纠错模型的网络丢包补偿仿真计算引擎",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(simulation_router, prefix="/api/v1")


@app.get("/")
async def root():
    return {
        "name": "Packet Loss FEC Simulator API",
        "version": "1.0.0",
        "docs": "/docs",
    }
