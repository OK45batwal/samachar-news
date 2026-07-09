"""Inline demo article seeder — avoids cross-package import issues."""
import random
from datetime import datetime, timedelta

from sqlalchemy import select

from .database import async_session, init_db
from .models.models import Article, ArticleStatus, Category, Source

DEMO_IMAGES = [
    "https://images.unsplash.com/photo-1611974789855-9c2a0a7236a3?w=800&q=80",
    "https://images.unsplash.com/photo-1504711434969-e33886168d8c?w=800&q=80",
    "https://images.unsplash.com/photo-1451187580459-43490279c0fa?w=800&q=80",
    "https://images.unsplash.com/photo-1526374965328-7f61d4dc18c5?w=800&q=80",
    "https://images.unsplash.com/photo-1461749280684-dccba630e2f6?w=800&q=80",
    "https://images.unsplash.com/photo-1550751827-4bd374c3f58b?w=800&q=80",
    "https://images.unsplash.com/photo-1532094349884-543bc11b234d?w=800&q=80",
    "https://images.unsplash.com/photo-1485827404703-89b55fcc595e?w=800&q=80",
    "https://images.unsplash.com/photo-1573164713988-8665fc963f03?w=800&q=80",
    "https://images.unsplash.com/photo-1541872703-74c5e44368f9?w=800&q=80",
    "https://images.unsplash.com/photo-1517245386807-bb43f82c33c4?w=800&q=80",
    "https://images.unsplash.com/photo-1504639725590-34d0984388bd?w=800&q=80",
    "https://images.unsplash.com/photo-1451187580459-43490279c0fa?w=800&q=80",
    "https://images.unsplash.com/photo-1526374965328-7f61d4dc18c5?w=800&q=80",
    "https://images.unsplash.com/photo-1461749280684-dccba630e2f6?w=800&q=80",
    "https://images.unsplash.com/photo-1611974789855-9c2a0a7236a3?w=800&q=80",
    "https://images.unsplash.com/photo-1550751827-4bd374c3f58b?w=800&q=80",
    "https://images.unsplash.com/photo-1532094349884-543bc11b234d?w=800&q=80",
    "https://images.unsplash.com/photo-1485827404703-89b55fcc595e?w=800&q=80",
    "https://images.unsplash.com/photo-1573164713988-8665fc963f03?w=800&q=80",
    "https://images.unsplash.com/photo-1504711434969-e33886168d8c?w=800&q=80",
    "https://images.unsplash.com/photo-1541872703-74c5e44368f9?w=800&q=80",
    "https://images.unsplash.com/photo-1517245386807-bb43f82c33c4?w=800&q=80",
]

