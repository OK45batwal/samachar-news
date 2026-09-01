from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..ai.fact_checker import verify_custom_claim
from ..database import get_db
from ..models.models import FactCheckQuery
from ..schemas import FactCheckRequest, FactCheckResponse

router = APIRouter(prefix="/api/fact-check", tags=["fact-check"])


@router.post("/verify", response_model=FactCheckResponse)
async def verify_claim(body: FactCheckRequest, db: AsyncSession = Depends(get_db)):
    """Interactive Fact-Checking endpoint for user-submitted claims, statements, or news headlines."""
    query = (body.query or body.claim or "").strip()
    if not query:
        raise HTTPException(status_code=400, detail="Query or claim text cannot be empty")

    result = verify_custom_claim(query)

    # Save query to history
    entry = FactCheckQuery(
        query_text=query,
        query_type=body.query_type,
        verdict=result["verdict"],
        credibility_score=result["credibility_score"],
        sensationalism_score=result["sensationalism_score"],
        analysis=result["analysis"],
        claims_breakdown=result["claims_breakdown"],
        corroborated_sources=result["corroborated_sources"],
    )
    db.add(entry)
    await db.commit()

    return FactCheckResponse(
        verdict=result["verdict"],
        credibility_score=result["credibility_score"],
        sensationalism_score=result["sensationalism_score"],
        analysis=result["analysis"],
        claims_breakdown=result["claims_breakdown"],
        corroborated_sources=result["corroborated_sources"],
        created_at=entry.created_at,
    )


@router.get("/recent", response_model=List[FactCheckResponse])
async def get_recent_fact_checks(db: AsyncSession = Depends(get_db)):
    """Retrieve recently analyzed and verified fact-check queries."""
    result = await db.execute(select(FactCheckQuery).order_by(desc(FactCheckQuery.created_at)).limit(10))
    queries = result.scalars().all()
    return [
        FactCheckResponse(
            verdict=q.verdict,
            credibility_score=q.credibility_score,
            sensationalism_score=q.sensationalism_score,
            analysis=q.analysis,
            claims_breakdown=q.claims_breakdown or [],
            corroborated_sources=q.corroborated_sources or [],
            created_at=q.created_at,
        )
        for q in queries
    ]
