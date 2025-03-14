#!/bin/bash
set -e  # Exit on error

# Update system and install dependencies
sudo apt update && sudo apt upgrade -y
sudo apt install -y nginx python3 python3-pip python3-venv sqlite3 git
# Install unzip used to install aws cli
sudo apt install -y unzip

# Download and install AWS CLI (version 2)
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install

# Verify the installation
aws --version

# Fetch GitHub credentials from AWS Secrets Manager
creds=$(aws ssm get-parameter --name "/github/creds" --with-decryption --region eu-west-1 --query "Parameter.Value" --output text)

GITHUB_USERNAME=$(echo $creds | jq -r .GITHUB_USERNAME)
GITHUB_TOKEN=$(echo $creds | jq -r .GITHUB_TOKEN)

REPO_URL="https://${GITHUB_USERNAME}:${GITHUB_TOKEN}@github.com/alizaidansp/flask-app.git"
# Clone the private repo and rename it
mkdir -p /home/ubuntu
cd /home/ubuntu
git clone $REPO_URL
mv flask-app catalog_server

# Set permissions
# chown -R ubuntu:ubuntu /home/ubuntu/catalog_server

# Set up the Flask app
cd catalog_server

# Set up Python virtual environment
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

# Set up Nginx reverse proxy
sudo rm -f /etc/nginx/sites-enabled/default
cat <<EOT | sudo tee /etc/nginx/sites-available/catalog
server {
    listen 80;
    server_name _;

    location /api/v1/ {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
    }
}
EOTn

sudo ln -s /etc/nginx/sites-available/catalog /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