DEMO_CONTENT = {
    "business": "<p>Markets showed strong momentum this quarter as investor confidence returned to pre-pandemic levels. The Federal Reserve's measured approach to monetary policy has been broadly praised by economists, though some warn of inflation risks ahead.</p><p>Key sectors driving growth include technology, healthcare, and renewable energy. Analysts project a 3.2% GDP growth for the current fiscal year, exceeding earlier forecasts. Corporate earnings reports have largely beaten expectations, with particular strength in the tech sector.</p><h2>Market Analysis</h2><p>Trading volumes remain elevated as institutional investors increase their positions. The S&P 500 has gained 12% year-to-date, while the tech-heavy Nasdaq has surged 18%. Bond yields have stabilized after the recent volatility, providing a supportive backdrop for equities.</p><blockquote>The current market environment presents a compelling opportunity for long-term investors.— Chief Market Strategist</blockquote><p>International markets have also performed well, with European and Asian indices reaching multi-year highs. The coordinated global recovery continues to support cross-border investment flows.</p>",
    "technology": "<p>A groundbreaking development in artificial intelligence is set to transform how businesses operate. The new platform leverages advanced machine learning algorithms to automate complex decision-making processes.</p><p>Industry experts suggest this could lead to productivity gains of up to 40% in knowledge-worker tasks. Major tech companies have already announced plans to integrate similar systems into their product offerings.</p><h2>How It Works</h2><p>The system uses a multi-layered neural network trained on billions of data points. Unlike previous approaches, it can generalize across domains without requiring task-specific fine-tuning. This breakthrough was achieved through a novel architecture that combines transformer-based processing with reinforcement learning.</p><h2>Industry Impact</h2><p>Early adopters report significant improvements in efficiency and accuracy. The technology is being deployed across healthcare diagnostics, financial modeling, supply chain optimization, and creative content generation.</p><p>Venture capital funding in AI startups reached an all-time high of $45 billion this year, signaling strong confidence in the sector's growth trajectory.</p>",
    "science": "<p>Scientists have announced a major breakthrough that could reshape our understanding of fundamental physics. The discovery, made at a leading research facility, opens new possibilities for technological applications.</p><p>The research team spent over five years conducting experiments and validating their findings through peer review. The results represent a significant step forward in the field.</p><h2>Research Methodology</h2><p>The team used advanced imaging techniques and computational modeling to observe phenomena at unprecedented scales. Their findings challenge several long-held assumptions in the field and suggest new directions for future research.</p><blockquote>This is the kind of discovery that comes once in a generation — it fundamentally changes how we think about the problem.</blockquote><p>The implications extend beyond pure science, with potential applications in energy production, materials science, and medical imaging. Several patents have already been filed based on the research.</p>",
    "world": "<p>International leaders have gathered for a landmark summit addressing global challenges. The conference aims to establish新的 frameworks for cooperation on climate change, trade, and security.</p><p>Delegates from over 100 nations are participating in the week-long event, which has been described as the most consequential diplomatic gathering of the decade. Key agenda items include emissions reduction targets, digital trade rules, and pandemic preparedness.</p><h2>Key Outcomes</h2><p>Early reports indicate progress on several fronts. A joint declaration on climate action has been signed by 75 nations, committing to accelerated emissions reductions. Trade ministers have reached preliminary agreements on digital services taxation and data flow regulations.</p><p>However, disagreements remain on security issues, with several nations calling for reformed international institutions to better reflect contemporary geopolitical realities.</p>",
    "health": "<p>New research published in a leading medical journal reveals promising results for a novel treatment approach. The study, conducted across multiple medical centers, shows significant improvements in patient outcomes.</p><p>The treatment targets previously hard-to-reach cellular mechanisms, offering hope for patients with conditions that have limited therapeutic options. Clinical trials demonstrated a 60% improvement rate compared to standard care.</p><h2>Clinical Trial Results</h2><p>The double-blind, placebo-controlled study involved 2,400 participants across 12 countries. Results showed a 47% reduction in symptoms among the treatment group, with minimal side effects reported.</p><p>Healthcare systems worldwide are evaluating the findings for potential integration into standard treatment protocols. Regulatory approval processes are expected to begin next quarter.</p>",
    "sports": "<p>In a thrilling conclusion to the season, underdogs clinched the championship in dramatic fashion. The deciding match drew record television audiences and captivated fans worldwide.</p><p>The victory caps an extraordinary journey for a team that was written off by pundits at the start of the season. Key players delivered career-defining performances when it mattered most.</p><h2>Match Summary</h2><p>The final was a tense affair, with both sides showing exceptional skill and determination. The winning score came in the final moments, sparking jubilant celebrations among fans. Analysts have called it one of the greatest finals in the sport's history.</p><p>Viewership data shows the match was streamed by over 50 million people globally, setting new records for the platform.</p>",
    "entertainment": "<p>The entertainment industry is experiencing a creative renaissance as new talent and technologies reshape how stories are told. Streaming platforms are investing heavily in original content, leading to a golden age of television and film production.</p><p>Industry revenue has grown 22% year-over-year, driven by expanding international markets and innovative content formats. The line between traditional cinema and digital platforms continues to blur.</p><h2>Trending Now</h2><p>Several groundbreaking projects are generating buzz ahead of their release. A highly anticipated series from a renowned director promises to push creative boundaries. Meanwhile, indie productions are finding unprecedented success through digital distribution channels.</p><p>Award season predictions are already generating debate among critics, with several films emerging as early frontrunners.</p>",
}

