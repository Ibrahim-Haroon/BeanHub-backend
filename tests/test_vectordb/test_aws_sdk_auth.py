import os
import pytest
from os import path
import pandas as pd
from botocore.exceptions import ClientError
from src.vector_db.aws_sdk_auth import get_secret
from mock import mock_open, mock, patch, MagicMock


@pytest.fixture
def mock_pandas_read_csv(mocker):
    secret_file_path = path.join(path.dirname(path.realpath(__file__)), "../..", "other", "aws-info.csv")
    read_data = 'secret_name,region_name,aws_access_key_id,aws_secret_access_key\ntest_secret,us-east-1,test_access_key,test_secret_key\n'
    with patch('builtins.open', new_callable=mock_open, read_data=read_data):
        mocker.patch('pandas.read_csv', return_value=pd.DataFrame({
            'secret_name': ['test_secret'],
            'region_name': ['region_name'],
            'aws_access_key_id': ['aws_access_key_id'],
            'aws_secret_access_key': ['aws_secret_access_key']
        }))

        mocker.patch('os.path.join', return_value=secret_file_path)

        yield secret_file_path


@pytest.fixture
def mock_boto3_session_client(mocker):
    return mocker.patch('boto3.session.Session.client', return_value=mock.MagicMock())


def test_that_environment_variables_set_correctly(mocker):
    # Arrange
    expected_env_vars = {
        "SECRET_NAME": "test_secret_name",
        "AWS_DEFAULT_REGION": "test_aws_default_region",
        "AWS_ACCESS_KEY_ID": "test_access_key_id",
        "AWS_SECRET_ACCESS_KEY": "test_secret_access_key"
    }

    mocker.patch.dict(os.environ, {
        "SECRET_NAME": "test_secret_name",
        "AWS_DEFAULT_REGION": "test_aws_default_region",
        "AWS_ACCESS_KEY_ID": "test_access_key_id",
        "AWS_SECRET_ACCESS_KEY": "test_secret_access_key"
    })

    # Act & Assert
    for key, expected_value in expected_env_vars.items():
        assert os.environ.get(key) == expected_value, f"Env var {key} expected to be {expected_value} but got {os.environ.get(key)}"


def test_get_secret_returns_expected_secret_when_environment_variables_used(mocker, mock_pandas_read_csv, mock_boto3_session_client):
    # Arrange
    expected_result = MagicMock

    mocker.patch.dict(os.environ, {
        "SECRET_NAME": "secretsmanager",
        "AWS_DEFAULT_REGION": "region_name",
        "AWS_ACCESS_KEY_ID": "aws_access_key_id",
        "AWS_SECRET_ACCESS_KEY": "aws_secret_access_key"
    })

    # Act
    result = get_secret()

    # Assert
    mock_boto3_session_client.assert_called_once_with(
        service_name='secretsmanager',
        region_name='region_name',
        aws_access_key_id='aws_access_key_id',
        aws_secret_access_key='aws_secret_access_key'
    )
    assert isinstance(result, expected_result), f"expected boto3 session client to return secret but got {result}"



def test_get_secret_returns_expected_secret_when_csv_file_used(mocker, mock_pandas_read_csv, mock_boto3_session_client):
    # Arrange
    expected_result = MagicMock

    mocker.patch.dict(os.environ, {
        "SECRET_NAME": "",
        "AWS_DEFAULT_REGION": "",
        "AWS_ACCESS_KEY_ID": "",
        "AWS_SECRET_ACCESS_KEY": ""
    })

    # Act
    result = get_secret()

    # Assert
    mock_boto3_session_client.assert_called_once_with(
        service_name='secretsmanager',
        region_name='region_name',
        aws_access_key_id='aws_access_key_id',
        aws_secret_access_key='aws_secret_access_key'
    )
    assert isinstance(result, expected_result), f"expected boto3 session client to return secret but got {result}"


def test_get_secret_to_throw_exception_when_given_error(mock_pandas_read_csv, mock_boto3_session_client):
    # Arrange
    mock_client = mock_boto3_session_client.return_value
    mock_client.get_secret_value.side_effect = ClientError({'Error': {}}, 'operation_name')

    # Act and Assert
    with pytest.raises(ClientError):
        get_secret()

    assert f"expected exception to be thrown when given error but got None"


@patch('sys.stderr.write')
@patch('sys.exit')
def test_that_connection_string_exits_when_invalid_file_passed(mock_exit, mock_stderr_write):
    # Arrange
    invalid_file = "invalid_file"
    expected_error_message = f"Must either use default csv file path or pass in a csv file, got {type(invalid_file)}."

    # Act and Assert
    with pytest.raises(SystemExit) as e:
        _ = get_secret(invalid_file)

    assert str(e.value) == expected_error_message, f"expected system to exit with {expected_error_message} but got {str(e.value)}"