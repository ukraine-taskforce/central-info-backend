#!/usr/bin/env python
# -*- coding: utf-8 -*-

import boto3
import csv
import io

def lambda_handler():
    s3 = boto3.resource('s3')
    dynamoDB = boto3.resource('dynamodb', region_name='eu-central-1')
    table = dynamoDB.Table('sos-info')
    s3_bucket_name  = 's9-prod-eu-central-1-lambda-states'
    s3_object_key   = 'dataset.csv'

    response = s3.Object(s3_bucket_name, s3_object_key).get()['Body'].read().decode('ascii')
    csvReader = csv.DictReader(io.StringIO(response))

    with table.batch_writer(overwrite_by_pkeys=['ID']) as batch:
        for row in csvReader:
            if row['ID'] == '':
                continue

            if row['ID'] == 'ID' or row['Hyperlink'] == '':
                batch.delete_item(Key={ 'ID': row['ID'] })
                continue

            del row['']

            batch.put_item(Item=row)

if __name__ == "__main__":
    lambda_handler()
