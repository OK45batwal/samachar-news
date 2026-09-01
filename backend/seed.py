import asyncio
from datetime import datetime, timezone
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .auth.auth import hash_password
from .database import async_session, init_db
from .models.models import Article, ArticleStatus, Category, FactCheckStatus, Source, User, UserRole

CATEGORIES = [
    {"name": "World", "slug": "world", "description": "International diplomacy, global treaties, and foreign policy.", "icon": "globe"},
    {"name": "Technology", "slug": "technology", "description": "Semiconductors, AI architectures, cybersecurity, and consumer tech.", "icon": "cpu"},
    {"name": "India", "slug": "india", "description": "National governance, state elections, economic reforms, and policy.", "icon": "flag"},
    {"name": "Business", "slug": "business", "description": "Global markets, central banks, corporate earnings, and trade.", "icon": "trending-up"},
    {"name": "Science", "slug": "science", "description": "Astrophysics, quantum computing, climate research, and discoveries.", "icon": "atom"},
    {"name": "Health", "slug": "health", "description": "Epidemiology, immunology breakthroughs, and public health policies.", "icon": "heart"},
    {"name": "Sports", "slug": "sports", "description": "Cricket, football, Olympics, grand slams, and global athletics.", "icon": "award"},
    {"name": "Entertainment", "slug": "entertainment", "description": "Cinema, streaming industries, arts, and cultural festivals.", "icon": "film"},
]

SOURCES = [
    {"name": "Reuters", "url": "https://www.reuters.com", "feed_url": "https://www.reutersagency.com/feed/?best-topics=world&post_type=best", "country": "Global", "rel": 98},
    {"name": "Associated Press", "url": "https://apnews.com", "feed_url": "https://feedx.net/rss/ap.xml", "country": "Global", "rel": 98},
    {"name": "BBC News", "url": "https://www.bbc.com/news", "feed_url": "http://feeds.bbci.co.uk/news/world/rss.xml", "country": "UK", "rel": 96},
    {"name": "The Hindu", "url": "https://www.thehindu.com", "feed_url": "https://www.thehindu.com/news/national/feeder/default.rss", "country": "India", "rel": 93},
    {"name": "Indian Express", "url": "https://indianexpress.com", "feed_url": "https://indianexpress.com/section/india/feed/", "country": "India", "rel": 91},
    {"name": "Bloomberg", "url": "https://www.bloomberg.com", "feed_url": "https://feeds.bloomberg.com/markets/news.rss", "country": "US", "rel": 96},
    {"name": "Nature Journal", "url": "https://www.nature.com", "feed_url": "https://www.nature.com/nature.rss", "country": "UK", "rel": 99},
    {"name": "TechCrunch", "url": "https://techcrunch.com", "feed_url": "https://techcrunch.com/feed/", "country": "US", "rel": 90},
    {"name": "MIT Technology Review", "url": "https://www.technologyreview.com", "feed_url": "https://www.technologyreview.com/feed/", "country": "US", "rel": 96},
    {"name": "ESPN", "url": "https://www.espn.com", "feed_url": "https://www.espn.com/espn/rss/news", "country": "US", "rel": 92},
]

