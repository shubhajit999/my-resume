from fastapi import APIRouter

router = APIRouter()


@router.get("/health", status_code=200)
def health_check() -> dict:
    """
    Health check endpoint returning system status.
    """
    return {"status": "ok"}
