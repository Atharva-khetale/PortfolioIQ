# PortfolioIQ — Deployment Guide

## 1. Local Development Setup

### Prerequisites
- Python 3.10+
- MySQL 8.0+
- Git

### Steps
```bash
git clone <repo_url> PortfolioIQ
cd PortfolioIQ

python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate

pip install -r requirements.txt

cp .env.example .env
# edit .env: DB credentials + API keys (Alpha Vantage, FMP, NewsAPI)

mysql -u root -p < database/schema.sql

streamlit run app/streamlit_app.py
```
App will be available at `http://localhost:8501`.

> First run of the sentiment engine downloads the FinBERT model (~400MB) from
> Hugging Face. If offline or on constrained hardware, the engine automatically
> falls back to VADER (lightweight, no download).

---

## 2. Docker Deployment

**Dockerfile**
```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8501
HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health || exit 1

ENTRYPOINT ["streamlit", "run", "app/streamlit_app.py", \
            "--server.port=8501", "--server.address=0.0.0.0"]
```

**docker-compose.yml**
```yaml
version: "3.9"
services:
  mysql:
    image: mysql:8.0
    restart: always
    environment:
      MYSQL_ROOT_PASSWORD: ${DB_PASSWORD}
      MYSQL_DATABASE: portfolioiq
    ports: ["3306:3306"]
    volumes:
      - db_data:/var/lib/mysql
      - ./database/schema.sql:/docker-entrypoint-initdb.d/schema.sql

  portfolioiq:
    build: .
    restart: always
    ports: ["8501:8501"]
    env_file: .env
    depends_on: [mysql]

volumes:
  db_data:
```

```bash
docker compose up --build -d
```

---

## 3. Cloud Deployment Options

| Platform | Notes |
|---|---|
| **Streamlit Community Cloud** | Fastest path to a public demo; connect GitHub repo, add secrets in dashboard for API keys. Use an external managed MySQL (PlanetScale, AWS RDS) since the platform is stateless. |
| **AWS (EC2 + RDS)** | EC2 instance running Docker Compose; RDS MySQL for persistence; ALB + ACM for HTTPS. Recommended for production. |
| **Azure App Service + Azure Database for MySQL** | Container deployment via App Service; good for enterprise/Azure-native shops. |
| **GCP Cloud Run + Cloud SQL** | Cloud Run for the Streamlit container (note: Cloud Run is stateless/scale-to-zero, fine for read-heavy dashboards); Cloud SQL for MySQL. |

### Production checklist
- [ ] Move API keys/DB credentials to a secrets manager (AWS Secrets Manager / Azure Key Vault / GCP Secret Manager)
- [ ] Put a reverse proxy (Nginx) or managed load balancer in front of Streamlit with HTTPS
- [ ] Enable MySQL automated backups + point-in-time recovery
- [ ] Add rate limiting on the news/company crawler endpoints to avoid provider throttling
- [ ] Cache price history (already modeled via `price_history` table) to reduce API calls
- [ ] Add application logging (structured logs) and a health-check endpoint
- [ ] Pin dependency versions (already done in `requirements.txt`) and run `pip-audit` in CI
- [ ] Add CI pipeline: `pytest tests/` on every PR

---

## 4. Environment Variables Reference

| Variable | Description |
|---|---|
| `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD` | MySQL connection |
| `ALPHA_VANTAGE_API_KEY` | Fallback market data provider |
| `FMP_API_KEY` | Fallback fundamentals provider |
| `NEWS_API_KEY` | Broader news coverage (optional) |
| `RISK_FREE_RATE` | Annualized risk-free rate used in Sharpe/Sortino |
| `BENCHMARK_TICKER` | Index used for Beta calculation (e.g. `^NSEI`, `^GSPC`) |
| `DEFAULT_CURRENCY` | Display currency |

---

## 5. Scaling Notes
- The analytics engine (`app/analytics/`) is stateless and pure-function based — safe to run in multiple worker processes.
- Price data should be cached in `price_history` to avoid repeated calls to Yahoo/Alpha Vantage on every dashboard refresh; a scheduled job (cron / Airflow) can pre-populate this table nightly.
- FinBERT inference is the heaviest component — consider a dedicated inference service (e.g. a small GPU/CPU-optimized microservice behind an internal API) if sentiment volume grows, rather than loading the model in every Streamlit worker.
