import json
import logging

import boto3
from botocore.exceptions import ClientError

logging.basicConfig(level=logging.INFO)

class DynamoDB:
    def __init__(self, 
                 dynamo_db: boto3.resource):
        # Initialize the DynamoDB client
        self.dynamo_db = dynamo_db
        self.table = self.dynamo_db.Table('projects')
        logging.info("DynamoDB created")

    def get_projects(self, user_id):
        try:
            # Query the table for items with the specified user_id
            response = self.table.query(
                KeyConditionExpression=boto3.dynamodb.conditions.Key('user_id').eq(user_id)
            )
            # Check if items were found
            if 'Items' in response and response['Items']:
                logging.info(f"Projects found for user_id {user_id}: {response['Items']}")
                return response['Items']
            else:
                logging.info(f"No projects found for user_id {user_id}")
                return []
        except ClientError as e:
            logging.error(f"An error occurred: {e.response['Error']['Message']}")
            return []