import boto3
import json
import csv
from io import StringIO
import os
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from datetime import datetime


def lambda_handler(event, context):
    nltk.data.path.append("/tmp")
    nltk.download('punkt', download_dir="/tmp")
    nltk.download('stopwords', download_dir="/tmp")

    s3_client = boto3.client('s3')
    # Create a corpus of preprocessed text descriptions and class labels
    text_descriptions = [
        "This video is a gameplay walkthrough of the new action RPG game, showing all the quests and boss battles.",
        "Watch me vlog my daily life as a college student, sharing my experiences, struggles, and adventures.",
        "An in-depth review of the latest smartphone, covering its design, performance, camera quality, and overall value for money.",
        "A step-by-step tutorial on how to bake the perfect chocolate cake, with easy-to-follow instructions and tips.",
        "Learn about the history of ancient civilizations through this engaging documentary series.",
        "Get ready to laugh out loud with this hilarious stand-up comedy special featuring the funniest jokes and sketches.",
        "The official music video for the latest hit single by your favorite pop star, featuring stunning visuals and choreography.",
        "Join me on a breathtaking journey through the stunning landscapes and rich cultures of Italy.",
        "Watch as these daring YouTubers attempt to complete extreme challenges and stunts that will leave you on the edge of your seat.",
        "Unboxing and reviewing the latest tech gadget, revealing all its features, accessories, and first impressions."
    ]

    class_labels = [
        "Gaming videos",
        "Vlogs",
        "Product reviews",
        "Educational videos",
        "Comedy videos",
        "Music videos",
        "Travel videos",
        "Challenge videos",
        "Unboxing videos"
    ]

    def preprocess_text(text):
        stop_words = set(stopwords.words('english'))
        text = text.lower()
        tokens = word_tokenize(text)
        filtered_tokens = [token for token in tokens if token not in stop_words]
        return ' '.join(filtered_tokens)

    corpus = [preprocess_text(text) for text in class_labels]
    #corpus.extend(class_labels)

    # Vectorize the corpus using TF-IDF
    vectorizer = TfidfVectorizer()
    X = vectorizer.fit_transform(corpus)

    def classify_text(text):
        text_vector = vectorizer.transform([preprocess_text(text)])
        similarities = cosine_similarity(text_vector, X).flatten()
        most_similar_index = similarities.argsort()[-1]
        return corpus[most_similar_index]



    bucket = event['Records'][0]['s3']['bucket']['name']
    key = event['Records'][0]['s3']['object']['key']

    response = s3_client.get_object(Bucket=bucket, Key=key)
    data = json.loads(response['Body'].read())

    classified_data = []

    for item in data:
        title = item['title']
        description = item['description']
        video_id = item['video_id']

        # Classify title and description
        #classified_title = classify_text(title)
        #classified_description = classify_text(description)
        classified_class = classify_text(title + " " +description)

        # Append classified results to the datapoint
        #item['classified_title'] = classified_title
        #item['classified_description'] = classified_description
        item['classified_class'] = classified_class

        classified_data.append(item)

    # Save the updated data to S3
    current_date = datetime.now().strftime("%Y-%m-%d")
    current_time = datetime.now().strftime("%H-%M-%S")
    file_name = f"/tmp/processed/{current_date}/classified_data_{current_time}.json"
    latest_file_name = f"/tmp/processed/{current_date}/classified_data_latest.json"

    s3_client.put_object(Bucket=bucket, Key=file_name, Body=json.dumps(classified_data))
    s3_client.put_object(Bucket=bucket, Key=latest_file_name, Body=json.dumps(classified_data))

    def json_to_csv(json_data, selected_keys):
        csv_buffer = StringIO()
        writer = csv.DictWriter(csv_buffer, fieldnames=selected_keys)
        writer.writeheader()
        for item in json_data:
            row = {key: item.get(key, '') for key in selected_keys}
            writer.writerow(row)
        return csv_buffer.getvalue()

    # Define the selected keys
    selected_keys = ['video_id', 'title', 'classified_class', 'published_at', 'views', 'likes', 'comments']

    csv_data = json_to_csv(classified_data, selected_keys)
    latest_csv_file_name = f"/tmp/processed/{current_date}/classified_data_latest.csv"
    s3_client.put_object(Body=csv_data, Bucket=bucket, Key=latest_csv_file_name)

    return {
        'statusCode': 200,
        'body': json.dumps('Classification and saving completed!')
    }

