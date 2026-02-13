ARG OPENHANDS_VERSION=latest
ARG BASE="ghcr.io/openhands/openhands"
FROM ${BASE}:${OPENHANDS_VERSION}

# Datadog labels
LABEL com.datadoghq.tags.service="deploy"
LABEL com.datadoghq.tags.env="${DD_ENV}"

# Install Node.js v20+ and npm (which includes npx)
# Apply security updates to fix CVEs
RUN apt-get update && \
    apt-get install -y curl && \
    curl -fsSL https://deb.nodesource.com/setup_20.x | bash - && \
    apt-get install -y nodejs && \
    apt-get install -y jq gettext && \
    # Apply security updates for packages with available fixes
    apt-get upgrade -y \
        libc-bin \
        libc6 \
        libgnutls30 \
        libsqlite3-0 \
        perl-base && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Install Python packages with security fixes
RUN pip install "alembic==1.16.5" "psycopg2-binary==2.9.10" "cloud-sql-python-connector==1.18.4" "pg8000==1.31.5" "gspread==6.2.1" "stripe==11.6.0" "python-keycloak==5.8.1" "asyncpg==0.30.0" "sqlalchemy[asyncio]==2.0.43" "resend==2.13.1" "tenacity==9.1.2" "slack-sdk==3.36.0" "ddtrace==3.13.0" "posthog==6.7.6" "limits==5.5.0" "coredis==4.24.0" "prometheus-client==0.22.1" "shap==0.48.0" "scikit-learn==1.7.1" "pandas==2.3.2" "numpy==2.2.6" && \
    # Update packages with known CVE fixes
    pip install --upgrade \
        "mcp>=1.10.0" \
        "pillow>=11.3.0"

WORKDIR /app
COPY enterprise .

RUN chown -R openhands:openhands /app && chmod -R 770 /app
USER openhands

# Command will be overridden by Kubernetes deployment template
CMD ["uvicorn", "saas_server:app", "--host", "0.0.0.0", "--port", "3000"]
