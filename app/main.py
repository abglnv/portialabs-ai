import fastapi
from fastapi import FastAPI
from dotenv import load_dotenv
from .routes import auth, services, exploits, reports
from .services.cron import run_cron

# run_cron()

load_dotenv()

app = FastAPI()

app.include_router(auth.router, prefix="/auth", tags=["Auth"])
app.include_router(services.router, prefix="/services", tags=["Services"])
app.include_router(exploits.router, prefix="/exploits", tags=["Exploits"])
app.include_router(reports.router, prefix="/reports", tags=["Reports"])