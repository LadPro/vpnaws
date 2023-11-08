import boto3
import json

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
waiter = session.get_waiter('stack_create_complete')

##templates
sg_stack_body = ""
sg_stack_path = "sg.yaml"
with open (sg_stack_path, "r") as sg_stack_file:
    sg_stack_body = sg_stack_file.read()


vpcs = ec2.describe_vpcs(Filters=[{'Name': 'isDefault', 'Values': ['true']}])
default_vpc_id = vpcs["Vpcs"][0]["VpcId"]
sgs = ec2.describe_security_groups(Filters=[{'Name': 'vpc-id', 'Values': [default_vpc_id]}])
print(sgs)
vpn_sg_id = next((sg for sg in sgs['SecurityGroups'] if sg['GroupName'] == "vpn_sg"), None)

# print (sg_stack_body)

if vpn_sg_id is None:
    # print(f"El Security Group '{sg_name}' no existe, creándolo...")
    # Crear el Security Group

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
    # print(f"Security Group creado con ID: {sg['GroupId']}")

    print (response['StackId'])
    
    waiter.wait(
        StackName=response['StackId'],
    )

else:
    vpn_sg_id = vpn_sg_id['GroupId']
    print(vpn_sg_id)

{'SecurityGroups': 
    [{'Description': 'security group que permite entrada ', 'GroupName': 'vpn_sg', 'IpPermissions': [{'FromPort': 22, 'IpProtocol': 'tcp', 'IpRanges': [{'CidrIp': '0.0.0.0/0'}], 'Ipv6Ranges': [], 'PrefixListIds': [], 'ToPort': 22, 'UserIdGroupPairs': []}, {'FromPort': 51820, 'IpProtocol': 'udp', 'IpRanges': [{'CidrIp': '0.0.0.0/0'}], 'Ipv6Ranges': [], 'PrefixListIds': [], 'ToPort': 51820, 'UserIdGroupPairs': []}], 'OwnerId': '196167126881', 'GroupId': 'sg-0d5f6a2a312fe3196', 'IpPermissionsEgress': [{'IpProtocol': '-1', 'IpRanges': [{'CidrIp': '0.0.0.0/0'}], 'Ipv6Ranges': [], 'PrefixListIds': [], 'UserIdGroupPairs': []}], 'Tags': [{'Key': 'aws:cloudformation:stack-id', 'Value': 'arn:aws:cloudformation:eu-north-1:196167126881:stack/sgVpn/d5c09bb0-7e4f-11ee-b649-06038d891f18'}, {'Key': 'aws:cloudformation:stack-name', 'Value': 'sgVpn'}, {'Key': 'aws:cloudformation:logical-id', 'Value': 'SgVpn'}], 'VpcId': 'vpc-0d6fb1857965b03ed'},
     {'Description': 'default VPC security group', 'GroupName': 'default', 'IpPermissions': [{'IpProtocol': '-1', 'IpRanges': [], 'Ipv6Ranges': [], 'PrefixListIds': [], 'UserIdGroupPairs': [{'GroupId': 'sg-0fae445bdb8a70e03', 'UserId': '196167126881'}]}], 'OwnerId': '196167126881', 'GroupId': 'sg-0fae445bdb8a70e03', 'IpPermissionsEgress': [{'IpProtocol': '-1', 'IpRanges': [{'CidrIp': '0.0.0.0/0'}], 'Ipv6Ranges': [], 'PrefixListIds': [], 'UserIdGroupPairs': []}], 'VpcId': 'vpc-0d6fb1857965b03ed'}], 
    'ResponseMetadata': {'RequestId': '41e660e2-8230-40ef-8252-66e0e1296db3', 'HTTPStatusCode': 200, 'HTTPHeaders': {'x-amzn-requestid': '41e660e2-8230-40ef-8252-66e0e1296db3', 'cache-control': 'no-cache, no-store', 'strict-transport-security': 'max-age=31536000; includeSubDomains', 'vary': 'accept-encoding', 'content-type': 'text/xml;charset=UTF-8', 'content-length': '3825', 'date': 'Wed, 08 Nov 2023 16:17:58 GMT', 'server': 'AmazonEC2'}, 'RetryAttempts': 0}}