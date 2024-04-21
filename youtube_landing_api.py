import json
import os
import boto3
from googleapiclient.discovery import build
from datetime import datetime

# Set up AWS resources
s3 = boto3.resource('s3')
bucket_name = "dsci6007-youtube-fp"

# Set up YouTube API credentials
api_key = ""
youtube = build('youtube', 'v3', developerKey=api_key)

def lambda_handler(event, context):
    # Get current date
    current_date = datetime.now().strftime('%Y-%m-%d')
    max_results=2000
    # Set start and end time for the current date
    start_time = f"{current_date}T00:00:00Z"
    end_time = f"{current_date}T23:59:59Z"
    
    next_page_token = None
    videos = []
    
    while True:
        # Extract data from YouTube API for videos published on the current date
        search_response = youtube.search().list(
            q='keyword',
            type='video',
            part='id,snippet',
            maxResults=max_results,
            pageToken=next_page_token,
            publishedAfter=start_time,
            publishedBefore=end_time
        ).execute()
        
        for search_result in search_response.get('items', []):
            if search_result['id']['kind'] == 'youtube#video':
                video_id = search_result['id']['videoId']
                video_response = youtube.videos().list(
                    id=video_id,
                    part='snippet,statistics,recordingDetails'
                ).execute()
                
                if video_response.get('items'):
                    snippet = video_response['items'][0]['snippet']
                    statistics = video_response['items'][0]['statistics']
                    recording_details = video_response['items'][0].get('recordingDetails', {})
                    region = recording_details.get('region', '') if 'region' in recording_details else ''
                    
                    video_data = {
                        'video_id': video_id,
                        'title': snippet.get('title', ''),
                        'description': snippet.get('description', ''),
                        'published_at': snippet.get('publishedAt', ''),
                        'views': statistics.get('viewCount', ''),
                        'likes': statistics.get('likeCount', ''),
                        'comments': statistics.get('commentCount', '')
                    }
                    videos.append(video_data)
                
        next_page_token = search_response.get('nextPageToken')
        
        if not next_page_token:
            break

    # Get current date and time
    current_datetime = datetime.now()
    current_date = current_datetime.strftime('%Y-%m-%d')
    current_time = current_datetime.strftime('%H-%M-%S')

    # Create folder if it doesn't exist
    folder_path = f"/tmp/landing/{current_date}"
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)

    # Save data into files
    filename_with_time = f"youtube_data_{current_time}.json"
    filename_latest = "youtube_data_latest.json"

    with open(os.path.join(folder_path, filename_with_time), 'w') as f:
        json.dump(videos, f)

    with open(os.path.join(folder_path, filename_latest), 'w') as f:
        json.dump(videos, f)

    # Upload files to S3 
    s3_object_with_time = s3.Object(bucket_name, f"{folder_path}/{filename_with_time}")
    s3_object_with_time.upload_file(os.path.join(folder_path, filename_with_time))

    s3_object_latest = s3.Object(bucket_name, f"{folder_path}/{filename_latest}")
    s3_object_latest.upload_file(os.path.join(folder_path, filename_latest))

    return {
        'statusCode': 200,
        'body': json.dumps('ETL process completed successfully!')
    }

