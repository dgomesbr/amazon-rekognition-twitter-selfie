import json
import urllib
import boto3
import logging
import base64
import uuid
import time
import os
import requests
from datetime import datetime, timedelta
from PIL import Image
from io import BytesIO
from aws_xray_sdk.core import xray_recorder
from aws_xray_sdk.core import patch_all

patch_all()

S3Bucket = os.getenv('TBucket')
CollectionId = os.getenv('CollectionId')

logger = logging.getLogger()
logger.setLevel(logging.INFO)

s3 = boto3.client('s3')
rek = boto3.client('rekognition')

def handler(event, context):
    try:
        xray_recorder.begin_subsegment('handler')
        xray_recorder.current_subsegment().put_annotation('Lambda', context.function_name)
        faces_count = 0
        faces = []
        fdata = {}
        event_data = json.loads(event["data"])
        identified_faces = event_data["facerecords"]
        fdata["first_name"] = 'NULL'
        fdata["last_name"] = 'NULL'

        for face in identified_faces:          
            if (int(face["FaceDetail"]["Confidence"])) < 80:
                continue

            url = 'https://randomuser.me/api/?gender=' + str(face["FaceDetail"]["Gender"]["Value"]).lower() + '&nat=ca&inc=name,nat' 
            ret = requests.get(url) 
            if ret.status_code == 200:  
                j_ret = ret.json()
                fdata["first_name"] = j_ret["results"][0]["name"]["first"]  
                fdata["last_name"] = j_ret["results"][0]["name"]["last"]  
            
            fdata["image_url"] = event_data["image_url"]
            fdata["guidstr"] = event_data["guidstr"]
            fdata["gender"] = face["FaceDetail"]["Gender"]
            fdata["face_id"] = face["Face"]["FaceId"] 
            fdata["emotions"] = face["FaceDetail"]["Emotions"]            
            fdata["agerange"] = face["FaceDetail"]["AgeRange"]

            # calculate the bounding boxes the detected face 
            r = requests.get(event_data["image_url"], allow_redirects=True)
            stream = BytesIO(r.content)
            image = Image.open(stream)
            imgWidth, imgHeight = image.size 
            box = face["FaceDetail"]["BoundingBox"]
            left = imgWidth * box['Left']
            top = imgHeight * box['Top']
            width = imgWidth * box['Width']
            height = imgHeight * box['Height']

            fdata["bbox_left"] = left
            fdata["bbox_top"] = top
            fdata["bbox_width"] = width
            fdata["bbox_height"] = height 
            fdata["imgWidth"] = imgWidth 
            fdata["imgHeight"] = imgHeight
            fdata["updated_at"] = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S")

            faces_count = faces_count + 1
            faces.append(face["Face"]["FaceId"])

            if imgWidth < 500:
                logger.warning("Image width not greater than 500px. Not processing.")
                continue

            if len(event_data) > 2:
                file_name = str(face["Face"]["FaceId"]) + '.json'
                key = "selfie-reports/" + file_name  
                logger.info(fdata)
                s3.put_object(
                    ACL='private',
                    Body=json.dumps(fdata),
                    Bucket=S3Bucket,          
                    Key=key
                )             
        if (len(faces) > 0):
            response = rek.delete_faces(
                CollectionId=CollectionId,
                FaceIds=faces
            )
        
        logger.info(str(faces_count) + " faces")
        xray_recorder.end_subsegment()
        return {'result': 'Succeed', 'count': str(faces_count) }

    except Exception as e:
        logger.error(str(e))
        xray_recorder.end_subsegment()
        return {'result': 'Fail', 'msg': str(e) }

    finally:
        xray_recorder.end_subsegment()