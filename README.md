# aws_script

### 1. repeat_alarm_all.py  
    send SNS message while any alarm is in ALARM state  
    Usage:  
    copy the code to AWS Lambda console function  

### 2. launch_ec2.py  
    launch ec2 and ebs, and then attach the ebs to each ec2  
    Usage:  
    python launch_ec2.py  

### 3. pthread_launch_ec2_v1.py  
    launch ec2 and ebs, and then attach the ebs to each ec2  
    add multi process support in this version  
    Usage:  
    # do launch function  
    python pthread_launch_ec2_v1.py -i run  
    # delete ebs or ec2  
    python pthread_launch_ec2_v1.py -d [ebs|ec2]  
    # show the ebs or ec2 that may delete, but dont't do delect action  
    python pthread_launch_ec2_v1.py -d [ebs|ec2] -t 1  

### 4. pthread_launch_ec2_v2.py  
    launch ec2 and ebs, and then attach the ebs to each ec2  
    add multi process support in this version  
    scan available ebs before attach, rather than recode the ebs id during creating  
    Usage:  
    the same as pthread_launch_ec2_v1.py  

