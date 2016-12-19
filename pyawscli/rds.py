class RDS:
	def __init__(self, client):
		self.client = client

	def instances(self, region=None, profile=None):
		args = ['describe-db-instances']
		args = self.prepare_args(args, region, profile)
		res = self.client.execute(args, region=region, profile=profile)
		return res['DBInstances']

	def instances_by(self, key, val, region=None, profile=None):
		instances = self.instances(region=region, profile=profile)
		return [i for i in instances if i[key]==val]		

	def instance_by_id(self, id, region=None, profile=None):
		instances = self.instances_by('DBInstanceIdentifier', id, region=region, profile=profile)
		return instances[0] if len(instances) else None

	def instances_by_keyname(self, keyname, region=None, profile=None):
		instances = self.instances(region=region, profile=profile)
		return [i for i in instances if i['KeyName']==keyname]

	def instances_by_name(self, name, region=None, profile=None):
		return self.instances_by_tags([('Name', name)])

	def instance_matches_tags(self, instance, tags):
		if 'Tags' not in instance:
			return False
		for t in tags:
			key = t[0]
			val = t[1]
			for t in instance['Tags']:
				if 'Key' in t and t['Key']==key and 'Value' in t and t['Value']==val:					return True
		return False

	def prepare_args(self, args, region, profile):
		args = ['rds'] + args
		if region is not None:
			args = args + ['--region', region]
		if profile is not None:
			args = args + ['--profile', profile]
		return args