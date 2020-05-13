from datetime import datetime
from datetime import timedelta
import json
import urllib
import boto3
import logging
import time
import os
from aws_xray_sdk.core import xray_recorder
from aws_xray_sdk.core import patch_all

patch_all()

s3_bucket = os.getenv('TBucket')
AthDispatcherLambdaName = os.getenv('AthDispatcherLambdaName')

logger = logging.getLogger()
logger.setLevel(logging.INFO)

print('Loading function')

client = boto3.client('s3')
s3 = boto3.resource('s3')
lambda_client = boto3.client('lambda')

payload = {}

def handler(event, context):
    try:
        xray_recorder.begin_subsegment('handler')
        xray_recorder.current_subsegment().put_annotation('Lambda', context.function_name)
        #logger.info(event)        
        if 'body' not in event:
            logger.error( 'Missing parameters')
            return {'result': False, 'msg': 'Missing parameters' }
            
        body = json.loads(event['body'])
        
        logger.info(body)
        s3.Object(s3_bucket, 'selfie-reports/' + body['id'] + '.json').delete()                
        logger.info('DELETED: selfie-reports/' + body['id'] + '.json')
        
        # Get the lastest csv for deletion
        get_last_modified = lambda obj: int(obj['LastModified'].strftime('%s')) 
        objs = client.list_objects_v2(Bucket=s3_bucket, Prefix='selfie-ath-results/' + body['emotion'])['Contents']
        file_list = [obj['Key'] for obj in sorted(objs, key=get_last_modified, reverse=True)]
        for csv_file in file_list:
            if "metadata" in csv_file:
                continue
            s3.Object(s3_bucket, csv_file).delete()
            logger.info('DELETED: ' +  csv_file)      
            break

        payload["type"] = "delselfie"

        response = client.invoke(
                FunctionName=AthDispatcherLambdaName,
                InvocationType='Event',
                Payload=json.dumps(payload)
            )

        logger.info(response)
        
        return {'result': True, 'selfie': 'selfie-reports/' + body['id'] + '.json', 'csv': 'selfie-ath-results/' + body['emotion'] + '/' + csv_file}

    except Exception as e:
        logger.error('Something went wrong: ' + str(e))
        return {'result': False, 'msg': str(e)}