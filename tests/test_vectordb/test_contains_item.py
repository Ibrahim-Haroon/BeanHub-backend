import json
import pytest
from mock import MagicMock
from io import StringIO
import csv
from src.vector_db.contain_item import contains_quantity


@pytest.fixture
def mock_components(
        mocker
) -> dict:
    mock_db_instance = mocker.patch('src.vector_db.contain_item.psycopg2.connect')
    mock_db_instance.return_value.cursor.return_value.fetchall.return_value = [(7, 'test', 6, 'test', '(60,120)', 10.0)]
    key = "foo-key"

    return {
        'openai_embedding_api': mocker.patch('src.vector_db.contain_item.openai_embedding_api'),
        'connection_string': mocker.patch('src.vector_db.aws_database_auth.connection_string'),
        'api_key': mocker.patch('os.environ', dict({
            'OPENAI_API_KEY': key
        })),
    }


@pytest.fixture()
def mock_boto3_session_client(
        mocker
) -> MagicMock:
    return mocker.patch('boto3.session.Session.client', return_value=MagicMock())


def as_csv_file(
        data: [[str]]
) -> StringIO:
    file_object = StringIO()
    writer = csv.writer(file_object)
    writer.writerows(data)
    file_object.seek(0)

    return file_object


def test_contains_quantity_returns_true_when_given_quantity_less_than_stock(
        mocker, mock_boto3_session_client, mock_components
) -> None:
    # Arrange
    data = "test"
    expected_res = '[true, 6]'
    database_info = [
        ["dbname", "user", "password", "host", "port"],
        ["mydb", "myuser", "mypassword", "localhost", "port"]]
    aws_info = [
        ["secret_name", "region_name", "aws_access_key_id", "aws_secret_access_key"],
        ["name", "us-east-1", "aws_access_key_id", "aws_secret_access_key"]]

    # Act
    res = contains_quantity(data, aws_csv_file=as_csv_file(aws_info), database_csv_file=as_csv_file(database_info))

    # Assert
    assert res == expected_res, f"expected search to return {expected_res} but got {res}"


def test_contains_quantity_returns_false_when_given_quantity_greater_than_stock(
        mocker, mock_boto3_session_client, mock_components
) -> None:
    # Arrange
    data = "test"
    quantity = 1_000
    expected_res = '[false, 6]'
    database_info = [
        ["dbname", "user", "password", "host", "port"],
        ["mydb", "myuser", "mypassword", "localhost", "port"]]
    aws_info = [
        ["secret_name", "region_name", "aws_access_key_id", "aws_secret_access_key"],
        ["name", "us-east-1", "aws_access_key_id", "aws_secret_access_key"]]

    aws = as_csv_file(aws_info)
    db = as_csv_file(database_info)

    # Act
    res = contains_quantity(data, key="foo_key", quantity=quantity, aws_csv_file=aws, database_csv_file=db)

    # Assert
    assert res == expected_res, f"expected search to return {expected_res} but got {res}"


def test_get_item_returns_false_when_given_invalid_params(
        mocker, mock_boto3_session_client, mock_components
) -> None:
    # Arrange
    expected_res = 'false'
    data = None

    # Act
    res = contains_quantity(data)

    # Assert
    assert res == expected_res, f"expected {expected_res} but got {res}"
