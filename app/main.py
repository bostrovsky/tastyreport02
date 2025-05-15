from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.v1.endpoints import auth_router, tastytrade_router, strategy_router, position_group_router

app = FastAPI(title="TastyTrade Tracker API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router, prefix=settings.API_V1_STR)
app.include_router(tastytrade_router, prefix=settings.API_V1_STR)
app.include_router(strategy_router, prefix=settings.API_V1_STR)
app.include_router(position_group_router, prefix=settings.API_V1_STR)
