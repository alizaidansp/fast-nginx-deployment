#!/bin/bash
set -e  # Exit on error

# Update system and install dependencies
sudo apt update && sudo apt upgrade -y
sudo apt install -y nginx python3 python3-pip python3-venv sqlite3 git unzip curl jq

# Check if AWS CLI is installed
if ! command -v aws &> /dev/null; then
    echo "AWS CLI not found. Installing..."

    # Download and install AWS CLI (version 2)
    curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
    unzip awscliv2.zip
    sudo ./aws/install

    # Clean up
    rm -rf awscliv2.zip aws

    # Verify installation
    aws --version
else
    echo "AWS CLI is already installed: $(aws --version)"
fi


# Fetch GitHub credentials from AWS SSM Parameter Store
creds=$(aws ssm get-parameter --name "/github/creds" --with-decryption --region eu-west-1 --query "Parameter.Value" --output text)

GITHUB_USERNAME=$(echo $creds | jq -r .GITHUB_USERNAME)
GITHUB_TOKEN=$(echo $creds | jq -r .GITHUB_TOKEN)

# Clone Flask backend repo
REPO_URL="https://${GITHUB_USERNAME}:${GITHUB_TOKEN}@github.com/alizaidansp/flask-app.git"
mkdir -p /home/ubuntu
cd /home/ubuntu
git clone $REPO_URL
mv flask-app catalog_server

# Set up Flask app
cd catalog_server
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt || pip install flask flask_sqlalchemy

# Execute the database creation script
bash exec_db.sh

# Set up Flask systemd service
cat <<EOT | sudo tee /etc/systemd/system/catalog.service
[Unit]
Description=Catalog API Server
After=network.target

[Service]
User=root
WorkingDirectory=/home/ubuntu/catalog_server
ExecStart=/home/ubuntu/catalog_server/venv/bin/python app.py
Restart=always

[Install]
WantedBy=multi-user.target
EOT

sudo systemctl daemon-reload
sudo systemctl enable catalog
sudo systemctl start catalog

# Install Node.js and npm (for Svelte frontend)
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt install -y nodejs


#get out of the backend server
cd ..


# Clone Svelte frontend repo
FRONTEND_REPO_URL="https://${GITHUB_USERNAME}:${GITHUB_TOKEN}@github.com/alizaidansp/nginx-app-frontend.git"
git clone $FRONTEND_REPO_URL
mv nginx-app-frontend catalog_frontend

# Build the Svelte frontend
cd /home/ubuntu/catalog_frontend
npm install
npm run build

# Set up Flask systemd service
cat <<EOT | sudo tee /etc/systemd/system/sveltekit.service
[Unit]
Description=SvelteKit Application
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/catalog_frontend
ExecStart=/usr/bin/node /home/ubuntu/catalog_frontend/build/index.js
Restart=always
Environment=PORT=3000
Environment=NODE_ENV=production

[Install]
WantedBy=multi-user.target
EOT

sudo systemctl daemon-reload
sudo systemctl enable sveltekit
sudo systemctl start sveltekit

# Set permissions for Nginx
sudo chown -R www-data:www-data /home/ubuntu/catalog_frontend/build

# Update Nginx configuration for Flask and Svelte
sudo rm -f /etc/nginx/sites-enabled/default
cat <<EOT | sudo tee /etc/nginx/sites-available/catalog
server {
    listen 80;
    server_name _;

    # Flask API
    location /api/v1/ {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;

        deny 196.61.35.152/32;
        # deny the above user IP


        allow all;   
        # allow others 
    }

      # SvelteKit SSR handler
    location / {
        proxy_pass http://127.0.0.1:3000;  # Ensure your SvelteKit app >
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
    }

}
EOT

# Apply the Nginx configuration
sudo ln -s /etc/nginx/sites-available/catalog /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
