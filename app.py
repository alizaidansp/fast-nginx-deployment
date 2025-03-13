import aws_cdk as cdk
from aws_cdk import Environment
from catalog_server.vpc_stack import CatalogVPC
from catalog_server.sg_stack import SecurityGroupStack
from catalog_server.ec2_stack import EC2Stack

app = cdk.App()


# Instantiate stacks with correct environment
vpc_stack = CatalogVPC(app, "CatalogVPC")

# Pass VPC from vpc_stack to SecurityGroupStack
sg_stack = SecurityGroupStack(app, "SecurityGroupStack", vpc=vpc_stack.vpc)

# Pass both VPC and Security Group to EC2Stack
EC2Stack(app, "EC2Stack", vpc=vpc_stack.vpc, sg=sg_stack.sg)

# Synthesize CloudFormation
app.synth()

# cdk destroy CatalogVPC SecurityGroupStack EC2Stack && cdk deploy CatalogVPC && cdk deploy SecurityGroupStack && cdk deploy EC2Stack
