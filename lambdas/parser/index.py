import os
import re
import json
import sys
import boto3
import uuid
import logging
from datetime import datetime, timedelta
from botocore.exceptions import ClientError
from boto3.dynamodb.conditions import Key, Attr
from aws_xray_sdk.core import xray_recorder
from aws_xray_sdk.core import patch

patch(['boto3'])

xray_recorder.configure(service='twitterSelfie')

DdbImageTable = os.getenv('DdbImageTable')
StateMachineArn = os.getenv('StateMachineArn')

rek = boto3.client('rekognition')
dynamodb = boto3.resource("dynamodb")
dyn_table = dynamodb.Table(DdbImageTable)

logger = logging.getLogger()
logger.setLevel(logging.INFO)

@xray_recorder.capture('GetDynamo')
def GetImage(url):
    try:
        response = dyn_table.query(
        KeyConditionExpression=Key('img_url').eq(str(url))
        )
        return response

    except ClientError as e:
        logger.error(e.response['Error']['Message'])
        return {'Items': [], 'Count': 0}

@xray_recorder.capture('AddDynamo')            
def AddImage(url,filename):
    try:
        epoch = datetime.utcfromtimestamp(0)
        epochexp = (datetime.now()+timedelta(days=15) - epoch).total_seconds() * 1000.0
        response = dyn_table.put_item(
        Item={
            'img_url': str(url),
            'filename': filename,
            'expire_at': int(epochexp)
            }
        )
        return response

    except ClientError as e:
        logger.error(e.response['Error']['Message'])
    return {'Items': [], 'Count': 0}

@xray_recorder.capture('StepFunction')
def CallStepFunction(img):
    hdata = {}
    guid_str = str(uuid.uuid4().hex)
    xray_recorder.current_subsegment().put_annotation('image_url', img)  
    hdata["image_url"] = img
    hdata['guidstr'] = guid_str
    client = boto3.client('stepfunctions') 
    response = client.start_execution(
        stateMachineArn=StateMachineArn,
        name=guid_str,
        input=json.dumps(hdata)
    )
    AddImage(img,guid_str+".csv")
    logger.info(json.dumps(hdata))    

def handler(event, context):
    logger.info(str(len(event)) + " records")
    for rec in event:
        a = json.dumps(rec)
        pos1 = a.find("media_url_https")
        if (pos1 != -1):
          pos2 = a.find(".jpg", pos1)
          if (pos2 != -1):
              if len(a[pos1+19:pos1+4+(pos2-pos1)]) > 4:
                  img_url = str(a[pos1+19:pos1+4+(pos2-pos1)])
                  dyn_resp = GetImage(img_url)
                  if dyn_resp["Count"] == 0:
                      logger.info("Executing StepFunctions for: " + img_url)
                      CallStepFunction(img_url)
                  else:
                      logger.info("skipped")
                    
    return True