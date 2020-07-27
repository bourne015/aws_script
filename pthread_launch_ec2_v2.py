import boto3
import time
import multiprocessing
import argparse
from botocore.config import Config

def create_ec2(client, param):
    print('launch', param['MaxCount'], 'instance')
    #client = boto3.client('ec2', region_name=param['region_name'])
    response = client.run_instances(
	BlockDeviceMappings=param['BlockDeviceMappings'],
	ImageId=param['ImageId'],
	InstanceType=param['InstanceType'],
        KeyName=param['KeyName'],
	MaxCount=param['MaxCount'],
	MinCount=param['MinCount'],
	Monitoring=param['Monitoring'],
        SubnetId=param['SubnetId'],
	SecurityGroupIds=param['SecurityGroupIds'],
        TagSpecifications=param['TagSpecifications']
        )

    return response['Instances']

def do_create_ebs(client, cnt, param):
    print('creating', cnt, 'ebs,', '1-size:', param['Size'], 'GB')
    for _ in range(cnt):
        response = client.create_volume(
            AvailabilityZone=param['AvailabilityZone'],
            Encrypted=param['Encrypted'],
            Size=param['Size'],
            VolumeType=param['VolumeType'],
            DryRun=param['DryRun'],
            )

def create_ebs(client, total_ebs, param, cnt_thread):
    cnt_ebs_th = total_ebs//cnt_thread
    remain = total_ebs - cnt_ebs_th*cnt_thread

    pool = multiprocessing.Pool(cnt_thread)
    p_lock = multiprocessing.Manager().Lock()
    thread_list = []
    if cnt_ebs_th > 0:
        for _ in range(cnt_thread):
            th = multiprocessing.Process(target=do_create_ebs,
                        args=(client, cnt_ebs_th, param))
            thread_list.append(th)
            #pool.apply_async(func=do_create_ebs,
            #            args=(cnt_ebs_th, param, vol_id, p_lock,))
    if remain > 0:
        #pool.apply_async(func=do_create_ebs,
        #          args=(remain, param, vol_id, p_lock,))
        th = multiprocessing.Process(target=do_create_ebs,
                    args=(client, remain, param))
        thread_list.append(th)
    for th in thread_list:
        th.start()
    #for th in thread_list:
    #    th.join()
    #pool.close()
    #pool.join()

def do_attach(ec2, inst_id, vol_id, cnt_ebs):
    vol_index = 0

    while inst_id:
        x = inst_id[-1]
        res = ec2.Instance(x)
        print("ec2:", x, 'state:', res.state)
        if res.state['Code'] == 16:
            for i in range(cnt_ebs):
                #print('\tattach:', vol_id[vol_index+i], 'to', x)
                if i < 25:
                    res.attach_volume(VolumeId=vol_id[vol_index+i],
                            Device='/dev/sd'+chr(i+98)) #/dev/sdb
                elif i < 50:
                    res.attach_volume(VolumeId=vol_id[vol_index+i],
                            Device='/dev/xvd'+chr(i-25+98)) #/dev/xvdb
                else:
                    print("too many ebs attached!")
            inst_id.pop(-1)
            vol_index += cnt_ebs
            print('\tattached', i+1, 'ebs')
        else:
            time.sleep(4)

def attach_ebs_ec2(ec2, instance, ebs_cnt_ec2, cnt_thread, param_ebs):
    #ec2 = boto3.resource('ec2')
    thread_list, vol_index, tmp = [], 0, []
    inst_id = [] #multiprocessing.Manager().list()

    cnt = len(instance)//cnt_thread
    ec2_cnt_th = 1 if cnt == 0 else cnt
    #p_lock = multiprocessing.Lock()
    #count = multiprocessing.Value('I', 1)

    for i, x in enumerate(instance):
        tmp.append(x['InstanceId'])

    inst_id = [tmp[i:i+ec2_cnt_th] for i in range(0, len(tmp), ec2_cnt_th)]
    vol_id = wait_ebs_ec2_ready(ec2, inst_id[0][0],
                len(tmp)*ebs_cnt_ec2, param_ebs)
    print(len(vol_id), 'ebs', 'ready')

    for i, ec2_group in enumerate(inst_id):
        th = multiprocessing.Process(target=do_attach,
                args=(ec2, ec2_group, vol_id[vol_index:], ebs_cnt_ec2))
        thread_list.append(th)
        vol_index += len(ec2_group)*ebs_cnt_ec2

    for th in thread_list:
        th.start()
    for th in thread_list:
        th.join()

def wait_ebs_ec2_ready(ec2, instid, total_ebs, param_ebs):
    while True:
        res1 = ec2.Instance(instid)
        if res1.state['Code'] == 16:
            break
        print('waiting ec2')
        time.sleep(4)
    while True:
        print('waiting ebs')
        volume_all = ec2.volumes.filter(
                Filters=[
                    {
                        'Name': 'status',
                        'Values': [
                            'available',
                        ]
                    },
                    {
                        'Name': 'size',
                        'Values': [
                            str(param_ebs['Size']),
                        ]
                    },
                ],
                DryRun=False,
            )
        i = 0
        for _ in volume_all:
            i+=1
        if i == total_ebs:
            break
        time.sleep(3)
    vol_id = []
    for x in volume_all:
        vol_id.append(x.id)
    return vol_id