CATEGORY_IMAGES = {
    "business": "https://images.unsplash.com/photo-1611974789855-9c2a0a7236a3?w=800&q=80",
    "technology": "https://images.unsplash.com/photo-1518770660439-4636190af475?w=800&q=80",
    "science": "https://images.unsplash.com/photo-1451187580459-43490279c0fa?w=800&q=80",
    "world": "https://images.unsplash.com/photo-1452421822248-d4c2b47f0c81?w=800&q=80",
    "health": "https://images.unsplash.com/photo-1532938911079-1b06ac7ceec7?w=800&q=80",
    "sports": "https://images.unsplash.com/photo-1461896836934-bd45ba8fcf9b?w=800&q=80",
    "entertainment": "https://images.unsplash.com/photo-1478720568477-152d9b164e26?w=800&q=80",
    "politics": "https://images.unsplash.com/photo-1541872703-74c5e44368f9?w=800&q=80",
    "india": "https://images.unsplash.com/photo-1524492412937-b28074a5d7da?w=800&q=80",
    "general": "https://images.unsplash.com/photo-1504711434969-e33886168d8c?w=800&q=80",
}


async def seed_demo_articles():
    await init_db()
    async with async_session() as db:
        cats = {c.slug: c for c in (await db.execute(select(Category))).scalars().all()}
        existing_sources = {s.name: s for s in (await db.execute(select(Source))).scalars().all()}

        country_sources = {
            "US": "ABC News", "UK": "BBC World", "India": "NDTV",
            "Germany": "Tagesschau", "France": "Le Monde",
        }

        articles_data = [
            ("US Markets Hit All-Time High on Tech Rally", "business", "US"),
            ("Federal Reserve Holds Interest Rates Steady", "business", "US"),
            ("NASA Announces New Mars Mission for 2028", "science", "US"),
            ("Major Earthquake Hits California Coast", "world", "US"),
            ("US Healthcare Bill Sparks Debate in Congress", "health", "US"),
            ("Hollywood Strikes: Studios Reach Agreement", "entertainment", "US"),
            ("Super Bowl LXI Sets Viewership Record", "sports", "US"),
            ("AI Startup Raises $5B in Record Funding Round", "technology", "US"),
            ("UK Prime Minister Announces New Cabinet", "world", "UK"),
            ("Premier League Season Preview: Top Contenders", "sports", "UK"),
            ("BBC Launches New Digital-First Strategy", "technology", "UK"),
            ("London Stock Exchange Reports Strong Quarter", "business", "UK"),
            ("NHS Winter Preparedness Plan Released", "health", "UK"),
            ("India Launches Chandrayaan-4 Moon Mission", "science", "India"),
            ("Indian Economy Grows 8.2% in Q2", "business", "India"),
            ("IPL 2026: New Teams and Format Announced", "sports", "India"),
            ("Digital India: 5G Coverage Reaches Rural Areas", "technology", "India"),
            ("Germany Approves Major Renewable Energy Package", "world", "Germany"),
            ("Bundesliga Season Kicks Off with Record Attendance", "sports", "Germany"),
            ("Volkswagen Unveils New Electric Vehicle Lineup", "business", "Germany"),
            ("France Hosts Global AI Safety Summit", "technology", "France"),
            ("French Wine Industry Reports Record Exports", "business", "France"),
            ("Tour de France 2026: Route Revealed", "sports", "France"),
        ]

        now = datetime.utcnow()
        added = 0
        for title, cat_slug, country in articles_data:
            existing = await db.execute(select(Article).where(Article.title == title))
            if existing.scalar_one_or_none():
                continue

            cat = cats.get(cat_slug)
            if not cat:
                continue

            src_name = country_sources.get(country)
            src = existing_sources.get(src_name)
            if not src:
                src = Source(name=src_name or f"{country} News", country=country, feed_url="", is_active=True)
                db.add(src)
                await db.flush()
                existing_sources[src.name] = src

            img = CATEGORY_IMAGES.get(cat_slug) or random.choice(DEMO_IMAGES)
            content_html = DEMO_CONTENT.get(cat_slug, f"<p>Full article content about {title.lower()}. This is a demonstration article seeded for initial deployment.</p>")

            a = Article(
                title=title,
                slug=f"demo-{added}-{title.lower().replace(' ', '-')[:60].rstrip('-')}",
                summary=f"{title}. This is a demo article for testing and display purposes.",
                content=content_html,
                image_url=img,
                status=ArticleStatus.PUBLISHED,
                category_id=cat.id,
                source_id=src.id,
                published_at=now - timedelta(hours=added),
            )
            db.add(a)
            added += 1

        await db.commit()
        print(f"Seeded {added} demo articles with images across 5 countries")
