from fastapi import FastAPI
from app.routes.flights import router as flights_router
from app.routes.analytics import router as analytics_router

app = FastAPI(
    title="FlightPulse",
    description="Asynchronous flight data pipeline and analytics API",
    version="1.0.0",
)

app.include_router(flights_router)
app.include_router(analytics_router)

@app.get("/", tags=["Health"])
def root():
    return {
        "message": "FlightPulse API is running",
        "docs": "/docs",
    }


@app.get("/health", tags=["Health"])
def health_check():
    return {"status": "healthy"}