def do_del_ebs(ec2, volume_id):
    for i, x in enumerate(volume_id):
        volume = ec2.Volume(x)
        print('delete:', x, volume.state)
        if volume.state == 'available':
            volume.delete(DryRun=False)

def del_ebs(ec2, param, cnt_thread, test):
    #ec2 = boto3.resource('ec2', region_name='cn-northwest-1')
    volume_all = ec2.volumes.filter(
            Filters=[
                {
                    'Name': 'status',
                    'Values': [
                        'available',
                    ]
                },
                {
                    'Name': 'size',
                    'Values': [
                        str(param['Size']),
                    ]
                },
            ],
            DryRun=False,
            #MaxResults=5
        )
    vol_id, thread_list = [], []
    for i, x in enumerate(volume_all):
        vol_id.append(x.id)
    print('total:', len(vol_id))
    if test == 1 or len(vol_id) == 0:
        return
    cnt = len(vol_id)//cnt_thread
    vol_cnt_th = 1 if cnt == 0 else cnt
    vol_id_g = [vol_id[i:i+vol_cnt_th] for i in range(0,len(vol_id),vol_cnt_th)]
    #pool = multiprocessing.Pool(len(vol_id_g))
    for vol_group in vol_id_g:
        th = multiprocessing.Process(target=do_del_ebs,
                args=(ec2, vol_group))
        thread_list.append(th)
    for th in thread_list:
        th.start()
    for th in thread_list:
        th.join()

def del_ec2(ec2, param, test):
    instance_all = ec2.instances.filter(
        Filters=[
            {
                'Name': 'tag:Name',
                'Values': [
                    param['TagSpecifications'][0]['Tags'][0]['Value'],
                ]
            },
            {
                'Name': 'instance-state-name',
                'Values': [
                    'pending',
                    'running',
                    'shutting-down',
                    'stopping',
                    'stopped',
                ]
            },
        ],
        DryRun=False,
    )
    instance_id = []
    for i, x in enumerate(instance_all):
        #print(i, x.id)
        instance_id.append(x.id)
    print('total:', len(instance_id))

    if test == 1 or len(instance_id) == 0:
        return
    response = client.terminate_instances(
        InstanceIds=instance_id,
        DryRun=False
    )
if __name__ == "__main__":
    ###########parameters need to configure############
    total_ec2, ec2_ebs_each = 10, 5
    total_ebs, size_ebs = 50, 1
    pthread_cnt = 12
    param_ec2 = {
            'BlockDeviceMappings':[{
		'DeviceName': '/dev/xvda',
		'Ebs': {
		    'DeleteOnTermination': True,
		    'VolumeSize': 8,
		    'VolumeType': 'gp2'
		},
	    },],
	    'ImageId': 'ami-05a85395c8ff37b18',
            'InstanceType': 't2.micro',
            'KeyName': 'target-ningxia-key',
            'region_name': 'cn-northwest-1',
            'MaxCount':total_ec2,
            'MinCount':total_ec2,
            'Monitoring':{
	        'Enabled': False
	    },
            'SubnetId': 'subnet-0e872f65e7d40368d',
            'SecurityGroupIds': [
                'sg-012994ecfd68530d6',
                ],
            'TagSpecifications':[
                {'ResourceType':'instance',
                'Tags':[{'Key': 'Name','Value': 'test123'},]
                },
            ],
            }
    param_ebs = {
            'AvailabilityZone':'cn-northwest-1a',
            'Encrypted':False,
            'Size':size_ebs,
            #'VolumeType':'sc1',
            'VolumeType':'gp2',
            'DryRun':False
            }
    config = Config(
       retries = {
          'max_attempts': 20,
          'mode': 'standard'
       }
    )
    access_key = None
    secret_access_key = None
    ############################################

    session = boto3.Session(
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_access_key
    )
    client = session.client('ec2', region_name=param_ec2['region_name'], config=config)
    ec2 = session.resource('ec2', region_name=param_ec2['region_name'], config=config)

    parser = argparse.ArgumentParser()
    parser.description='''e.g.\
                python xxx.py -i run | -d ebs [-t 1]'''
    parser.add_argument('-i', help='run instance[run]',  type=str, default='n')
    parser.add_argument('-d', help='delete target[ebs|ec2]',  type=str, default='')
    parser.add_argument('-t', help='test but not delete[0|1]',  type=int, default=0)
    args = parser.parse_args()

    if args.i == 'run':
        create_ebs(client, total_ebs, param_ebs, pthread_cnt)
        inst = create_ec2(client, param_ec2)
        attach_ebs_ec2(ec2, inst, ec2_ebs_each, pthread_cnt, param_ebs)

    if args.d == 'ebs':
        del_ebs(ec2, param_ebs, pthread_cnt, args.t)
    elif args.d == 'ec2':
        del_ec2(ec2, param_ec2, args.t)

