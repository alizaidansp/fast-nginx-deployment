#!/bin/bash
# Update system and install dependencies
sudo apt update && sudo apt upgrade -y
sudo apt install -y nginx python3 python3-pip python3-venv sqlite3

# Set up application directory
mkdir -p /home/ubuntu/catalog_server

# Dynamically write app.py
# EOF => End Of File(specifying beginning and end of file)
# << => Here doc operator specifying 
cat << 'EOF' > /home/ubuntu/catalog_server/app.py
from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////home/ubuntu/catalog_server/catalog.db'


db = SQLAlchemy(app)

class Products(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    description = db.Column(db.String(200))
    price = db.Column(db.Float, nullable=False)

@app.route('/products', methods=['GET'])
def get_products():
    products = Products.query.all()
    return jsonify([{
        'id': p.id,
        'name': p.name,
        'description': p.description,
        'price': p.price
    } for p in products])

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
EOF

# Set up Python virtual environment and Flask app
cd /home/ubuntu/catalog_server
python3 -m venv venv
source venv/bin/activate
pip install flask flask_sqlalchemy

# Initialize the SQLite database
sqlite3 catalog.db <<EOF
CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    description TEXT,
    price REAL NOT NULL
);
INSERT INTO products (name, description, price) VALUES
('Laptop', 'A high-end laptop', 1200.00),
('Phone', 'Latest smartphone', 800.00);
EOF

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
sudo rm /etc/nginx/sites-enabled/default
cat <<EOT | sudo tee /etc/nginx/sites-available/catalog
server {
    listen 80;
    server_name _;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
    }
}
EOT

sudo ln -s /etc/nginx/sites-available/catalog /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
