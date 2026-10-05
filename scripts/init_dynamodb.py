import os
import time

import boto3
from botocore.exceptions import BotoCoreError, ClientError


region = os.getenv("DDB_AWS_REGION", "us-east-1")
table_name = os.getenv("DDB_TABLE_NAME", "votingapp-restaurants")
endpoint_url = os.getenv("DDB_ENDPOINT_URL")
client = boto3.client(
    "dynamodb",
    region_name=region,
    endpoint_url=endpoint_url,
)

deadline = time.monotonic() + 120
while True:
    try:
        try:
            client.describe_table(TableName=table_name)
        except ClientError as error:
            if error.response["Error"]["Code"] != "ResourceNotFoundException":
                raise
            try:
                client.create_table(
                    TableName=table_name,
                    AttributeDefinitions=[
                        {"AttributeName": "name", "AttributeType": "S"}
                    ],
                    KeySchema=[
                        {"AttributeName": "name", "KeyType": "HASH"}
                    ],
                    BillingMode="PAY_PER_REQUEST",
                )
            except ClientError as create_error:
                if create_error.response["Error"]["Code"] != "ResourceInUseException":
                    raise

        client.get_waiter("table_exists").wait(
            TableName=table_name,
            WaiterConfig={"Delay": 1, "MaxAttempts": 30},
        )
        break
    except (BotoCoreError, ClientError) as error:
        if time.monotonic() >= deadline:
            raise RuntimeError(
                f"Could not initialize DynamoDB table {table_name!r}"
            ) from error
        print(f"Waiting for DynamoDB at {endpoint_url or 'the configured endpoint'}: {error}")
        time.sleep(2)

table = boto3.resource(
    "dynamodb",
    region_name=region,
    endpoint_url=endpoint_url,
).Table(table_name)

for restaurant in ("outback", "bucadibeppo", "ihop", "chipotle"):
    table.update_item(
        Key={"name": restaurant},
        UpdateExpression="SET restaurantcount = if_not_exists(restaurantcount, :zero)",
        ExpressionAttributeValues={":zero": 0},
    )

print(f"DynamoDB table {table_name!r} is ready.")
