# Use the official Python image with a slim variant for a smaller size
FROM python:3.13-slim

# Create and set a non-root user for better security
RUN useradd -m -s /bin/bash python

# Set the working directory
WORKDIR /app

# Copy only the requirements file first to leverage Docker layer caching
COPY requirements.txt .

# Set environment variables to force CPU-only execution
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    HF_HOME="/home/python/.cache/huggingface" \
    CUDA_VISIBLE_DEVICES="" \
    FORCE_CUDA="0" \
    USE_CUDA="0" \
    TORCH_CUDA_ARCH_LIST=""

# Install system dependencies
RUN apt-get update && apt-get -y upgrade && \
    apt-get install -y --no-install-recommends gcc && \
    pip install --no-cache-dir --upgrade pip

# Install PyTorch CPU-only version FIRST to prevent LangChain from pulling GPU dependencies
RUN pip install --no-cache-dir torch --extra-index-url https://download.pytorch.org/whl/cpu

# Now install all other dependencies
RUN pip install --no-cache-dir -r requirements.txt --prefer-binary

# Clean up unnecessary dependencies
RUN apt-get purge -y --auto-remove gcc && \
    rm -rf /var/lib/apt/lists/*

# Create and set proper permissions for Hugging Face cache directory
RUN mkdir -p /home/python/.cache/huggingface && \
    chown -R python:python /home/python/.cache/huggingface

# Copy the rest of the application files and configuration.json file
COPY . .
# COPY configuration.json /app/configuration.json

# Switch to the non-root user
USER python

# Run the application
CMD ["python", "src/app.py"]