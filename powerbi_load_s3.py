import boto3
import pandas as pd

bucket_name= 'dsci6007-youtube-fp'
folder_name= '/tmp/processed/2024-04-21/'
file_name = r'classified_data_latest.csv'  # or .json in your case
key=folder_name+file_name

s3 = boto3.resource(
    service_name='s3',
    region_name='us-east-1',  ## ex: 'us-east-2'
    aws_access_key_id='',
    aws_secret_access_key='',
    aws_session_token=''

)

obj = s3.Bucket(bucket_name).Object(key).get()
df = pd.read_csv(obj['Body'])

# Open PowerBI as Administrator to avoid any issues"
