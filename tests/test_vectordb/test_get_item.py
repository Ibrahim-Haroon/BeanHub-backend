import pytest
from mock import patch, MagicMock
from io import StringIO
import csv
from src.vector_db.get_item import get_item


@pytest.fixture
def mock_components(mocker):
    mock_db_instance = mocker.patch('src.vector_db.get_item.psycopg2.connect')
    mock_db_instance.return_value.cursor.return_value.fetchall.return_value = [(7, 'test', 6, 'test', '(60,120)', 10.0)]

    return {
        'openai_embedding_api': mocker.patch('src.vector_db.get_item.openai_embedding_api'),
        'connection_string': mocker.patch('src.vector_db.aws_database_auth.connection_string'),
    }


@pytest.fixture()
def mock_boto3_session_client(mocker):
    return mocker.patch('boto3.session.Session.client', return_value=MagicMock())


def as_csv_file(data: [[str]]) -> StringIO:
    file_object = StringIO()
    writer = csv.writer(file_object)
    writer.writerows(data)
    file_object.seek(0)

    return file_object


def test_get_item_returns_true_when_successfully_found_closest_item(mocker, mock_boto3_session_client, mock_components):
    # Arrange
    data = "test"
    key = "mock_api_key"
    database_info = [
        ["dbname", "user", "password", "host", "port"],
        ["mydb", "myuser", "mypassword", "localhost", "port"]]
    aws_info = [
        ["secret_name", "region_name", "aws_access_key_id", "aws_secret_access_key"],
        ["name", "us-east-1", "aws_access_key_id", "aws_secret_access_key"]]

    db = as_csv_file(database_info)

    # Act
    _, res = get_item(data, api_key=key, database_csv_file=db)

    # Assert
    assert res is True, f"expected search to be successful but {res}"

#### Temporarily not needed. ###
# def test_get_item_returns_false_when_given_quantity_greater_than_stock(mocker, mock_boto3_session_client, mock_components):
#     # Arrange
#     data = "test"
#     quantity = 1_000
#     key = "mock_api_key"
#     database_info = [
#         ["dbname", "user", "password", "host", "port"],
#         ["mydb", "myuser", "mypassword", "localhost", "port"]]
#     aws_info = [
#         ["secret_name", "region_name", "aws_access_key_id", "aws_secret_access_key"],
#         ["name", "us-east-1", "aws_access_key_id", "aws_secret_access_key"]]
#
#     aws = as_csv_file(aws_info)
#     db = as_csv_file(database_info)
#
#     # Act
#     _, res = get_item(data, key=key, aws_csv_file=aws, database_csv_file=db)
#
#     # Assert
#     assert res is False, f"expected search not to return most similar item but {res}"


def test_get_item_returns_false_when_given_invalid_params(mocker, mock_boto3_session_client, mock_components):
    # Arrange
    data = None

    # Act
    _, res = get_item(data)

    # Assert
    assert res is False, f"expected search to be unsuccessful but {res}"
