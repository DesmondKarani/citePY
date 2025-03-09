#!/bin/bash

# Make script executable with: chmod +x setup.sh
# Run with: ./setup.sh

echo "Setting up Citation Generator project..."

# Install dependencies
echo "Installing Python dependencies..."
pip install -r requirements.txt

# Create necessary directories if they don't exist
echo "Creating directory structure..."
mkdir -p app/styles

# Download CSL styles
echo "Downloading CSL style files..."
python3 scripts/download_styles.py

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "Creating .env file..."
    cat > .env << EOL
# Citation Generator Environment Variables
PORT=8000
HOST=0.0.0.0
DEBUG=True
LOG_LEVEL=INFO
# Add your API keys below
ISBNDB_API_KEY=
EOL
    echo ".env file created. Please add your API keys."
fi

echo "Setup complete! You can now run the application with:"
echo "uvicorn app.main:app --reload"
