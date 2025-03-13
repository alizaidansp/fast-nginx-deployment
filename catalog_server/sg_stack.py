from aws_cdk import aws_ec2 as ec2
from constructs import Construct
from aws_cdk import Stack

class SecurityGroupStack(Stack):
  
    def __init__(self, scope: Construct, id: str,vpc: ec2.Vpc,**kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        self.sg = ec2.SecurityGroup(
            self, "EC2SG", vpc=vpc, allow_all_outbound=True
        )

        my_ip = "196.61.35.158/32"  # Replace with your IP

        self.sg.add_ingress_rule(ec2.Peer.ipv4(my_ip), ec2.Port.tcp(22), "Allow SSH")
        self.sg.add_ingress_rule(ec2.Peer.any_ipv4(), ec2.Port.tcp(80), "Allow HTTP")
        # self.sg.add_ingress_rule(ec2.Peer.any_ipv4(), ec2.Port.tcp(5000), "Allow Flask API")
