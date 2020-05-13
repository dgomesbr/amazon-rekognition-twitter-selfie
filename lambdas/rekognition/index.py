from datetime import datetime, timedelta
import json
import urllib
import boto3
import logging
import uuid
import urllib 
import io
import os
import requests
from aws_xray_sdk.core import xray_recorder
from aws_xray_sdk.core import patch_all

patch_all()

DdbStatsTable = os.getenv('DdbStatsTable')
S3Bucket = os.getenv('TBucket')
CollectionId = os.getenv('CollectionId')

logger = logging.getLogger()
logger.setLevel(logging.INFO)

s3 = boto3.client('s3')
s3_bucket = S3Bucket

rek = boto3.client('rekognition')
dynamo_client = boto3.client('dynamodb')

status = ["success", "error", "moderated"]
year_week = datetime.now().strftime("%Y-W%U")
year_month = datetime.now().strftime("%Y-%m")

def Initialize():    
    try:
        rek.create_collection(
        CollectionId=CollectionId,
    )
    except Exception as e:
        logger.warning(e)
    
@xray_recorder.capture('Initialize Ddb')
def InitializeStat(dt):
    items = []
    for s in status:    
        items.append(
            {
                'Put': 
                    {
                    'TableName': DdbStatsTable,
                    "Item": {
                        "id": {"S": str(s) },
                        "dt": {"S": str(dt) },
                        "total_count": {"N": "0" }
                    },
                    "ConditionExpression": "attribute_not_exists(total_count)"
                },
            }
        )    

    try:
        response = dynamo_client.transact_write_items(
            TransactItems=items
        )
        logger.info(response)
        return True

    except Exception as e:
        logger.error(str(e))
        return False
  
@xray_recorder.capture('SaveDdb')  
def UpdateStat(status, value):
    try:
        logger.info("update")
        response = dynamo_client.transact_write_items(
            TransactItems=[
                {
                    'Update': {
                        'Key': { 
                            'id': { 'S': str(status)},
                            'dt': { 'S': str(year_week)}
                        },
                        'UpdateExpression': 'set total_count = total_count + :val',
                        'ExpressionAttributeValues': {':val': { "N": value },
                        },
                        'TableName': DdbStatsTable
                    }
                },
                {
                    'Update': {
                        'Key': { 
                            'id': { 'S': str(status)},
                            'dt': { 'S': str(year_month)}
                        },
                        'UpdateExpression': 'SET total_count = total_count + :val',
                        'ExpressionAttributeValues': {':val': { "N": value },
                        },
                        'TableName': DdbStatsTable
                    }
                },
            ]
        )
        logger.info(response)
        return True

    except Exception as e:
        logger.error(str(e))
        return False

    return True

def handler(event, context):
    try: 
        xray_recorder.begin_subsegment('handler')
        xray_recorder.current_subsegment().put_annotation('Lambda', context.function_name)
        today = datetime.utcnow()
        if today.day == 1: 
            InitializeStat(year_month)
        if today.weekday() == 0:
            InitializeStat(year_week)        
        
        r = requests.get(event["image_url"], allow_redirects=True)

        attributes=[]
        attributes.append("DEFAULT")
        attributes.append("ALL")

        
        mod_response = rek.detect_moderation_labels(
            Image={
                'Bytes': r.content
            },
            MinConfidence=50
        )

        if len(mod_response["ModerationLabels"]) != 0:
            logger.warning("MODERATED " + str(mod_response))
            xray_recorder.current_subsegment().put_annotation('Moderation', mod_response)
            UpdateStat("moderated", "1")        
            return {'result': 'Fail', 'msg': 'Image Moderated', 'labels':mod_response["ModerationLabels"] }

        rek_response = rek.index_faces(
            Image={"Bytes": r.content},
            CollectionId=CollectionId,
            DetectionAttributes=attributes
        )
      
        if 'FaceRecords' in rek_response:
            logger.info('Calling selfie_processfaces')
            hdata = {}
            hdata['image_url'] = str(event["image_url"])
            hdata['facerecords'] = rek_response["FaceRecords"]
            hdata['collectionname'] = CollectionId
            hdata['guidstr'] = event["guidstr"]

            faces_count = len(rek_response["FaceRecords"])
            UpdateStat("success", str(faces_count))
            return {'result': 'Succeed', 'count': str(faces_count), 'data': json.dumps(hdata)}
            
        else:
            logger.error('Unable to rekognize face')
            xray_recorder.end_subsegment()
            UpdateStat("error", "1")
            return {'result': 'Fail', 'msg': 'Unable to rekognize face'}

    except Exception as e:
        logger.error(str(e))
        xray_recorder.end_subsegment()
        # Reckoginition Collection
        Initialize()
        return {'result': 'Fail', 'msg': str(e)}

    finally:
        xray_recorder.end_subsegment()