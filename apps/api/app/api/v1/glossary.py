from fastapi import APIRouter, Response

from app.knowledge.loader import load_glossary
from app.schemas.glossary import GlossaryResponse

router = APIRouter()


@router.get("/glossary", response_model=GlossaryResponse)
def glossary(response: Response) -> GlossaryResponse:
    # Static content that only changes with a deploy.
    response.headers["Cache-Control"] = "public, max-age=3600"
    return GlossaryResponse(entries=list(load_glossary()))
