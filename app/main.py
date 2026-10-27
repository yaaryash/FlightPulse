
from fastapi import FastAPI, HTTPException
from app.routes.flights import router as flights_router
from app.routes.analytics import router as analytics_router
from app.pipeline import run_pipeline

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


@app.post("/pipeline/run", tags=["Pipeline"])
async def trigger_pipeline():
    try:
        return await run_pipeline()
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail="Pipeline execution failed. Check application logs.",
        ) from exc
