import boto3

regiones = {"india":"ap-south-1",
"suecia":"eu-north-1",
"francia":"eu-west-3",
"inglaterra":"eu-west-2",
"irlanda":"eu-west-1",
"corea":"ap-northeast-2",
"japon":"ap-northeast-1",
"canada":"ca-central-1",
"brasil":"sa-east-1",
"singapur":"ap-southeast-1",
"australia":"ap-southeast-2",
"alemania":"eu-central-1",
"us":"us-east-1"}

##Varibles
actual = "suecia"
region = regiones[actual]
session = boto3.Session(region_name=region,)
ec2 = session.client("ec2")
cloudformation = session.client("cloudformation")
waiter = cloudformation.get_waiter('stack_create_complete')


##templates
sg_stack_body = ""
sg_stack_path = "sg.yaml"
with open (sg_stack_path, "r") as sg_stack_file:
    sg_stack_body = sg_stack_file.read()


vpcs = ec2.describe_vpcs(Filters=[{'Name': 'isDefault', 'Values': ['true']}])
default_vpc_id = vpcs["Vpcs"][0]["VpcId"]
sgs = ec2.describe_security_groups(Filters=[{'Name': 'vpc-id', 'Values': [default_vpc_id]}])
# print(sgs)
vpn_sg_id = next((sg for sg in sgs['SecurityGroups'] if sg['GroupName'] == "vpn_sg"), None)

# print (sg_stack_body)

if vpn_sg_id is None:

    response = cloudformation.create_stack(
        StackName='sgVpn',
        TemplateBody=sg_stack_body,
        Parameters=[
            {
                'ParameterKey': "VpcId",
                'ParameterValue': default_vpc_id,
                
            },
        ],
        # DisableRollback=False,
        TimeoutInMinutes=123,
        OnFailure='ROLLBACK',
    )

    
    waiter.wait(
        StackName=response['StackId'],
    )
    stack_descripcion = cloudformation.describe_stacks(StackName=response['StackId'])
    print (stack_descripcion["Stacks"][0]['Outputs'][0]['OutputValue'])
else:
    vpn_sg_id = vpn_sg_id['GroupId']
    print(vpn_sg_id)

