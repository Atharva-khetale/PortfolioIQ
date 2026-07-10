-- ============================================================
-- PortfolioIQ — MySQL Schema
-- ============================================================
CREATE DATABASE IF NOT EXISTS portfolioiq
    CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE portfolioiq;

-- ------------------------------------------------------------
-- Users (analysts / clients / advisors)
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS users (
    user_id          INT AUTO_INCREMENT PRIMARY KEY,
    full_name        VARCHAR(150) NOT NULL,
    email            VARCHAR(150) UNIQUE NOT NULL,
    role             ENUM('ANALYST','PORTFOLIO_MANAGER','CLIENT','ADMIN') DEFAULT 'CLIENT',
    created_at       TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ------------------------------------------------------------
-- Portfolios
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS portfolios (
    portfolio_id     INT AUTO_INCREMENT PRIMARY KEY,
    user_id          INT NOT NULL,
    portfolio_name   VARCHAR(150) NOT NULL,
    base_currency    VARCHAR(10) DEFAULT 'INR',
    source           ENUM('MANUAL','EXCEL_UPLOAD','API') DEFAULT 'MANUAL',
    created_at       TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

-- ------------------------------------------------------------
-- Securities master (ticker reference data)
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS securities (
    security_id      INT AUTO_INCREMENT PRIMARY KEY,
    ticker           VARCHAR(30) UNIQUE NOT NULL,
    company_name     VARCHAR(200),
    asset_class      ENUM('EQUITY','ETF','MUTUAL_FUND','BOND','CRYPTO','OTHER') DEFAULT 'EQUITY',
    sector           VARCHAR(100),
    industry         VARCHAR(100),
    country          VARCHAR(100),
    exchange         VARCHAR(50),
    currency         VARCHAR(10),
    website          VARCHAR(255),
    last_updated     TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- ------------------------------------------------------------
-- Holdings (positions inside a portfolio)
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS holdings (
    holding_id       INT AUTO_INCREMENT PRIMARY KEY,
    portfolio_id     INT NOT NULL,
    security_id      INT NOT NULL,
    quantity         DECIMAL(18,4) NOT NULL,
    purchase_price   DECIMAL(18,4) NOT NULL,
    purchase_date    DATE,
    created_at       TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (portfolio_id) REFERENCES portfolios(portfolio_id) ON DELETE CASCADE,
    FOREIGN KEY (security_id) REFERENCES securities(security_id)
);

-- ------------------------------------------------------------
-- Daily price history (cache of provider data)
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS price_history (
    price_id         BIGINT AUTO_INCREMENT PRIMARY KEY,
    security_id      INT NOT NULL,
    price_date       DATE NOT NULL,
    open_price       DECIMAL(18,4),
    high_price       DECIMAL(18,4),
    low_price        DECIMAL(18,4),
    close_price      DECIMAL(18,4),
    adj_close        DECIMAL(18,4),
    volume           BIGINT,
    UNIQUE KEY uq_security_date (security_id, price_date),
    FOREIGN KEY (security_id) REFERENCES securities(security_id) ON DELETE CASCADE
);

-- ------------------------------------------------------------
-- Computed risk metrics snapshot (per portfolio, per run)
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS risk_metrics (
    metric_id           BIGINT AUTO_INCREMENT PRIMARY KEY,
    portfolio_id         INT NOT NULL,
    run_date              TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    total_value           DECIMAL(20,4),
    daily_return           DECIMAL(10,6),
    annual_return           DECIMAL(10,6),
    volatility               DECIMAL(10,6),
    sharpe_ratio             DECIMAL(10,6),
    sortino_ratio             DECIMAL(10,6),
    beta                       DECIMAL(10,6),
    max_drawdown               DECIMAL(10,6),
    var_95                      DECIMAL(10,6),
    expected_shortfall_95        DECIMAL(10,6),
    diversification_score          DECIMAL(6,2),
    risk_score                       DECIMAL(6,2),
    FOREIGN KEY (portfolio_id) REFERENCES portfolios(portfolio_id) ON DELETE CASCADE
);

-- ------------------------------------------------------------
-- Sentiment records (news / earnings)
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS sentiment_records (
    sentiment_id      BIGINT AUTO_INCREMENT PRIMARY KEY,
    security_id       INT NOT NULL,
    headline           VARCHAR(500),
    source              VARCHAR(150),
    url                   VARCHAR(500),
    published_at           DATETIME,
    sentiment_label          ENUM('POSITIVE','NEUTRAL','NEGATIVE'),
    sentiment_score            DECIMAL(6,4),
    fetched_at                   TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (security_id) REFERENCES securities(security_id) ON DELETE CASCADE
);

-- ------------------------------------------------------------
-- AI-generated insights / recommendations log
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS ai_insights (
    insight_id        BIGINT AUTO_INCREMENT PRIMARY KEY,
    portfolio_id       INT NOT NULL,
    insight_type         ENUM('CONCENTRATION','DIVERSIFICATION','RISK','SENTIMENT','REBALANCE','GENERAL'),
    insight_text            TEXT,
    severity                  ENUM('INFO','WARNING','CRITICAL') DEFAULT 'INFO',
    created_at                  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (portfolio_id) REFERENCES portfolios(portfolio_id) ON DELETE CASCADE
);

-- ------------------------------------------------------------
-- Generated reports log
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS reports (
    report_id         INT AUTO_INCREMENT PRIMARY KEY,
    portfolio_id        INT NOT NULL,
    file_path              VARCHAR(500),
    generated_at              TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (portfolio_id) REFERENCES portfolios(portfolio_id) ON DELETE CASCADE
);

-- ------------------------------------------------------------
-- Indexes for performance
-- ------------------------------------------------------------
CREATE INDEX idx_price_security_date ON price_history(security_id, price_date);
CREATE INDEX idx_sentiment_security ON sentiment_records(security_id, published_at);
CREATE INDEX idx_holdings_portfolio ON holdings(portfolio_id);
