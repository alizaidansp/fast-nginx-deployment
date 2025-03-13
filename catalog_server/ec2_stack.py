from aws_cdk import Stack, aws_ec2 as ec2, CfnOutput
from constructs import Construct
from aws_cdk import Stack
import os

# In ec2_stack.py __init__ method
# current_dir = os.path.dirname(os.path.abspath(__file__))
# user_data_path = os.path.join(current_dir, "user_data.sh")
class EC2Stack(Stack):
    def __init__(self, scope: Construct, id: str, vpc: ec2.Vpc, sg: ec2.SecurityGroup,**kwargs) -> None:
       
        super().__init__(scope, id, **kwargs)



        with open("user_data.sh", "r") as f:
            user_data_script = f.read()

        user_data = ec2.UserData.for_linux()
        user_data.add_commands(user_data_script)

        instance = ec2.Instance(
            self, "CatalogEC2",
            instance_type=ec2.InstanceType.of(ec2.InstanceClass.BURSTABLE2, ec2.InstanceSize.MICRO),
            machine_image=ec2.MachineImage.generic_linux({
                "eu-west-1": "ami-03fd334507439f4d1"  # Ubuntu 22.04 LTS
            }),
            vpc=vpc,
            security_group=sg,
            key_name="LabKP",
            user_data=user_data
        )

        CfnOutput(self, "EC2PublicIP", value=instance.instance_public_ip)
