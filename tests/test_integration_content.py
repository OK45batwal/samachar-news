import pytest
from httpx import ASGITransport, AsyncClient

from backend.app import app


@pytest.mark.asyncio
async def test_list_news_articles():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get("/api/news/")
        assert res.status_code == 200
        data = res.json()
        assert "articles" in data
        assert "total" in data
        assert len(data["articles"]) > 0
        first = data["articles"][0]
        assert "credibility_score" in first
        assert "fact_check_status" in first


@pytest.mark.asyncio
async def test_fact_check_tool_endpoint():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.post(
            "/api/fact-check/verify",
            json={"query": "Ministry of Transport announced $1.2B highway modernization budget."}
        )
        assert res.status_code == 200
        data = res.json()
        assert "verdict" in data
        assert "credibility_score" in data
        assert "analysis" in data
        assert "claims_breakdown" in data


@pytest.mark.asyncio
async def test_categories_and_sources():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        cat_res = await client.get("/api/news/categories")
        assert cat_res.status_code == 200
        assert len(cat_res.json()) >= 6

        src_res = await client.get("/api/news/sources")
        assert src_res.status_code == 200
        assert len(src_res.json()) >= 5


@pytest.mark.asyncio
async def test_search_like_wildcard_escaping():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Wildcards like % and _ should be safely escaped rather than matching everything blindly
        res = await client.get("/api/news/?q=%25%25%25")
        assert res.status_code == 200
        data = res.json()
        assert "articles" in data

        res_source = await client.get("/api/news/?source=___")
        assert res_source.status_code == 200


@pytest.mark.asyncio
async def test_platform_stats_dynamic_countries():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get("/api/news/stats")
        assert res.status_code == 200
        data = res.json()
        assert "countries_covered" in data
        assert isinstance(data["countries_covered"], int)
        assert data["countries_covered"] >= 1


@pytest.mark.asyncio
async def test_nextgen_article_endpoints():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Get an existing article ID
        list_res = await client.get("/api/news/")
        assert list_res.status_code == 200
        articles = list_res.json()["articles"]
        assert len(articles) > 0
        art_id = articles[0]["id"]

        # Test Cognitive Depth endpoint
        depth_res = await client.get(f"/api/news/{art_id}/depth")
        assert depth_res.status_code == 200
        depth_data = depth_res.json()
        assert "radar" in depth_data
        assert "brief" in depth_data
        assert "deep" in depth_data
        assert "eli5" in depth_data
        assert len(depth_data["radar"]["takeaways"]) > 0

        # Test Socratic Ask Copilot endpoint
        ask_res = await client.post(
            f"/api/news/{art_id}/ask",
            json={"question": "What are the counter-arguments?", "selected_context": "primary claim"}
        )
        assert ask_res.status_code == 200
        ask_data = ask_res.json()
        assert "answer" in ask_data
        assert "confidence_score" in ask_data
        assert "evidence_tag" in ask_data

        # Test Perspective Prism endpoint
        persp_res = await client.get(f"/api/news/{art_id}/perspectives")
        assert persp_res.status_code == 200
        persp_data = persp_res.json()
        assert "consensus_points" in persp_data
        assert "perspectives" in persp_data
        assert "omission_radar" in persp_data

        # Test Personal Impact endpoint
        impact_res = await client.post(
            f"/api/news/{art_id}/impact",
            json={"persona": "developer"}
        )
        assert impact_res.status_code == 200
        impact_data = impact_res.json()
        assert "impact_level" in impact_data
        assert "takeaway" in impact_data
        assert "action_item" in impact_data
