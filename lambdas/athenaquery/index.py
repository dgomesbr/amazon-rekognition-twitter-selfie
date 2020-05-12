from datetime import datetime
from datetime import timedelta
import json
import urllib
import boto3
import logging
import time
import os
from aws_xray_sdk.core import xray_recorder
from aws_xray_sdk.core import patch

patch(['boto3'])

DdbStatsTable = os.getenv('DdbStatsTable')
S3Bucket = os.getenv('TBucket')

logger = logging.getLogger()
logger.setLevel(logging.INFO)

print('Loading function')

s3_output =  's3://' + S3Bucket + '/selfie-ath-results/'
ath = boto3.client('athena')
dynamodb = boto3.resource("dynamodb")
dyn_table = dynamodb.Table(DdbStatsTable)
timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def AddToDdbStat(result):
    epoch = datetime.utcfromtimestamp(0)
    epochexp = (datetime.now()+timedelta(days=1) - epoch).total_seconds() * 1000.0
    try:
        response = dyn_table.put_item(
          Item={
              'id': result[0]['etype'],
              'dt': timestamp,
              'face_id': result[0]['face_id'],
              'image_url': result[0]['image_url'],
              'first_name': result[0]['first_name'],
              'last_name': result[0]['last_name'],
              'age': result[0]['age'],
              'gender': result[0]['gender_value'],
              'confidence': result[0]['confidence'],
              'expire_at': int(epochexp)
          }
        )    
        return True

    except Exception as e:
        logger.error(e)
        return False

def fetchall_athena(query_string, emotion):
    query_id = ath.start_query_execution(
        QueryString=query_string,
        QueryExecutionContext={
            'Database': 'DATABASE_NAME'
        },
        ResultConfiguration={
            'OutputLocation': s3_output + emotion
        }
    )['QueryExecutionId']
    query_status = None
    while query_status == 'QUEUED' or query_status == 'RUNNING' or query_status is None:
        query_status = ath.get_query_execution(QueryExecutionId=query_id)['QueryExecution']['Status']['State']
        if query_status == 'FAILED' or query_status == 'CANCELLED':
            raise Exception('Athena query with the string "{}" failed or was cancelled'.format(query_string))
        time.sleep(5)
        results_paginator = ath.get_paginator('get_query_results')
        results_iter = results_paginator.paginate(
            QueryExecutionId=query_id,
            PaginationConfig={
                'PageSize': 1000
            }
        )
    results = []
    column_names = None
    for results_page in results_iter:
        for row in results_page['ResultSet']['Rows']:
           column_values = [col.get('VarCharValue', None) for col in row['Data']]
           if not column_names:
               column_names = column_values
           else:
               results.append(dict(zip(column_names, column_values)))
    
    return results
        
def handler(event, context):
        #logger.info(event)
    
        res = fetchall_athena(event["query"], event["type"])

        logger.info(res)
        # AddToDdbStat(res)

        return {'result': True}