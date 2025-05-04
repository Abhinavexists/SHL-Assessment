FROM python:3.10-slim

WORKDIR /app

# Copy requirements first for better cache utilization
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Make the scripts executable
RUN chmod +x /app/setup.sh

# Expose ports for FastAPI and Streamlit
EXPOSE 8000 8501

# Command to run both services
ENTRYPOINT ["/app/entrypoint.sh"] 