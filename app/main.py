import logging
import uvicorn
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.config import settings
from app.schemas import ProspectDiscoveryRequest, ProspectDiscoveryResponse
from app.services.prospect_service import prospect_service

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("main")

app = FastAPI(
    title="AI-Powered Multi-Platform Prospect Discovery API",
    description="Discovers and consolidates public profiles and contact information across Google, LinkedIn, X, YouTube, Instagram, WhatsApp, Facebook, Email, and Threads based on natural language queries.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Enable CORS for cross-origin frontend requests and evaluations
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", tags=["Health"])
async def root():
    return {
        "status": "online",
        "service": "AI-Powered Multi-Platform Prospect Discovery API",
        "docs": "/docs",
        "endpoint": "/prospect-discovery"
    }


@app.get("/health", tags=["Health"])
async def health_check():
    return {"status": "healthy"}


@app.post(
    "/prospect-discovery",
    response_model=ProspectDiscoveryResponse,
    status_code=status.HTTP_200_OK,
    tags=["Prospect Discovery"],
    summary="Discover multi-platform prospects from a natural language query"
)
async def discover_prospects(payload: ProspectDiscoveryRequest):
    """
    Accepts a natural-language search query, parses the intent & location,
    discovers public profiles across 9 platforms, extracts contacts,
    consolidates duplicates, and returns structured prospects.
    """
    try:
        query = payload.query.strip()
        if not query:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Query cannot be empty."
            )

        response = await prospect_service.discover_prospects(query)
        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error during prospect discovery: {e}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "success": False,
                "query": payload.query,
                "total_prospects": 0,
                "prospects": [],
                "error": "Failed to complete discovery due to internal processing error."
            }
        )


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=(settings.ENVIRONMENT == "development")
    )
