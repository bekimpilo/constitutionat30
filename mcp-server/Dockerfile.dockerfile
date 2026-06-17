FROM python:3.12

WORKDIR /app

# Install dependencies
COPY mcp-server/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy code
COPY . /app

# Set working directory to where server.py lives
WORKDIR /app/mcp-server

# Expose port
EXPOSE 8000

# Run with uvicorn
CMD ["python", "-m", "uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8000"]