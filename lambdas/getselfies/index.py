from datetime import datetime, timedelta
from boto3.dynamodb.conditions import Key, Attr
import decimal
import json
import urllib
import boto3
import logging
import csv
import os
from aws_xray_sdk.core import xray_recorder
from aws_xray_sdk.core import patch_all

patch_all()

DdbStatsTable = os.getenv('DdbStatsTable')
s3_bucket = os.getenv('TBucket')

logger = logging.getLogger()
logger.setLevel(logging.INFO)

print('Loading function')

s3 = boto3.resource('s3')
s3_client = boto3.client('s3')
dynamodb = boto3.resource("dynamodb")
dyn_table = dynamodb.Table(DdbStatsTable)

status = ["success", "error", "moderated"]
rekEmotions = ["HAPPY","SAD","ANGRY","CONFUSED","DISGUSTED","SURPRISED","CALM","FEAR"]

prefixes = []
for e in rekEmotions:
    prefixes.append(str("selfie-ath-results/" + e))

# Helper class to convert a DynamoDB item to JSON.
class DecimalEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, decimal.Decimal):
            if o % 1 > 0:
                return float(o)
            else:
                return int(o)
        return super(DecimalEncoder, self).default(o)

def GetStats():
    try:
        items = []
        for s in status:
            response = dyn_table.query(
                KeyConditionExpression=Key('id').eq(str(s)) & Key('dt').begins_with(datetime.now().strftime("%Y")),
            )

            for i in response["Items"]:              
                #items.setdefault("STATS", []).append(json.dumps(i, cls=DecimalEncoder))
                items.append(json.dumps(i, cls=DecimalEncoder))

            while 'LastEvaluatedKey' in response:
                response = dyn_table.query(
                    KeyConditionExpression=Key('id').eq(str(s)) & Key('dt').begins_with(datetime.now().strftime("%Y")),          
                    ExclusiveStartKey=response['LastEvaluatedKey']
                )
                for i in response["Items"]:
                    #items.setdefault("STATS", []).append(json.dumps(i, cls=DecimalEncoder))
                    items.append(json.dumps(i, cls=DecimalEncoder))

        return items

    except Exception as e:
        logger.error(e)
        return items

def handler(event, context):
    try:
        xray_recorder.begin_subsegment('handler')
        xray_recorder.current_subsegment().put_annotation('Lambda', context.function_name)
        
        get_last_modified = lambda obj: int(obj['LastModified'].strftime('%s')) 
    
        emotions_results = {}
        
        for prefix in prefixes:
            try:
                objs = s3_client.list_objects_v2(Bucket=s3_bucket, Prefix=prefix)['Contents']
                file_list = [obj['Key'] for obj in sorted(objs, key=get_last_modified, reverse=True)]
            except Exception as e:
                continue
            
            for csv_file in file_list:
                if "metadata" in csv_file:
                    continue
                #logger.info('result: ' + csv_file)
                break
            
            obj = s3.Object(s3_bucket, csv_file)
            lines = obj.get()['Body'].read().decode('utf-8').split() 
            for row in csv.DictReader(lines):
                for e in rekEmotions:
                    if e in prefix:
                        emotions_results[e] = row
                        break
            
            #for s in GetStats():
            #    emotions_results.setdefault("STATS", []).append(json.loads(s)) 
            #emotions_results.setdefault("STATS", GetStats())
            print(json.dumps(emotions_results))
                    
        return json.dumps(emotions_results)

    except Exception as e:
        logger.error('Something went wrong: ' + str(e))
        return {'result': False, 'msg': str(e)}