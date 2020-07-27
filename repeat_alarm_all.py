import boto3

def send_sns(alarm, sns):
    response = ''
    if 'AlarmName' in alarm:
        print("send repeat sns:", alarm['AlarmName'])
        actions = alarm['AlarmActions']
        for arn in actions:
            response = sns.publish(TopicArn=arn,
                    Message='Repeat Alarm Notifications.\n'+'Reason:' + alarm['StateReason'],
                    Subject='AlARM:' + alarm['AlarmName'],
                    MessageAttributes={"Attri":{'DataType': 'String', 'StringValue': 'val'}})
    return response

def lambda_handler(event, context):
    response, alarm_all = '', {}
    cloudwatch = boto3.client('cloudwatch')
    sns = boto3.client('sns')
    if cloudwatch and sns:
        alarm_all = cloudwatch.describe_alarms(StateValue='ALARM')
    for alarm_class in alarm_all:
        for alarm in alarm_all[alarm_class]:
            response = send_sns(alarm, sns)
    return response
