# ──────────────────────────────────────────────────
# Dockerfile — recipe for building your app container
#
# Think of it like a cooking recipe:
# 1. Start with a base ingredient (Python image)
# 2. Add your code
# 3. Install dependencies
# 4. Set the command to run
# ──────────────────────────────────────────────────

# Step 1: Start with Python 3.12 (the base image)
# This is like saying "start with a clean Linux machine that has Python installed"
FROM python:3.12-slim

# Step 2: Set the working directory inside the container
# All following commands run from this folder
# Like: cd /app
WORKDIR /app

# Step 3: Copy requirements.txt first (for caching)
# Docker caches each step. If requirements.txt hasn't changed,
# Docker skips the pip install step (much faster rebuilds)
COPY requirements.txt .

# Step 4: Install Python dependencies
# --no-cache-dir = don't save pip cache (smaller container)
RUN pip install --no-cache-dir -r requirements.txt

# Step 5: Copy your entire project into the container
# . = current directory on your machine
# . = /app inside the container (because of WORKDIR)
COPY . .

# Step 6: Expose port 8000 (documentation — tells others which port your app uses)
EXPOSE 8000

# Step 7: The command to run when the container starts
# Same as: uvicorn main_api_db:app --host 0.0.0.0 --port 8000
# --host 0.0.0.0 means "accept connections from outside the container"
CMD ["uvicorn", "main_api_db:app", "--host", "0.0.0.0", "--port", "8000"]