BENCHMARK_ARTICLES = [
    # Technology
    {
        "title": "Global Semiconductor Alliance Unveils 1.4nm Photonic Chip Architecture",
        "slug": "global-semiconductor-alliance-unveils-1-4nm-photonic-chip",
        "summary": "Major semiconductor consortiums across Europe, US, and Asia have officially ratified the 1.4nm photonic node standard, delivering 45% power reduction and unprecedented AI model inference bandwidth.",
        "content": "In an official joint briefing in Geneva, leading global chip manufacturers confirmed the completion of specifications for 1.4-nanometer silicon photonic interconnects. Peer-reviewed benchmarks verify a 45% reduction in thermal dissipation while achieving 10x throughput for hyperscale transformer workloads. Independent audits from IEEE and MIT confirm physical lab validation across 12 test foundries.",
        "category_slug": "technology",
        "source_name": "Reuters",
        "fact_check_status": FactCheckStatus.VERIFIED,
        "credibility_score": 96,
        "sensationalism_score": 6,
        "key_claims": [
            {"claim": "1.4nm photonic chip specifications ratified by global consortium", "status": "Verified Fact", "evidence": "Ratified in official joint communique in Geneva"},
            {"claim": "45% reduction in thermal dissipation validated in test foundries", "status": "Data-Backed Assertion", "evidence": "IEEE & MIT independent peer-reviewed lab test data"},
            {"claim": "10x throughput enhancement for AI transformer workloads", "status": "Verified Reporting", "evidence": "Corroborated by 12 independent foundries"}
        ],
        "corroborating_sources": ["Reuters", "Associated Press", "MIT Technology Review", "BBC News"],
        "bias_spectrum": "Neutral Analytic (Wire Grade)",
        "image_url": "https://images.unsplash.com/photo-1518770660439-4636190af475?auto=format&fit=crop&w=1200&q=80",
    },
    {
        "title": "Open-Source AI Frontier Consortium Releases 100B Parameter Multilingual Model",
        "slug": "open-source-ai-frontier-consortium-releases-100b-model",
        "summary": "A coalition of European and Indian research institutions has released a fully open-weights 100-billion parameter foundation model trained with verified factual ground-truth pipelines.",
        "content": "The Open Frontier AI initiative has released model checkpoints, training data lineage, and benchmark evaluation suites for its flagship 100B parameter neural network. Independent evaluations by Stanford CRFM confirm the architecture achieves parity with proprietary commercial systems while maintaining full open-access licensing for public research.",
        "category_slug": "technology",
        "source_name": "MIT Technology Review",
        "fact_check_status": FactCheckStatus.VERIFIED,
        "credibility_score": 94,
        "sensationalism_score": 8,
        "key_claims": [
            {"claim": "100B parameter model released with full open-weights", "status": "Verified Fact", "evidence": "Public model checkpoints released on HuggingFace and Zenodo"},
            {"claim": "Independent evaluation confirms factual benchmark accuracy parity", "status": "Data-Backed Assertion", "evidence": "Stanford CRFM evaluation suite audit log"}
        ],
        "corroborating_sources": ["MIT Technology Review", "TechCrunch", "Reuters"],
        "bias_spectrum": "Neutral Analytic (Technical Audit)",
        "image_url": "https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?auto=format&fit=crop&w=1200&q=80",
    },

    # World
    {
        "title": "G20 Climate Negotiators Finalize $1.5 Trillion Clean Transition Compact",
        "slug": "g20-climate-negotiators-finalize-1-5-trillion-transition-compact",
        "summary": "Delegates representing the world's 20 largest economies have signed a binding multilateral agreement establishing sovereign green bond credit guarantees for emerging industrial economies.",
        "content": "In a historic concluding plenary in Brasilia, finance ministers from all 20 member states ratified the Multilateral Transition Facility. World Bank auditing frameworks will oversee credit issuance, with the initial tranche of $300 billion set for deployment across renewable electrification and smart grid modernization projects by Q3 2026.",
        "category_slug": "world",
        "source_name": "Associated Press",
        "fact_check_status": FactCheckStatus.VERIFIED,
        "credibility_score": 97,
        "sensationalism_score": 7,
        "key_claims": [
            {"claim": "Binding $1.5 Trillion Clean Transition Compact signed by G20 delegates", "status": "Official Statement", "evidence": "Ratified G20 Final Communique Brasilia 2026"},
            {"claim": "Initial $300 billion deployment audited by World Bank facility", "status": "Data-Backed Assertion", "evidence": "World Bank treasury filing and deployment roadmap"}
        ],
        "corroborating_sources": ["Associated Press", "Reuters", "BBC News", "Financial Times"],
        "bias_spectrum": "Neutral Analytic (Diplomatic Wire)",
        "image_url": "https://images.unsplash.com/photo-1526778548025-fa2f459cd5c1?auto=format&fit=crop&w=1200&q=80",
    },
    {
        "title": "UN Maritime Agency Adopts Mandatory Net-Zero Emission Targets for Global Shipping",
        "slug": "un-maritime-agency-adopts-net-zero-targets-shipping",
        "summary": "The International Maritime Organization has ratified universal carbon tax and alternative fuel mandates across all commercial cargo vessels exceeding 5,000 gross tonnage.",
        "content": "Following intensive negotiations in London, the IMO assembly approved Resolution MEPC.89. The regulatory framework imposes progressive greenhouse gas fuel standards from 2027, with revenue recycled into developing nation port electrification and green methanol bunkering infrastructure.",
        "category_slug": "world",
        "source_name": "Reuters",
        "fact_check_status": FactCheckStatus.VERIFIED,
        "credibility_score": 95,
        "sensationalism_score": 5,
        "key_claims": [
            {"claim": "IMO assembly ratifies universal maritime carbon standard", "status": "Official Statement", "evidence": "IMO London Plenary Resolution MEPC.89"},
            {"claim": "Applies to all commercial cargo vessels exceeding 5,000 gross tonnage", "status": "Verified Fact", "evidence": "Maritime Safety & Environment Directorate Gazette"}
        ],
        "corroborating_sources": ["Reuters", "BBC News", "The Hindu"],
        "bias_spectrum": "Neutral Analytic (Regulatory Wire)",
        "image_url": "https://images.unsplash.com/photo-1505705694340-019e1e335916?auto=format&fit=crop&w=1200&q=80",
    },

    # India
    {
        "title": "India Completes Phase-4 Expansion of National Green Hydrogen Grid",
        "slug": "india-completes-phase-4-expansion-green-hydrogen-grid",
        "summary": "The Ministry of New and Renewable Energy has announced the commercial commissioning of 12 green hydrogen production hubs, targeting 5 million metric tonnes annual capacity by 2030.",
        "content": "Official government gazette notifications confirm the operational launch of 12 integrated green hydrogen hubs across Gujarat, Maharashtra, and Odisha. Industry audits verify that 1.2 GW of dedicated solar-wind hybrid infrastructure has been energized, with supply contracts signed with national steel and fertilizer corporations.",
        "category_slug": "india",
        "source_name": "The Hindu",
        "fact_check_status": FactCheckStatus.VERIFIED,
        "credibility_score": 94,
        "sensationalism_score": 8,
        "key_claims": [
            {"claim": "12 integrated green hydrogen hubs commercially commissioned", "status": "Official Statement", "evidence": "Ministry of New and Renewable Energy Gazette Notification"},
            {"claim": "Target of 5 million metric tonnes annual capacity by 2030", "status": "Data-Backed Assertion", "evidence": "National Green Hydrogen Mission roadmap documents"},
            {"claim": "1.2 GW dedicated hybrid renewable capacity energized", "status": "Verified Fact", "evidence": "Audited grid interconnection logs from Power Grid Corp"}
        ],
        "corroborating_sources": ["The Hindu", "Indian Express", "Reuters", "Bloomberg"],
        "bias_spectrum": "Neutral Analytic (Policy Review)",
        "image_url": "https://images.unsplash.com/photo-1497435334941-8c899ee9e8e9?auto=format&fit=crop&w=1200&q=80",
    },
    {
        "title": "ISRO and European Space Agency Partner for Lunar Polar Exploration Rover",
        "slug": "isro-esa-partner-lunar-polar-rover-chandrayaan",
        "summary": "ISRO and ESA scientists have completed integrated vacuum thermal testing for the upcoming Lupex scientific drill payload designed for water ice extraction.",
        "content": "Scientists at ISRO Satellite Integration Centre in Bengaluru verified mechanical compatibility for the 350kg scientific rover platform. The mission will deploy deep subterranean sensors to measure lunar regolith volatile compositions in permanently shadowed polar craters.",
        "category_slug": "india",
        "source_name": "Indian Express",
        "fact_check_status": FactCheckStatus.VERIFIED,
        "credibility_score": 96,
        "sensationalism_score": 6,
        "key_claims": [
            {"claim": "Integrated thermal vacuum testing completed for polar drill payload", "status": "Verified Fact", "evidence": "ISRO-ESA joint technical mission bulletin"},
            {"claim": "Targeting water ice volatile analysis in permanently shadowed craters", "status": "Data-Backed Assertion", "evidence": "Published payload instrumentation specs"}
        ],
        "corroborating_sources": ["Indian Express", "The Hindu", "Nature Journal"],
        "bias_spectrum": "Neutral Analytic (Science & Space)",
        "image_url": "https://images.unsplash.com/photo-1446776811953-b23d57bd21aa?auto=format&fit=crop&w=1200&q=80",
    },

    # Business
    {
        "title": "Central Banks Finalize Cross-Border Instant Settlement Protocol",
        "slug": "central-banks-finalize-cross-border-instant-settlement-protocol",
        "summary": "Project Nexus, led by the Bank for International Settlements and five central banks, has officially transitioned from pilot to multilateral production for sub-second cross-border payments.",
        "content": "In a formal joint declaration at Basel, the Bank for International Settlements (BIS) alongside monetary authorities from Singapore, India, Eurozone, and Japan confirmed the activation of the multilateral instant settlement network. Transaction fees are capped at 0.05%, with atomic settlement eliminating counterparty credit risk across currency corridors.",
        "category_slug": "business",
        "source_name": "Bloomberg",
        "fact_check_status": FactCheckStatus.VERIFIED,
        "credibility_score": 97,
        "sensationalism_score": 7,
        "key_claims": [
            {"claim": "Project Nexus instant settlement network enters multilateral production", "status": "Official Statement", "evidence": "BIS formal joint declaration at Basel"},
            {"claim": "Transaction fees capped at 0.05% across participating corridors", "status": "Data-Backed Assertion", "evidence": "Published tariff schedules in central bank filings"},
            {"claim": "Atomic sub-second settlement eliminates counterparty credit risk", "status": "Verified Fact", "evidence": "Operational test logs verified across 5 central banks"}
        ],
        "corroborating_sources": ["Bloomberg", "Financial Times", "Reuters", "The Hindu"],
        "bias_spectrum": "Neutral Analytic (Financial Wire)",
        "image_url": "https://images.unsplash.com/photo-1611974789855-9c2a0a7236a3?auto=format&fit=crop&w=1200&q=80",
    },

    # Science
    {
        "title": "James Webb Telescope Detects Atmospheric Water Vapor on Habitable-Zone Exoplanet",
        "slug": "james-webb-telescope-detects-atmospheric-water-vapor-exoplanet",
        "summary": "Spectroscopic observations published in Nature confirm atmospheric water vapor and carbon dioxide signatures on exoplanet K2-18b within the habitable zone of its host star.",
        "content": "Astrophysicists analyzing transit spectroscopy data from the James Webb Space Telescope have published confirmed detections of methane, carbon dioxide, and water vapor absorption lines. The 5-sigma statistical significance rules out false-positive instrumental artifacts, marking one of the clearest atmospheric characterizations of a temperate sub-Neptune exoplanet to date.",
        "category_slug": "science",
        "source_name": "Nature Journal",
        "fact_check_status": FactCheckStatus.VERIFIED,
        "credibility_score": 99,
        "sensationalism_score": 5,
        "key_claims": [
            {"claim": "Atmospheric water vapor and CO2 detected on K2-18b", "status": "Verified Fact", "evidence": "Peer-reviewed publication in Nature journal"},
            {"claim": "Statistical significance exceeds 5-sigma threshold", "status": "Data-Backed Assertion", "evidence": "Quantitative analysis of JWST NIRISS and NIRSpec data"}
        ],
        "corroborating_sources": ["Nature Journal", "BBC News", "Associated Press", "NASA Science"],
        "bias_spectrum": "Neutral Analytic (Scientific Peer Review)",
        "image_url": "https://images.unsplash.com/photo-1451187580459-43490279c0fa?auto=format&fit=crop&w=1200&q=80",
    },

    # Health
    {
        "title": "WHO Reports 78% Drop in Global Malaria Mortality Following Dual-Vaccine Rollout",
        "slug": "who-reports-78-percent-drop-malaria-mortality-vaccine-rollout",
        "summary": "Comprehensive public health surveillance across 18 sub-Saharan nations reveals dramatic declines in pediatric severe malaria after wide deployment of RTS,S and R21 vaccines.",
        "content": "The World Health Organization (WHO) and Gavi have released the 24-month post-implementation epidemiological evaluation for the R21/Matrix-M and RTS,S malaria vaccines. In high-transmission districts, child mortality fell by 78%, accompanied by an 82% reduction in hospital admissions. Cold-chain distribution metrics maintained a 99.4% efficacy adherence rate.",
        "category_slug": "health",
        "source_name": "BBC News",
        "fact_check_status": FactCheckStatus.VERIFIED,
        "credibility_score": 98,
        "sensationalism_score": 6,
        "key_claims": [
            {"claim": "78% reduction in pediatric severe malaria mortality", "status": "Data-Backed Assertion", "evidence": "WHO 24-month epidemiological surveillance report"},
            {"claim": "Deployment across 18 nations in high-transmission zones", "status": "Official Statement", "evidence": "Joint WHO and Gavi immunization registry"}
        ],
        "corroborating_sources": ["BBC News", "Reuters", "Nature Journal", "Associated Press"],
        "bias_spectrum": "Neutral Analytic (Global Health)",
        "image_url": "https://images.unsplash.com/photo-1584515979956-d9f6e5d09982?auto=format&fit=crop&w=1200&q=80",
    },

    # Sports
    {
        "title": "ICC Confirms Universal Automated Ball-Tracking & Real-Time Decision System",
        "slug": "icc-confirms-universal-automated-ball-tracking-system",
        "summary": "The International Cricket Council has ratified an AI-assisted high-framerate optical tracking system across all international test and limited-overs matches.",
        "content": "In an official technical committee release from Dubai, the ICC verified that the next-generation 240fps multi-camera tracking system reduces decision latency to under 3.5 seconds while delivering sub-millimeter trajectory precision across ball-impact and boundary reviews.",
        "category_slug": "sports",
        "source_name": "ESPN",
        "fact_check_status": FactCheckStatus.VERIFIED,
        "credibility_score": 95,
        "sensationalism_score": 8,
        "key_claims": [
            {"claim": "240fps multi-camera system ratified for all international fixtures", "status": "Official Statement", "evidence": "ICC Dubai Technical Committee Press Briefing"},
            {"claim": "Decision latency reduced to under 3.5 seconds with sub-millimeter precision", "status": "Data-Backed Assertion", "evidence": "Independent optical validation testing report"}
        ],
        "corroborating_sources": ["ESPN", "BBC News", "The Hindu"],
        "bias_spectrum": "Neutral Analytic (Sports Technology)",
        "image_url": "https://images.unsplash.com/photo-1540747913346-19e32dc3e97e?auto=format&fit=crop&w=1200&q=80",
    },

    # Entertainment
    {
        "title": "Global Archival Initiative Restores 500 Lost Classics in 8K Neural Resolution",
        "slug": "global-archival-initiative-restores-500-lost-classics",
        "summary": "A partnership between international film archives in France, India, and Japan has completed chemical and optical neural reconstruction of 500 historical cinematic works.",
        "content": "The International Film Preservation Federation (FIAF) confirmed the archival completion of 500 fragile celluloid masters dating from 1910 to 1965. Custom optical spectrometers and neural debayering algorithms eliminated nitrate degradation artifacts while preserving original grain chemistry.",
        "category_slug": "entertainment",
        "source_name": "Associated Press",
        "fact_check_status": FactCheckStatus.VERIFIED,
        "credibility_score": 96,
        "sensationalism_score": 5,
        "key_claims": [
            {"claim": "500 celluloid masters preserved and reconstructed in 8K", "status": "Verified Fact", "evidence": "FIAF International Film Archive Registry Catalog"},
            {"claim": "Original grain chemistry preserved with zero generative hallucination", "status": "Data-Backed Assertion", "evidence": "Published technical whitepaper by French National Archives"}
        ],
        "corroborating_sources": ["Associated Press", "BBC News", "Reuters"],
        "bias_spectrum": "Neutral Analytic (Arts & Culture)",
        "image_url": "https://images.unsplash.com/photo-1489599849927-2ee91cede3ba?auto=format&fit=crop&w=1200&q=80",
    }
]


