import time, datetime

class EC2:
	def __init__(self, client):
		self.client = client

	def instances(self, region=None, profile=None):
		args = ['describe-instances']
		args = self.prepare_args(args, region, profile)
		res = self.client.execute(args, region=region, profile=profile)
		instances = []
		for r in res['Reservations']:
			instances = instances+r['Instances']
		return instances

	def instances_by(self, key, val, region=None, profile=None):
		instances = self.instances(region=region, profile=profile)
		return [i for i in instances if i[key]==val]		

	def instance_by_id(self, id, region=None, profile=None):
		instances = self.instances_by('InstanceId', id, region=region, profile=profile)
		return instances[0] if len(instances) else None

	def instances_by_tags(self, tags, region=None, profile=None):
		instances = self.instances(region=region, profile=profile)
		return [i for i in instances if self.instance_matches_tags(i, tags)]

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

	def instances_in_scaling_group(self, group, region=None, profile=None):
		group_name = group if isinstance(group, str) else group['AutoScalingGroupName']
		return self.instances_by_tags([('aws:autoscaling:groupName', group_name)], region=region, profile=profile)

	def terminate_instances(self, instances, region=None, profile=None):
		if not isinstance(instances, list):
			instances = [instances]
		instance_ids = []
		for instance in instances:
			instance_ids.append(instance if isinstance(instance, str) else instance['InstanceId'])
		args = ['terminate-instances', '--instance-ids']+instance_ids
		args = self.prepare_args(args, region, profile)
		res = self.client.execute(args, region=region, profile=profile)
		return res['TerminatingInstances']

	def snapshots(self, region=None, profile=None, owner_ids='auto'):
		args = ['describe-snapshots']
		args = self.prepare_args(args, region, profile)
		if isinstance(owner_ids, list):
			args = args + ['--owner-ids'] + owner_ids
		elif owner_ids=='auto' and self.client.owner_id is not None:
			args = args + ['--owner-ids', self.client.owner_id]
		res = self.client.execute(args, region=region, profile=profile)
		return res['Snapshots']

	def snapshots_by(self, key, val, region=None, profile=None):
		snapshots = self.snapshots(region=region, profile=profile)
		return [s for s in snapshots if s[key]==val]

	def volumes(self, region=None, profile=None):
		args = ['describe-volumes']
		args = self.prepare_args(args, region, profile)
		res = self.client.execute(args, region=region, profile=profile)
		return res['Volumes']

	def instance_volumes(self, id, region=None, profile=None):
		instance = self.instance_by_id(id, region=region, profile=profile)
		if instance is None:
			return []
		return instance['BlockDeviceMappings']

	def instance_volume_by_name(self, id, name, region=None, profile=None):
		volumes = self.instance_volumes(id, region=region, profile=profile)
		volumes = [v for v in volumes if v['DeviceName']==name]
		return volumes[0] if len(volumes) else None

	def create_snapshot(self, volume_id, description=None, region=None, profile=None):
		if description is None:
			description = volume_id+'-'+self.client.create_stamp()
		args = ['create-snapshot']
		args = self.prepare_args(args, region, profile)
		args = args + ['--volume-id', volume_id, '--description', description]
		return self.client.execute(args, region=region, profile=profile)

	def create_snapshot_of_instance_volume(self, instance, volume_name, description=None, region=None, profile=None):
		instance_id = instance if isinstance(instance, str) else instance['InstanceId']
		volume = self.instance_volume_by_name(instance_id, volume_name, region=region, profile=profile)
		volume_id = volume['Ebs']['VolumeId']
		return self.create_snapshot(volume_id, description=description, region=region, profile=profile)

	def delete_snapshot(self, snapshot, region=None, profile=None):
		snapshot_id = snapshot if isinstance(snapshot, str) else snapshot['SnapshotId']
		args = ['delete-snapshot', '--snapshot-id', snapshot_id]
		args = self.prepare_args(args, region, profile)
		return self.client.execute(args, region=region, profile=profile)

	def delete_snapshots(self, snapshots, region=None, profile=None):
		for s in snapshots:
			snapshot_id = s if isinstance(s, str) else s['SnapshotId']
			try:
				self.delete_snapshot(snapshot_id, region=region, profile=profile)
			except:
				pass

	def cleanup_snapshots_in_error(self, region=None, profile=None):
		snapshots = self.snapshots_by('State', 'error', region=region, profile=profile)
		self.delete_snapshots(snapshots)

	def cleanup_snapshots_of_volume(self, volume_id, retain=1, region=None, profile=None):
		self.cleanup_snapshots_in_error(region=region, profile=profile)
		snapshots = self.snapshots_by('VolumeId', volume_id)
		snapshots = [s for s in snapshots if 'CreateImage' not in s['Description']]
		snapshots = sorted(snapshots, key=lambda k: k['StartTime'])[:-retain]
		self.delete_snapshots(snapshots)

	def cleanup_snapshots_from_amis(self, region=None, profile=None):
		amis = self.amis()
		ami_ids = [a['ImageId'] for a in amis]
		snapshots = self.snapshots(region=region, profile=profile)
		snapshots_to_delete = []
		for s in snapshots:
			ami_id = self.ami_id_from_snapshot(s)
			if ami_id is not None and ami_id not in ami_ids:
				snapshots_to_delete.append(s)
		self.delete_snapshots(snapshots_to_delete, region=region, profile=profile)

	def snapshot_is_from_ami(self, snapshot):
		description = snapshot['Description']
		return 'CreateImage' in description and 'ami-' in description

	def ami_id_from_snapshot(self, snapshot):
		if not self.snapshot_is_from_ami(snapshot):
			return None
		description = snapshot['Description']
		description = description[description.index('ami-'):]
		return description[:description.index(' ')]

	def amis(self, ami_ids=None, region=None, profile=None, owner_ids='auto'):
		args = ['describe-images']
		args = self.prepare_args(args, region, profile)
		if isinstance(owner_ids, list):
			args = args + ['--owners'] + owner_ids
		elif owner_ids=='auto' and self.client.owner_id is not None:
			args = args + ['--owners', self.client.owner_id]
		if isinstance(ami_ids, list):
			args = args + ['--image-ids']+ami_ids
		res = self.client.execute(args, region=region, profile=profile)
		return res['Images']

	def create_ami(self, instance, name_prefix=None, no_reboot=False, wait_for_state=False, wait_timeout=300, region=None, profile=None):
		instance_id = instance if isinstance(instance, str) else instance['InstanceId']
		if name_prefix is None:
			name_prefix = instance_id
		name = name_prefix+'-'+self.client.create_stamp()
		args = ['create-image', '--instance-id', instance_id, '--name', name]
		if no_reboot:
			args = args+['--no-reboot']
		args = self.prepare_args(args, region, profile)
		res = self.client.execute(args, region=region, profile=profile)
		if wait_for_state:
			start_time = time.time()
			done = False
			while not done:
				amis = self.amis(ami_ids=[res['ImageId']], region=region, profile=profile)
				res = amis[0]
				if res['State']!='pending' or time.time()-start_time>wait_timeout:
					done = True
				else:
					time.sleep(10)
		return res

	def deregister_ami(self, ami, region=None, profile=None):
		ami_id = ami if isinstance(ami, str) else ami['ImageId']
		args = ['deregister-image', '--image-id', ami_id]
		args = self.prepare_args(args, region, profile)
		return self.client.execute(args, region=region, profile=profile)

	def deregister_amis(self, amis, region=None, profile=None):
		for a in amis:
			ami_id = a if isinstance(a, str) else a['ImageId']
			try:
				self.deregister_ami(ami_id, region=region, profile=profile)
			except:
				pass

	def cleanup_amis_with_prefix(self, prefix, retain=1, region=None, profile=None):
		amis = self.amis(region=region, profile=profile)
		amis = [a for a in amis if a['Name'].startswith(prefix)]
		amis = sorted(amis, key=lambda k: k['CreationDate'])[:-retain]
		self.deregister_amis(amis, region=region, profile=profile)

	def security_groups(self, region=None, profile=None):
		args = ['describe-security-groups']
		args = self.prepare_args(args, region, profile)
		res = self.client.execute(args, region=region, profile=profile)
		return res['SecurityGroups']

	def security_groups_by(self, key, val, region=None, profile=None):
		security_groups = self.security_groups(region=region, profile=profile)
		return [i for i in security_groups if i[key]==val]

	def security_group_by_id(self, id, region=None, profile=None):
		security_groups = self.security_groups_by('GroupId', id, region=region, profile=profile)
		return security_groups[0] if len(security_groups) else None

	def security_groups_by_name(self, name, region=None, profile=None):
		return self.security_groups_by('GroupName', name, region=region, profile=profile)

	def prepare_args(self, args, region, profile):
		args = ['ec2'] + args
		if region is not None:
			args = args + ['--region', region]
		if profile is not None:
			args = args + ['--profile', profile]
		return args