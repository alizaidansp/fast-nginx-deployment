import aws_cdk as core
import aws_cdk.assertions as assertions

from 3_catalog_server.3_catalog_server_stack import 3CatalogServerStack

# example tests. To run these tests, uncomment this file along with the example
# resource in 3_catalog_server/3_catalog_server_stack.py
def test_sqs_queue_created():
    app = core.App()
    stack = 3CatalogServerStack(app, "3-catalog-server")
    template = assertions.Template.from_stack(stack)

#     template.has_resource_properties("AWS::SQS::Queue", {
#         "VisibilityTimeout": 300
#     })
