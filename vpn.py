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
keypub = "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQCxMEo7XjvUVFug45TGA4k3rM5iiil1R35B+gQmNBAoy9ithQITlOtuE93HQNLnqGKnOl83kLKHRaymTNwM6gNusyUIuNuj6hXYtCdygFphBsoPZ3+W2dtRZ3hjpl59MfAbHHkd+2u5RMJXjt9jrhFer/FhyZ6x6S5B4+yIVI4JLCrJ3pnRvifbrisOAWhd4von55ewlBQKelNc6DNNjbL/tSTSQluf48tzcrwz21RItQRxwTASrehL6zrAZRncrSjPF61Shef6ce8ohNIQHmD1zSBWxWIPF2krlRW36nCJrTgxCuNHVzY60bn8diy+ZdeTONzrEK33CmsTW0Pv8Q35"

##crear key par
keypairs = ec2.describe_key_pairs()
keypar = next((key for key in keypairs['KeyPairs'] if key['KeyName']=='vpn'),None)
# print(keypar)
if keypar is None:
    response = ec2.import_key_pair(KeyName='vpn', PublicKeyMaterial=keypub)

###templates
#template sg
sg_stack_body = ""
sg_stack_path = "sg.yaml"
with open (sg_stack_path, "r") as sg_stack_file:
    sg_stack_body = sg_stack_file.read()
#template ec2
vpn_stack_body = ""
vpn_stack_path = "vpnstack.yaml"
with open (vpn_stack_path, "r") as vpn_stack_file:
    vpn_stack_body = vpn_stack_file.read()

##buscar tipo de instancia
ins_type = ""
typei = []
try:
    ins_type = ec2.describe_instance_types(
        InstanceTypes=['t3.micro'],
        Filters=[
        {
            'Name': 'free-tier-eligible',
            'Values': ['true']
            }
        ]
        )
    # print(ins_type['InstanceTypes'])
    if ins_type['InstanceTypes'] != []:
        typei.append(ins_type['InstanceTypes'])
except Exception as e:
    print (e)
    
try:
    ins_type = ec2.describe_instance_types(
        InstanceTypes=['t2.micro'],
        Filters=[
        {
            'Name': 'free-tier-eligible',
            'Values': ['true']
            }
        ]
        )
    # print(ins_type['InstanceTypes'])
    if ins_type['InstanceTypes'] != []:
        typei.append(ins_type['InstanceTypes'])
except Exception as e:
    print (e)
    
if typei[0] != []:
    typei = typei[0][0]['InstanceType']
else:
    print ("ni t2 ni t3 micro son freetier para esta cuenta")

##buscar sg id
vpcs = ec2.describe_vpcs(Filters=[{'Name': 'isDefault', 'Values': ['true']}])
default_vpc_id = vpcs["Vpcs"][0]["VpcId"]
sgs = ec2.describe_security_groups(Filters=[{'Name': 'vpc-id', 'Values': [default_vpc_id]}])
vpn_sg_id = next((sg for sg in sgs['SecurityGroups'] if sg['GroupName'] == "vpn_sg"), None)

##crear si no existe
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
    stack_descripcion = cloudformation.describe_stacks(StackName="sgVpn")
    print (stack_descripcion["Stacks"][0]['Outputs'][0]['OutputValue'])
else:
    vpn_sg_id = vpn_sg_id['GroupId']


##crear ec2 stack
amis = ec2.describe_images(
     Filters=[
        {
            'Name': 'owner-alias',
            'Values': ['amazon']
        },
        {
            'Name': 'name',
            'Values': ['amzn2-ami-hvm-*-x86_64-gp2']
        },
        {
            'Name': 'state',
            'Values': ['available']
        }
    ],
    # Ordenar por fecha de creación de manera descendente y obtener la más reciente
    Owners=['amazon']
)

###########lanzar stack de ec2

#buscar ami id (/) prefiero buscarlo a mano y ponerlo en el dict
# amis['Images'].sort(key=lambda x: x['CreationDate'], reverse=True)
# ultima_ami = amis['Images'][0] if amis['Images'] else None
# print (ultima_ami['ImageId'])

#buscar si stack esta creado
stack_descripcion = cloudformation.describe_stacks()
stack_vpn = next((st for st in stack_descripcion['Stacks'] if st['StackName'] == "ec2vpn"), None)
# print(stack_vpn)

#condicional si no esta creado 
if stack_vpn == None:
    print ("creando ec2vpn")
    response = cloudformation.create_stack(
        StackName='ec2vpn',
        TemplateBody=vpn_stack_body,
        Parameters=[
            {
                'ParameterKey': "SgId",
                'ParameterValue': vpn_sg_id,
                
            },
        ],
        TimeoutInMinutes=123,
        OnFailure='ROLLBACK',
    )
else:
    #eliminado stack
    eliminar = cloudformation.delete_stack(
        StackName='ec2vpn',
    )
    waiter_delete = cloudformation.get_waiter('stack_create_complete')
    waiter_delete.wait(
        StackName='ec2vpn',
    )
    #creando stack
    response = cloudformation.create_stack(
        StackName='ec2vpn',
        TemplateBody=vpn_stack_body,
        Parameters=[
            {
                'ParameterKey': "SgId",
                'ParameterValue': vpn_sg_id,
                
            },
        ],
        TimeoutInMinutes=123,
        OnFailure='ROLLBACK',
    )
        
        
        
#scp -i vpn.pem ec2-user@52.195.152.243:/home/wireguard/config/peer1/peer1.conf .


