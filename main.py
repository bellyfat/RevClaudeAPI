import argparse

import fire
import uvicorn
from fastapi import FastAPI
from loguru import logger

from rev_claude.client.client_manager import ClientManager
from rev_claude.configs import LOGS_PATH
from rev_claude.lifespan import lifespan
from rev_claude.middlewares.register_middlewares import register_middleware
from rev_claude.router import router
from rev_claude.utility import get_client_status

parser = argparse.ArgumentParser()
parser.add_argument("--host", default="0.0.0.0", help="host")
parser.add_argument("--port", default=6238, help="port")
parser.add_argument("--workers", default=1, type=int, help="workers")
args = parser.parse_args()
logger.add(LOGS_PATH / "log_file.log", rotation="1 week")  # 每周轮换一次文件
app = FastAPI(lifespan=lifespan)
app = register_middleware(app)


@app.get("/health")
async def health_check():
    """简单的健康检查端点，不依赖外部服务"""
    return {"status": "healthy", "message": "RevClaudeAPI is running"}


@app.get("/api/v1/health")
async def api_health_check():
    """API版本的健康检查端点"""
    return {"status": "healthy", "message": "RevClaudeAPI is running", "version": "v1"}


@app.get("/api/v1/clients_status")
async def _get_client_status():
    basic_clients, plus_clients = ClientManager().get_clients()
    return await get_client_status(basic_clients, plus_clients)


def start_server(port=args.port, host=args.host):
    logger.info(f"Starting server at {host}:{port}")
    app.include_router(router)
    config = uvicorn.Config(app, host=host, port=port, workers=args.workers)
    server = uvicorn.Server(config=config)
    try:
        server.run()
    finally:
        logger.info("Server shutdown.")


if __name__ == "__main__":
    fire.Fire(start_server)
