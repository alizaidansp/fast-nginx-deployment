from aws_cdk import Stack
from aws_cdk import aws_ec2 as ec2
from constructs import Construct

class CatalogVPC(Stack):
    def __init__(self, scope: Construct, id: str,**kwargs) -> None:
        super().__init__(scope, id, **kwargs)


        self.vpc = ec2.Vpc(
            self, "CatalogVPC",
            max_azs=2,
            # nat_gateways=1,
            subnet_configuration=[
                ec2.SubnetConfiguration(name="PublicSubnet", subnet_type=ec2.SubnetType.PUBLIC),
                # ec2.SubnetConfiguration(name="PrivateSubnet", subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS)
            ]
        )