async def seed_database():
    """Seed initial categories, sources, admin user, and verified benchmark stories."""
    await init_db()

    async with async_session() as db:
        check_user = await db.execute(select(User).where(User.email == "admin@samachar.news"))
        if check_user.scalar_one_or_none():
            return

        # 1. Seed Users
        admin_user = User(
            email="admin@samachar.news",
            username="admin",
            hashed_password=hash_password("AdminPass123!"),
            full_name="Samachar Chief Editor",
            role=UserRole.ADMIN,
        )
        demo_user = User(
            email="reader@samachar.news",
            username="reader",
            hashed_password=hash_password("ReaderPass123!"),
            full_name="Alex Mercer",
            role=UserRole.USER,
        )
        db.add_all([admin_user, demo_user])
        await db.flush()

        # 2. Seed Categories
        cat_map = {}
        for c in CATEGORIES:
            cat = Category(name=c["name"], slug=c["slug"], description=c["description"], icon=c["icon"])
            db.add(cat)
            await db.flush()
            cat_map[c["slug"]] = cat.id

        # 3. Seed Sources
        src_map = {}
        for s in SOURCES:
            src = Source(
                name=s["name"],
                url=s["url"],
                feed_url=s["feed_url"],
                country=s["country"],
                reliability_score=s["rel"],
            )
            db.add(src)
            await db.flush()
            src_map[s["name"]] = src.id

        # 4. Seed Benchmark Verified Articles
        for a in BENCHMARK_ARTICLES:
            art = Article(
                title=a["title"],
                slug=a["slug"],
                summary=a["summary"],
                content=a["content"],
                image_url=a["image_url"],
                source_url=f"https://samachar.news/verified/{a['slug']}",
                author="Editorial Intelligence Wire",
                status=ArticleStatus.PUBLISHED,
                sentiment_score=20,
                fact_check_status=a["fact_check_status"],
                credibility_score=a["credibility_score"],
                sensationalism_score=a["sensationalism_score"],
                key_claims=a["key_claims"],
                corroborating_sources=a["corroborating_sources"],
                bias_spectrum=a["bias_spectrum"],
                category_id=cat_map.get(a["category_slug"]),
                source_id=src_map.get(a["source_name"]),
                published_at=datetime.now(timezone.utc).replace(tzinfo=None),
            )
            db.add(art)

        await db.commit()


if __name__ == "__main__":
    asyncio.run(seed_database())
