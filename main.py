import fastapi
from fastapi import FastAPI
from dotenv import load_dotenv
from app.routes import auth, services, exploits, reports
from app.services.cron import run_cron
from fastapi.middleware.cors import CORSMiddleware

# run_cron()

load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://185.229.87.176:3000", "http://localhost:3000"],  # Allow specific origin
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods
    allow_headers=["*"],  # Allow all headers
)

app.include_router(auth.router, prefix="/auth", tags=["Auth"])
app.include_router(services.router, prefix="/services", tags=["Services"])
app.include_router(exploits.router, prefix="/exploits", tags=["Exploits"])
app.include_router(reports.router, prefix="/reports", tags=["Reports"])
