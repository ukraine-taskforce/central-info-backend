import os
import boto3


def get_bot_token():
    session = boto3.session.Session()
    client = session.client(service_name='secretsmanager')
    response = client.get_secret_value(SecretId=os.environ['token_parameter'])
    return response['SecretString']
