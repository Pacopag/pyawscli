class Autoscaling:
	def __init__(self, client):
		self.client = client

	def launch_configurations(self, region=None, profile=None):
		args = ['describe-launch-configurations']
		args = self.prepare_args(args, region, profile)
		res = self.client.execute(args, region=region, profile=profile)
		return res['LaunchConfigurations']

	def launch_configurations_by(self, key, val, region=None, profile=None):
		launch_configurations = self.launch_configurations(region=region, profile=profile)
		return [i for i in launch_configurations if i[key]==val]

	def launch_configuration_by_name(self, name, region=None, profile=None):
		launch_configurations = self.launch_configurations_by('LaunchConfigurationName', name, region=region, profile=profile)
		return launch_configurations[0] if len(launch_configurations)>0 else None

	def create_launch_configuration(self, image, instance_type, key_name, security_groups, name_prefix=None, region=None, profile=None):
		stamp = self.client.create_stamp()
		image_id = image if isinstance(image, str) else image['ImageId']
		if name_prefix is not None:
			name = name+'-'+stamp
		elif not isinstance(image, str) and 'Name' in image:
			name = image['Name']
		else:
			name = image_id+'-'+stamp
		security_groups = security_groups if isinstance(security_groups, list) else [security_groups]
		args = ['create-launch-configuration', '--launch-configuration-name', name, '--image-id', image_id, '--instance-type', instance_type, '--key-name', key_name, '--security-groups']+security_groups
		args = self.prepare_args(args, region, profile)
		self.client.execute(args, region=region, profile=profile)
		return name

	def delete_launch_configuration(self, name, region=None, profile=None):
		args = ['delete-launch-configuration', '--launch-configuration-name', name]
		args = self.prepare_args(args, region, profile)
		return self.client.execute(args, region=region, profile=profile)

	def scaling_groups(self, region=None, profile=None):
		args = ['describe-auto-scaling-groups']
		args = self.prepare_args(args, region, profile)
		res = self.client.execute(args, region=region, profile=profile)
		return res['AutoScalingGroups']

	def scaling_groups_by(self, key, val, region=None, profile=None):
		scaling_groups = self.scaling_groups(region=region, profile=profile)
		return [i for i in scaling_groups if i[key]==val]

	def scaling_group_by_name(self, name, region=None, profile=None):
		scaling_groups = self.scaling_groups_by('AutoScalingGroupName', name, region=region, profile=profile)
		return scaling_groups[0] if len(scaling_groups)>0 else None

	def update_scaling_group_launch_config(self, scaling_group, launch_config, region=None, profile=None):
		scaling_group_name = scaling_group if isinstance(scaling_group, str) else scaling_group['AutoScalingGroupName']
		launch_config_name = launch_config if isinstance(launch_config, str) else launch_config['LaunchConfigurationName']
		args = ['update-auto-scaling-group', '--auto-scaling-group-name', scaling_group_name, '--launch-configuration-name', launch_config_name]
		args = self.prepare_args(args, region, profile)
		return self.client.execute(args, region=region, profile=profile)

	def prepare_args(self, args, region, profile):
		args = ['autoscaling'] + args
		if region is not None:
			args = args + ['--region', region]
		if profile is not None:
			args = args + ['--profile', profile]
		return args