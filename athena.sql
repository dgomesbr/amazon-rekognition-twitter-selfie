CREATE EXTERNAL TABLE `selfie_reports`(
  `first_name` string COMMENT 'from deserializer', 
  `last_name` string COMMENT 'from deserializer', 
  `image_url` string COMMENT 'from deserializer', 
  `guidstr` string COMMENT 'from deserializer', 
  `gender` struct<value:string,confidence:double> COMMENT 'from deserializer', 
  `face_id` string COMMENT 'from deserializer', 
  `emotions` array<struct<type:string,confidence:double>> COMMENT 'from deserializer', 
  `bbox_left` double COMMENT 'from deserializer', 
  `bbox_top` double COMMENT 'from deserializer', 
  `bbox_width` double COMMENT 'from deserializer', 
  `bbox_height` double COMMENT 'from deserializer', 
  `imgWidth` int COMMENT 'from deserializer', 
  `imgHeight` int COMMENT 'from deserializer', 
  `updated_at` string COMMENT 'from deserializer', 
  `agerange` struct<low:int,high:int> COMMENT 'from deserializer')
ROW FORMAT SERDE 
  'org.openx.data.jsonserde.JsonSerDe' 
WITH SERDEPROPERTIES ( 
  'paths'='agerange,box,emotions,face_id,first_name,gender,guidstr,image_url,last_name') 
STORED AS INPUTFORMAT 
  'org.apache.hadoop.mapred.TextInputFormat' 
OUTPUTFORMAT 
  'org.apache.hadoop.hive.ql.io.HiveIgnoreKeyTextOutputFormat'
LOCATION
  's3://<app-bucket>/selfie-reports/'
TBLPROPERTIES (
  'CrawlerSchemaDeserializerVersion'='1.0', 
  'CrawlerSchemaSerializerVersion'='1.0', 
  'UPDATED_BY_CRAWLER'='twitterApp', 
  'averageRecordSize'='877', 
  'classification'='json', 
  'compressionType'='none', 
  'objectCount'='25', 
  'recordCount'='25', 
  'sizeKey'='22079', 
  'typeOfData'='file')
