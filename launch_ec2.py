import boto3
import time

def create_ec2(cnt_ec2, param):
    print('launch', cnt_ec2, 'instance')
    client = boto3.client('ec2', region_name=param['region_name'])
    response = client.run_instances(
	BlockDeviceMappings=[
	    {
		'DeviceName': '/dev/xvda',
		'Ebs': {
		    'DeleteOnTermination': True,
		    'VolumeSize': 8,
		    'VolumeType': 'gp2'
		},
	    },
	],
	ImageId=param['ImageId'],
	InstanceType=param['InstanceType'],
        KeyName=param['KeyName'],
	MaxCount=cnt_ec2,
	MinCount=cnt_ec2,
	Monitoring={
	    'Enabled': False
	},
        SubnetId=param['SubnetId'],
	SecurityGroupIds=[
	    param['SecurityGroupIds'],
	],
    )

    return response['Instances']

def create_ebs(cnt, ebs_size, param):
    print('creating', cnt, 'ebs,', '1-size:', ebs_size, 'GB')
    vol_id = []
    client = boto3.client('ec2')
    for _ in range(cnt):
        response = client.create_volume(
            AvailabilityZone=param['AvailabilityZone'],
            Encrypted=param['Encrypted'],
            Size=ebs_size,
            VolumeType=param['VolumeType'],
            DryRun=param['DryRun'],
            )
        vol_id.append(response['VolumeId'])

    return vol_id

def attach_ebs_ec2(instance, vol_id, cnt_ebs):
    ec2 = boto3.resource('ec2')
    inst_id, vol_index = [], 0

    for x in instance:
        inst_id.append(x['InstanceId'])
    while inst_id:
        x = inst_id[-1]
        res = ec2.Instance(x)
        print("try instance:", x, 'state:', res.state)
        if res.state['Code'] == 16:
            for i in range(cnt_ebs):
                print('\tattach vol_id:', i, vol_id[vol_index+i])
                if i < 25:
                    res.attach_volume(VolumeId=vol_id[vol_index+i],
                            Device='/dev/sd'+chr(i+98)) #/dev/sdb
                elif i < 50:
                    res.attach_volume(VolumeId=vol_id[vol_index+i],
                            Device='/dev/xvd'+chr(i-25+98)) #/dev/xvdb
                else:
                    print("too many ebs attached!")
            inst_id.pop(-1)
            vol_index += i+1
        else:
            time.sleep(2)

if __name__ == "__main__":
    total_ec2, ec2_ebs_each = 30, 30
    total_ebs, size_ebs = 900, 1
    param_ec2 = {
            'ImageId': 'ami-05a85395c8ff37b18',
            'InstanceType': 't2.micro',
            'KeyName': 'target-ningxia-key',
            'region_name': 'cn-northwest-1',
            'SubnetId': 'subnet-0e872f65e7d40368d',
            'SecurityGroupIds': 'sg-012994ecfd68530d6'
            }
    param_ebs = {
            'AvailabilityZone':'cn-northwest-1a',
            'Encrypted':False,
            #'VolumeType':'sc1',
            'VolumeType':'gp2',
            'DryRun':False
            }

    vol_id = create_ebs(total_ebs, size_ebs, param_ebs)
    inst = create_ec2(total_ec2, param_ec2)
    attach_ebs_ec2(inst, vol_id, ec2_ebs_each)

