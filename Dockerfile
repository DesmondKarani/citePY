FROM python:3.10-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Create directory for CSL styles
RUN mkdir -p /app/styles

# Copy application code
COPY . .

# Download common CSL styles at build time for faster startup
RUN python -c "import os; import requests; \
    styles = ['apa', 'apa-7th-edition', 'modern-language-association', 'modern-language-association-9th-edition', \
              'chicago-author-date', 'chicago-note-bibliography', 'harvard1', 'ieee', 'vancouver', \
              'american-medical-association', 'american-chemical-society', 'nature', 'science']; \
    for style in styles: \
        url = f'https://raw.githubusercontent.com/citation-style-language/styles/master/{style}.csl'; \
        r = requests.get(url); \
        if r.status_code == 200: \
            with open(f'/app/styles/{style}.csl', 'w') as f: \
                f.write(r.text); \
            print(f'Downloaded {style}.csl'); \
        else: \
            print(f'Failed to download {style}.csl')"

# Expose the port
EXPOSE 8000

# Run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
