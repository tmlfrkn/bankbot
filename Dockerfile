# ----------------------------------------------------------------------------
# BankBot – FastAPI / Python 3.10 container image
# ----------------------------------------------------------------------------
# 1. Uses the slim Python base image
# 2. Installs system build deps for psycopg2-binary & pgvector client libs
# 3. Installs Python dependencies via requirements.txt (preferred)
# 4. Creates a non-root user for runtime security
# 5. Exposes port 8000 and runs uvicorn
# ----------------------------------------------------------------------------

FROM python:3.10-slim AS base

# ----- system packages -------------------------------------------------------
RUN apt-get update \
    && apt-get install --no-install-recommends -y \
       build-essential \
       libpq-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# ----- dedicated user --------------------------------------------------------
ENV APP_USER=bankbot
RUN useradd -m -d /home/${APP_USER} -s /usr/sbin/nologin ${APP_USER}

# ----- python deps -----------------------------------------------------------
WORKDIR /app

# copy only requirements first to leverage Docker cache
COPY requirements*.txt ./
RUN pip install --no-cache-dir --upgrade pip \
    && if [ -f requirements.txt ]; then pip install --no-cache-dir -r requirements.txt; fi \
    && if [ -f requirements.dev.txt ]; then pip install --no-cache-dir -r requirements.dev.txt; fi

# ----- app code --------------------------------------------------------------
COPY . .

# change ownership
RUN chown -R ${APP_USER}:${APP_USER} /app

USER ${APP_USER}

EXPOSE 8000

# uvicorn with optimum production settings; can be overridden at runtime
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

# --- Yi-1.5-9B-Chat model (optional) ----------------------------------------
# Set MODEL_URL as build-arg to auto-download gguf; otherwise mount via volume
ARG YI_MODEL_URL="https://huggingface.co/mradermacher/Yi-1.5-9B-GGUF/resolve/main/Yi-1.5-9B.Q4_K_S.gguf"
ENV MODEL_DIR=/models/yi-1.5-9b-chat
ENV YI_MODEL_PATH=${MODEL_DIR}/Yi-1.5-9B.Q4_K_S.gguf

RUN if [ ! -z "$YI_MODEL_URL" ]; then \
      mkdir -p ${MODEL_DIR} && \
      echo "Downloading Yi model…" && \
      wget -qO ${YI_MODEL_PATH} "$YI_MODEL_URL" ; \
    fi
