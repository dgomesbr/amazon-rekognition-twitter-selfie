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

AthQueryLambdaName = os.getenv('AthQueryLambdaName')

logger = logging.getLogger()
logger.setLevel(logging.INFO)


print('Loading function')

client = boto3.client('lambda')

payload = {}

def handler(event, context):
    try:
        xray_recorder.begin_subsegment('handler')
        xray_recorder.current_subsegment().put_annotation('Lambda', context.function_name)
        rekEmotions = ["HAPPY","SAD","ANGRY","CONFUSED","DISGUSTED","SURPRISED","CALM","FEAR"]
        for emotion in rekEmotions:
            query_str = """
            with selfie_emotions as (
              select face_id, image_url, first_name, last_name, (agerange.low + agerange.high)/2 as age, 
                gender.value as gender_value, emotion.type as etype, 
                round(emotion.confidence,3) as confidence,
                bbox_left, bbox_top, bbox_width, bbox_height,
                imgWidth, imgHeight, updated_at
              from default.selfie_reports TABLESAMPLE BERNOULLI (50)
              cross JOIN UNNEST(emotions) as t(emotion)
              where emotion.type = '%s'
              order by confidence desc
              LIMIT 1
            )
            select * from selfie_emotions           
            """ % (emotion)

            payload["type"] = emotion
            payload["query"] = query_str

            response = client.invoke(
                FunctionName=AthQueryLambdaName,
                InvocationType='Event',
                Payload=json.dumps(payload)
            )

            logger.info(response)

        return {'result': True }

    except Exception as e:
        logger.error('Something went wrong: ' + str(e))
        return {'result': False, 'msg': str(e)}