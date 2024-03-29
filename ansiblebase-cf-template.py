"""Generating CloudFormation template."""
from ipaddress import ip_network
from ipify import get_ip
from troposphere import (
  Base64,
  ec2,
  GetAtt,
  Join,
  Output,
  Parameter,
  Ref,
  Template,
)

ApplicationName = "helloworld"
ApplicationPort = "3000"

GithubAccount = "ash8454"
GithubAnsibleURL = "https://github.com/{}/ansible".format(GithubAccount)
AnsiblePullCmd = \
"/usr/bin/ansible-pull -U {} {}.yml -i localhost".format(GithubAnsibleURL,
ApplicationName)

PublicCidrIp = str(ip_network(get_ip()))

t = Template()

t.add_description("Effective DevOps in AWS: HelloWorld web application")

t.add_parameter(Parameter(
 "KeyPair",
 Description="Name of an existing EC2 KeyPair to SSH",
 Type="AWS::EC2::KeyPair::KeyName",
 ConstraintDescription="must be the name of an existing EC2 KeyPair.",
))

t.add_resource(ec2.SecurityGroup(
 "SecurityGroup",
 GroupDescription="Allow SSH and TCP/{} access".format(ApplicationPort),
 SecurityGroupIngress=[
    ec2.SecurityGroupRule(
      IpProtocol="tcp",
      FromPort="22",
      ToPort="22",
      CidrIp=PublicCidrIp,
    ),
    ec2.SecurityGroupRule(
      IpProtocol="tcp",
      FromPort=ApplicationPort,
      ToPort=ApplicationPort,
      CidrIp="0.0.0.0/0",
    ),
  ],
))

# ud=Base64(Join('\n', [
#   "#!/bin/bash",
#   "sudo yum install --enablerepo=epel -y nodejs",
#   "wget http://bit.ly/2vESNuc -O /home/ec2-user/helloworld.js",
#   "wget http://bit.ly/2vVvT18 -O /etc/init/helloworld.conf",
#   "start helloworld"
# ]))

ud = Base64(Join('\n', [ "#!/bin/bash",
"yum install --enablerepo=epel -y git", "pip install ansible",
AnsiblePullCmd,
"echo '*/10 * * * * {}' > /etc/cron.d/ansible- pull".format(AnsiblePullCmd)
]))

t.add_resource(ec2.Instance(
   "instance",
   ImageId="ami-0ff8a91507f77f867",
   InstanceType="t2.micro",
   SecurityGroups=[Ref("SecurityGroup")],
   KeyName=Ref("KeyPair"),
   UserData=ud,
))

t.add_output(Output(
  "InstancePublicIp",
  Description="Public IP of our instance.",
  Value=GetAtt("instance", "PublicIp"),
))

t.add_output(Output(
  "WebUrl",
  Description="Application endpoint",
  Value=Join("", [
      "http://", GetAtt("instance", "PublicDnsName"),
      ":", ApplicationPort
  ]),
))

print t.to_json()
