FROM python:3.11-slim

# Create a non-root user (required by Hugging Face Spaces)
RUN useradd -m -u 1000 user

WORKDIR /app

# Copy requirements and install
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Switch to non-root user
USER user

# Set environment variables
ENV PATH="/home/user/.local/bin:$PATH"

# Copy the entire backend directory into /app/backend
COPY --chown=user backend/ /app/backend/

# Set working directory to the backend folder so imports work natively
WORKDIR /app/backend

# Expose the default port for Hugging Face Spaces
EXPOSE 7860

# Run the FastAPI app
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "7860"]
