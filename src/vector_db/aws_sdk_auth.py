import boto3
import pandas as pd
from os import path
from io import StringIO
from os import getenv as env
from dotenv import load_dotenv
from botocore.exceptions import ClientError

load_dotenv()


def get_secret(
        csv_file: StringIO = None
) -> dict:
    """

    @purpose: SDK for AWS
    @rtype: dict
    @param csv_file: used for unit tests and if you want to pass in own AWS authentication
    @return: ex. {"username":"username","password":"pass","engine":"engine","host":"host","port":5432,"dbname":"name","dbInstanceIdentifier":"db-id"}
    """
    secret_file_path = path.join(path.dirname(path.realpath(__file__)), "../..", "other", "aws-info.csv")
    try:
        df = pd.read_csv(secret_file_path)
    except FileNotFoundError:
        df = pd.DataFrame()
        pass

    if (csv_file is None and
        env('AWS_ACCESS_KEY_ID') and
        env('AWS_SECRET_ACCESS_KEY') and
        env('AWS_DEFAULT_REGION') and
        env('SECRET_NAME')
    ):
        secret_name = env('SECRET_NAME')
        region_name = env('AWS_DEFAULT_REGION')
        aws_access_key_id = env('AWS_ACCESS_KEY_ID')
        aws_secret_access_key = env('AWS_SECRET_ACCESS_KEY')

    else:
        if csv_file is None and not df.empty:
            pass
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
