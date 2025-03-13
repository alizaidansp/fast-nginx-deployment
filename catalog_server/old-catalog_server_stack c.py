from aws_cdk import (
    Stack,
    aws_ec2 as ec2,
    Duration
)
import aws_cdk as cdk
from constructs import Construct

class CatalogServerStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Create a VPC with public and private subnets
        vpc = ec2.Vpc(
            self, "CatalogVPC",
            max_azs=2,  # Use 2 Availability Zones
            nat_gateways=1,  # Create 1 NAT Gateway for private subnet
            subnet_configuration=[
                ec2.SubnetConfiguration(name="PublicSubnet", subnet_type=ec2.SubnetType.PUBLIC),
                ec2.SubnetConfiguration(name="PrivateSubnet", subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS)
            ]
        )

        # Security Group to control EC2 access
        my_ip = "196.61.35.158/32"  # Your IP (replace if necessary)

        ec2_sg = ec2.SecurityGroup(self, "EC2SG", vpc=vpc, allow_all_outbound=True)

        # Allow SSH (port 22) only from your IP
        ec2_sg.add_ingress_rule(ec2.Peer.ipv4(my_ip), ec2.Port.tcp(22), "Allow SSH from my IP")

        # Allow HTTP (port 80) for external access to the API via Nginx
        ec2_sg.add_ingress_rule(ec2.Peer.any_ipv4(), ec2.Port.tcp(80), "Allow HTTP for API Access")

        # Allow Flask API (port 5000) - optional if directly accessing Flask
        ec2_sg.add_ingress_rule(ec2.Peer.any_ipv4(), ec2.Port.tcp(5000), "Allow Flask API on port 5000")

        # EC2 User Data (Initialization script for setting up the server)
        user_data = ec2.UserData.for_linux()

        user_data.add_commands(
            # Update packages and install necessary software
            "sudo apt update && sudo apt upgrade -y",
            "sudo apt install -y nginx python3 python3-pip python3-venv sqlite3",

            # Set up Flask API
            "mkdir -p /home/ubuntu/catalog_server && cd /home/ubuntu/catalog_server",
            "python3 -m venv venv && source venv/bin/activate",
            "pip install flask flask_sqlalchemy",

            # Create SQLite database and populate it with sample data
            "sqlite3 catalog.db 'CREATE TABLE products (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, description TEXT, price REAL NOT NULL);'",
            "sqlite3 catalog.db \"INSERT INTO products (name, description, price) VALUES ('Laptop', 'A high-end laptop', 1200.00), ('Phone', 'Latest smartphone', 800.00);\"",

            # Write Flask app
            "cat <<EOF > /home/ubuntu/catalog_server/app.py",
            "from flask import Flask, jsonify",
            "from flask_sqlalchemy import SQLAlchemy",
            "app = Flask(__name__)",
            "app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////home/ubuntu/catalog_server/catalog.db'",
            "db = SQLAlchemy(app)",
            "class Products(db.Model):",
            "    id = db.Column(db.Integer, primary_key=True)",
            "    name = db.Column(db.String(255), nullable=False)",
            "    description = db.Column(db.Text)",
            "    price = db.Column(db.Float, nullable=False)",
            "@app.route('/products', methods=['GET'])",
            "def get_products():",
            "    products = Products.query.all()",
            "    return jsonify([{'id': p.id, 'name': p.name, 'description': p.description, 'price': p.price} for p in products])",
            "if __name__ == '__main__':",
            "    app.run(host='0.0.0.0', port=5000)",
            "EOF",

            # Create systemd service to run Flask as a background service
            "sudo bash -c 'cat > /etc/systemd/system/catalog.service' <<EOF",
            "[Unit]",
            "Description=Catalog API Server",
            "After=network.target",
            "",
            "[Service]",
            "User=ubuntu",
            "WorkingDirectory=/home/ubuntu/catalog_server",
            "ExecStart=/home/ubuntu/catalog_server/venv/bin/python /home/ubuntu/catalog_server/app.py",
            "Restart=always",
            "",
            "[Install]",
            "WantedBy=multi-user.target",
            "EOF",

            # Reload systemd to recognize the new service, start and enable Flask service
            "sudo systemctl daemon-reload",
            "sudo systemctl start catalog",
            "sudo systemctl enable catalog",

            # Set up Nginx reverse proxy to forward requests from port 80 to Flask (port 5000)
            "sudo rm /etc/nginx/sites-enabled/default",
            "sudo bash -c 'cat > /etc/nginx/sites-available/catalog' <<EOF",
            "server {",
            "    listen 80;",
            "    server_name _;",
            "    location / {",
            "        proxy_pass http://127.0.0.1:5000;",
            "        proxy_set_header Host \\$host;",
            "        proxy_set_header X-Real-IP \\$remote_addr;",
            "        proxy_set_header X-Forwarded-For \\$proxy_add_x_forwarded_for;",
            "    }",
            "}",
            "EOF",

            # Enable and restart Nginx
            "sudo ln -s /etc/nginx/sites-available/catalog /etc/nginx/sites-enabled/",
            "sudo nginx -t",
            "sudo systemctl restart nginx"
        )

        # EC2 Instance configuration
        ec2_instance = ec2.Instance(
            self, "CatalogEC2",
            instance_type=ec2.InstanceType.of(ec2.InstanceClass.BURSTABLE2, ec2.InstanceSize.MICRO),
            machine_image=ec2.MachineImage.generic_linux({
                "eu-west-1": "ami-03fd334507439f4d1"  # Ubuntu 22.04 LTS for eu-west-1
            }),
            vpc=vpc,
            vpc_subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PUBLIC),
            security_group=ec2_sg,
            user_data=user_data,
            key_name="LabKP"  # Ensure this key pair exists in your AWS account
        )

        # Output the public IP address of the EC2 instance
        self.ec2_ip = ec2_instance.instance_public_ip
        cdk.CfnOutput(self, "server_ip", value=self.ec2_ip)

