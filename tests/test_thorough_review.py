import pytest
from httpx import ASGITransport, AsyncClient
from backend.app import app

@pytest.mark.asyncio
async def test_full_throttle_backend_routes():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Health check
        h_res = await client.get("/api/health")
        assert h_res.status_code == 200
        assert h_res.json()["status"] == "healthy"

        # 2. News listing with various parameters
        res_all = await client.get("/api/news/")
        assert res_all.status_code == 200
        data = res_all.json()
        assert "articles" in data
        assert len(data["articles"]) > 0

        # Verified only filter
        res_ver = await client.get("/api/news/?verified_only=true")
        assert res_ver.status_code == 200

        # Category filter
        res_cat = await client.get("/api/news/?category=technology")
        assert res_cat.status_code == 200

        # Search filter
        res_search = await client.get("/api/news/?q=semiconductor")
        assert res_search.status_code == 200

        # Sort options
        for s in ["latest", "trending", "credibility"]:
            res_sort = await client.get(f"/api/news/?sort={s}")
            assert res_sort.status_code == 200

        # 3. Trending & Verified breaking
        res_trend = await client.get("/api/news/trending")
        assert res_trend.status_code == 200

        res_break = await client.get("/api/news/verified")
        assert res_break.status_code == 200

        # 4. Categories & Sources & Stats
        res_cats = await client.get("/api/news/categories")
        assert res_cats.status_code == 200
        assert len(res_cats.json()) == 8

        res_srcs = await client.get("/api/news/sources")
        assert res_srcs.status_code == 200

        res_stats = await client.get("/api/news/stats")
        assert res_stats.status_code == 200
        assert res_stats.json()["total_articles"] > 0

        # 5. Single article lookup and 404 test
        first_id = data["articles"][0]["id"]
        res_single = await client.get(f"/api/news/{first_id}")
        assert res_single.status_code == 200
        assert res_single.json()["id"] == first_id

        res_404 = await client.get("/api/news/999999")
        assert res_404.status_code == 404

        # 6. Fact Check Tool: Normal statement, Clickbait statement, and recent checks
        res_fc_valid = await client.post(
            "/api/fact-check/verify",
            json={"claim": "WHO reports 78% drop in pediatric malaria mortality following vaccine rollout"}
        )
        assert res_fc_valid.status_code == 200
        fc_data = res_fc_valid.json()
        assert fc_data["credibility_score"] >= 80

        res_fc_clickbait = await client.post(
            "/api/fact-check/verify",
            json={"claim": "SHOCKING SECRET! Doctors are furious over this miracle trick that changes everything!"}
        )
        assert res_fc_clickbait.status_code == 200
        assert res_fc_clickbait.json()["sensationalism_score"] >= 60

        res_recent = await client.get("/api/fact-check/recent")
        assert res_recent.status_code == 200
        assert len(res_recent.json()) > 0
