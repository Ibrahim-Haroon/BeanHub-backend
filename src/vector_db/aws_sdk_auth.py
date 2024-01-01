import boto3
import pandas as pd
from os import path
from botocore.exceptions import ClientError
from io import StringIO


def get_secret(csv_file: StringIO = None) -> dict:
    """

    @purpose: validate Amazon SDK
    @rtype: dict
    @param csv_file: can be passed if you want to pass in own AWS authentication and is used for unit tests
    @return: ex. {"username":"username","password":"pass","engine":"engine","host":"host","port":5432,"dbname":"name","dbInstanceIdentifier":"db-id"}
    """

    if csv_file is None:
        secret_file_path = path.join(path.dirname(path.realpath(__file__)), "../..", "other", "aws-info.csv")
        df = pd.read_csv(secret_file_path)
    elif isinstance(csv_file, StringIO):
        df = pd.read_csv(csv_file)
    else:
        raise SystemExit(f"Must either use default csv file path or pass in a csv file, got {type(csv_file)}.")

    row = df.iloc[0]

    secret_name = row['secret_name']
    region_name = row['region_name']
    aws_access_key_id = row['aws_access_key_id']
    aws_secret_access_key = row['aws_secret_access_key']

    session = boto3.session.Session()
    client = session.client(
        service_name='secretsmanager',
        region_name=region_name,
        aws_access_key_id=aws_access_key_id,
        aws_secret_access_key=aws_secret_access_key
    )

    try:
        get_secret_value_response = client.get_secret_value(
            SecretId=secret_name
        )
    except ClientError as e:
        raise e

    return get_secret_value_response['SecretString']


if __name__ == "__main__":
    get_secret()