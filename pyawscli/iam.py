class IAM:
	def __init__(self, client):
		self.client = client

	def get_user(self, region=None, profile=None):
		args = ['get-user']
		args = self.prepare_args(args, region, profile)
		res = self.client.execute(args, region=region, profile=profile)
		return res['User']

	def get_owner_id(self, region=None, profile=None):
		user = self.get_user(region=region, profile=profile)
		arn = user['Arn']
		return arn.split(':')[4]

	def prepare_args(self, args, region, profile):
		args = ['iam'] + args
		if region is not None:
			args = args + ['--region', region]
		if profile is not None:
			args = args + ['--profile', profile]
		return args