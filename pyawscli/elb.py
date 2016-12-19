import time

class ElbInServiceTimeoutException(Exception):
	def __init__(self, elb, instances, timeout):
		super(ElbInServiceTimeoutException, self).__init__("Waited more than "+str(timeout)+" seconds for instances "+str(instances)+"to become in service for load balancer "+elb)

class ELB:
	def __init__(self, client):
		self.client = client

	def balancers(self, region=None, profile=None):
		args = ['describe-load-balancers']
		args = self.prepare_args(args, region, profile)
		res = self.client.execute(args, region=region, profile=profile)
		return res['LoadBalancerDescriptions']

	def balancers_by(self, key, val, region=None, profile=None):
		balancers = self.balancers(region=region, profile=profile)
		return [i for i in balancers if i[key]==val]		

	def balancer_by_name(self, name, region=None, profile=None):
		balancers = self.balancers_by('LoadBalancerName', name, region=region, profile=profile)
		return balancers[0] if len(balancers) else None

	def health(self, name, region=None, profile=None):
		args = ['describe-instance-health','--load-balancer-name',name]
		args = self.prepare_args(args, region, profile)
		res = self.client.execute(args, region=region, profile=profile)
		return res['InstanceStates']

	def register_instances(self, elb_name, instances, wait_for_service=None, wait_timeout=600, throw_on_timeout=True, region=None, profile=None):
		if not isinstance(instances, list):
			instances = [instances]
		args = ['register-instances-with-load-balancer','--load-balancer-name',elb_name,'--instances']
		instances = [i for i in instances if isinstance(i,str)]+[i['InstanceId'] for i in instances if isinstance(i,dict) and 'InstanceId' in i]
		args+=instances
		args = self.prepare_args(args, region, profile)
		res = self.client.execute(args, region=region, profile=profile)
		_instances = res['Instances']
		if wait_for_service is not None and wait_for_service!=False:
			wait_for_service = len(instances) if not isinstance(wait_for_service, int) else wait_for_service
			return self.wait_for_service(elb_name, instances, wait_for_service, wait_timeout, throw_on_timeout)
		return _instances

	def deregister_instances(self, elb_name, instances, region=None, profile=None):
		if not isinstance(instances, list):
			instances = [instances]
		args = ['deregister-instances-from-load-balancer','--load-balancer-name',elb_name,'--instances']
		instances = [i for i in instances if isinstance(i,str)]+[i['InstanceId'] for i in instances if isinstance(i,dict) and 'InstanceId' in i]
		args+=instances
		args = self.prepare_args(args, region, profile)
		res = self.client.execute(args, region=region, profile=profile)
		return res['Instances']

	def wait_for_service(self, elb_name, instance_ids, num, timeout, throw):
		then = time.time()
		ready = False
		while not ready:
			now = time.time()
			instances = self.health(elb_name)
			instances_in_service = [i for i in instances if i['InstanceId'] in instance_ids and i['State']=='InService']
			if len(instances_in_service) >= num:
				ready = True
			elif now-then>timeout:
				if throw:
					raise ElbInServiceTimeoutException(elb_name, instance_ids, timeout)
				else:
					break
			time.sleep(5)
		return instances_in_service	

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
		args = ['elb'] + args
		if region is not None:
			args = args + ['--region', region]
		if profile is not None:
			args = args + ['--profile', profile]
		return args