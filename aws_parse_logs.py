import botocore
import boto3
import datetime
import json
import jsons
import os
import gzip

from io import BytesIO
from aws_log_parser import log_parser, LogType
from requests_aws4auth import AWS4Auth
from elasticsearch import Elasticsearch, RequestsHttpConnection

## Global
today = datetime.datetime.now()

logtype = os.environ['logtype'] # Provide logtype parse log
endpoint = os.environ['endpoint'] # Provide the elasticsearch endpoint
region = os.environ['region'] # Provide the region
index_name = os.environ['logindex'] + today.strftime("%Y.%m.%d") # Name of the index to create it

service = 'es'
credentials = boto3.Session().get_credentials()
awsauthes = AWS4Auth(credentials.access_key, credentials.secret_key, region, service, session_token=credentials.token)

# To serializate datetime in json format
def jsonserial_date(obj):
    if isinstance(obj, datetime.datetime):
        return obj.__str__()

# Main function
def main(event, context):
    try: 
        # Build session S3
        s3 = boto3.client('s3')
    
        # Build the connection to Elasticsearch
        es = Elasticsearch (
            hosts=[{'host': endpoint, 'port': 443}],
            http_auth=awsauthes,
            use_ssl=True,
            verify_certs=True,
            connection_class=RequestsHttpConnection
        )

        for record in event['Records']:

            # Save the bucket name and key from the event
            bucket = record['s3']['bucket']['name']
            keyfile = record['s3']['object']['key']
            print("Bucket: " + bucket + " Key: " + keyfile)

            # Get the new object
            obj = s3.get_object(Bucket=bucket, Key=keyfile)
            print("Object: " + json.dumps(obj, default=jsonserial_date))
                
            # Open de gzip file
            file = gzip.open(BytesIO(obj['Body'].read()))
        
            # Read the content
            content = file.read().decode('utf-8')            
            lines = content.splitlines()
            
            # Count the number of lines that not starts with comment in the file
            total_lines = 0
            for number_line in lines:
                if not number_line.startswith('#'):
                    total_lines += 1
            
            # Check the correct logtype
            if logtype == 'LoadBalancer':
                generator_line = log_parser(lines, LogType.LoadBalancer)
            elif logtype == 'CloudFront':
                generator_line = log_parser(lines, LogType.CloudFront)
            else:
                print("ERROR. The logtype is not correct. Please insert a correct logtype.")     
                exit()
            
            # Count total lines
            total_lines_es = 0
            
            # Parse each line and loop it
            for line in generator_line:
                
                # If not exists a field with name timestamp, create it. Necessary for Kibana to filter with date and time correctly
                if not "timestamp" in line.__dict__:
                    date = datetime.date.fromisoformat(str(line.__dict__['date']))
                    time = datetime.time.fromisoformat(str(line.__dict__['time']))
            
                    line.__dict__['timestamp'] = datetime.datetime.combine(date, time, tzinfo=datetime.timezone.utc)
                
                # Import it in ElasticSearch and count lines that has been imported in ElasticSearch
                es_import = es.index(index=index_name, body=jsons.dumps(line.__dict__, default=jsonserial_date))
                
                if es_import['result'] == 'created':
                    total_lines_es += 1
                else:
                    print("ERROR. This line has not been imported: " + jsons.dumps(line.__dict__, default=jsonserial_date))
            
            # Check if every lines has been imported into ElasticSearch
            if total_lines == total_lines_es:
                print("SUCCESS. Every lines has been imported correctly into ElasticSearch. Number of total imported lines: " + str(total_lines_es) + "/" + str(total_lines))
            else:
                print("ERROR. Some lines has not been imported correctly. Number of total imported lines: " + str(total_lines_es) + "/" + str(total_lines))
                
    except botocore.exceptions.ClientError as Error:
            print(Error)