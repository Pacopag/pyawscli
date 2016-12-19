import json, sys, time, datetime
from subprocess import Popen, PIPE
from .iam import IAM
from .ec2 import EC2
from .rds import RDS
from .elb import ELB
from .autoscaling import Autoscaling

class AwsClient:
	def __init__(self, 
		profile=None, 
		region=None,
		exit_on_error=True,
		error_handler=None):
		self.profile = profile
		self.region = region
		self.exit_on_error = exit_on_error
		self.error_handler = error_handler
		self.iam = IAM(self)
		self.ec2 = EC2(self)
		self.rds = RDS(self)
		self.elb = ELB(self)
		self.autoscaling = Autoscaling(self)
		self.owner_id = self.iam.get_owner_id()


	def raw(self, command):
		args = command.split(' ')+['--profile', self.profile]
		self.execute(args)
		
	def execute(self, args, region=None, profile=None):
		args = self.prepare_args(args, region=region, profile=profile)
		p = Popen(args, stdin=PIPE, stdout=PIPE, stderr=PIPE)
		aws, err = p.communicate()
		if len(aws):
			aws = json.loads(aws.decode('utf-8'))
		if len(err):
			self.handle_error(err, args)
		return aws

	def handle_error(self, err, args):
		if self.error_handler is not None:
			self.error_handler(err, args)
		if self.exit_on_error:
			sys.exit(1)

	def prepare_args(self, args, region=None, profile=None):
		if args[0]!='aws':
			args = ['aws']+args

		region = self.get_region(region)
		if '--region' not in args and region is not None:
			args = args+['--region', region]

		profile = self.get_profile(profile)
		if '--profile' not in args and profile is not None:
			args = args+['--profile', profile]

		return args


	def get_region(self, region=None):
		return region if region is not None else self.region

	def get_profile(self, profile=None):
		return profile if profile is not None else self.profile	

	def create_stamp(self):
		now = datetime.datetime.utcnow()
		return ''.join(str(now).replace(' ','-').replace(':','-').split('.')[0:-1])
