# Use the official Python lightweight image
FROM python:3.10-slim

# 1. Install system dependencies (CRITICAL for OpenCV/cv2)
# Without 'libgl1', your app will crash when running tools.py
RUN apt-get update && apt-get install -y \
    libgl1 \
    libglib2.0-0 \
    git \
    && rm -rf /var/lib/apt/lists/*

# 2. Set up a user (Hugging Face security requirement)
RUN useradd -m -u 1000 user
USER user
ENV HOME=/home/user \
    PATH=/home/user/.local/bin:$PATH

# 3. Set working directory
WORKDIR $HOME/app

# 4. Copy requirements and install Python libraries
COPY --chown=user requirements.txt requirements.txt
RUN pip install --no-cache-dir --upgrade -r requirements.txt

# 5. Copy your application code
COPY --chown=user . .

# 6. Expose the required port
EXPOSE 7860

# 7. Run Streamlit
# --server.enableXsrfProtection=false is REQUIRED for file uploads to work in Docker Spaces
CMD ["streamlit", "run", "app.py", "--server.port=7860", "--server.address=0.0.0.0", "--server.enableXsrfProtection=false"]