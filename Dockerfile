FROM python:3.13-slim-bookworm

# Step 2: Environment settings for production stability
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Step 3: Install system-level dependencies for the headless browser
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    gnupg \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Step 4: Optimized layer caching for dependencies
COPY requirements.txt /app/
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Step 5: Install Playwright & Crawl4AI binaries
# This handles the browser requirements for your 130-second crawls
RUN playwright install --with-deps chromium && \
    crawl4ai-setup

# Step 6: Copy your LangGraph project files
COPY . /app/

# Step 7: Default command (overridden by GitHub Actions)
CMD ["python", "manage.py", "run_newsletter_agent"]