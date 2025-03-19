import requests
from aws_cdk import aws_ec2 as ec2
from constructs import Construct
from aws_cdk import Stack

class SecurityGroupStack(Stack):
    def __init__(self, scope: Construct, id: str, vpc: ec2.Vpc, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        self.sg = ec2.SecurityGroup(
            self, "EC2SG", vpc=vpc, allow_all_outbound=True
        )

        # Get your current public IP dynamically
        try:
            my_ip = requests.get("https://ifconfig.me").text.strip() + "/32"
        except Exception:
            my_ip = "0.0.0.0/0"  # Fallback if request fails

        # Allow SSH from your current IP
        self.sg.add_ingress_rule(ec2.Peer.ipv4(my_ip), ec2.Port.tcp(22), "Allow SSH from my IP")

        # Allow Svelte app traffic (uncomment if needed)
        # self.sg.add_ingress_rule(ec2.Peer.any_ipv4(), ec2.Port.tcp(3000), "Allow SvelteKit")

        # Allow HTTP (port 80) from anywhere
        self.sg.add_ingress_rule(ec2.Peer.any_ipv4(), ec2.Port.tcp(80), "Allow HTTP")

        # Allow Flask API (uncomment if needed)
        # self.sg.add_ingress_rule(ec2.Peer.any_ipv4(), ec2.Port.tcp(5000), "Allow Flask API")
