import csv
import json
import queue
import pytest
from io import StringIO
from mock import MagicMock
from src.vector_db.get_item import get_item


@pytest.fixture
def mock_components(
        mocker
) -> dict:
    mock_db_instance = mocker.patch('src.vector_db.get_item.psycopg2.connect')
    mock_db_instance.return_value.cursor.return_value.fetchall.return_value = [(7, 'test', 6, 'test', '(60,120)', 10.0)]

    mock_embedding_api = mocker.patch('src.vector_db.get_item.openai_embedding_api')
    mock_embedding_api.return_value = [0.1, 0.2, 0.3]

    return {
        'openai_embedding_api': mock_embedding_api,
        'connection_string': mocker.patch('src.vector_db.aws_database_auth.connection_string'),
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


def test_get_item_returns_true_when_successfully_found_closest_item_and_adds_to_cache(
        mocker, mock_boto3_session_client, mock_components
) -> None:
    # Arrange
    mock_redis = mocker.Mock()
    mock_redis.set = MagicMock()
    mock_redis.exists = MagicMock(return_value=False)
    database_info = [
        ["dbname", "user", "password", "host", "port"],
        ["mydb", "myuser", "mypassword", "localhost", "port"]]
    db = as_csv_file(database_info)

    # Act
    _, res = get_item(order="test", api_key="test_key", embedding_cache=mock_redis, database_csv_file=db)

    # Assert
    assert res is True, f"expected search to be successful but {res}"


def test_get_item_returns_true_when_successfully_found_closest_item_and_cache_hit(
        mocker, mock_boto3_session_client, mock_components
) -> None:
    # Arrange
    mock_redis = mocker.Mock()
    mock_redis.set = MagicMock()
    mock_redis.exists = MagicMock(return_value=True)
    mock_redis.get = MagicMock(return_value=json.dumps([0.1, 0.2, 0.3]))
    database_info = [
        ["dbname", "user", "password", "host", "port"],
        ["mydb", "myuser", "mypassword", "localhost", "port"]]
    db = as_csv_file(database_info)

    # Act
    _, res = get_item(order="test", api_key="test_key", embedding_cache=mock_redis, database_csv_file=db)

    # Assert
    assert res is True, f"expected search to be successful but {res}"


def test_get_item_returns_true_when_successfully_found_closest_item_without_being_passed_embedding_cache(
        mock_boto3_session_client, mock_components
) -> None:
    # Arrange
    database_info = [
        ["dbname", "user", "password", "host", "port"],
        ["mydb", "myuser", "mypassword", "localhost", "port"]]
    db = as_csv_file(database_info)

    # Act
    _, res = get_item(order="test", api_key="test_key", embedding_cache=None, database_csv_file=db)

    # Assert
    assert res is True, f"expected search to be successful but {res}"


def test_get_item_returns_false_when_given_invalid_params(
        mock_boto3_session_client, mock_components
) -> None:
    # Arrange
    data = None

    # Act
    _, res = get_item(data)

    # Assert
    assert res is False, f"expected search to be unsuccessful but {res}"


def test_get_item_throws_correct_exception_when_queue_empty(
        mocker, mock_components
) -> None:
    # Mock the queue to raise queue.Empty
    mock_queue = MagicMock(spec=queue.Queue)
    mock_queue.get.side_effect = queue.Empty

    mocker.patch('src.vector_db.get_item.queue.Queue', return_value=mock_queue)

    database_info = [
        ["dbname", "user", "password", "host", "port"],
        ["mydb", "myuser", "mypassword", "localhost", "port"]]
    db = as_csv_file(database_info)

    # Call the function under test
    error_message, success_flag = get_item(order="test", api_key="test_key", database_csv_file=db)

    # Assertions
    assert error_message == "Error, return_queue.get turned into a deadlock. Check the `get_embedding` function"
    assert success_flag is False


#### Temporarily not needed. ###
# def test_get_item_returns_false_when_given_quantity_greater_than_stock(mock_boto3_session_client, mock_components):
#     # Arrange
#     data = "test"
#     quantity = 1_000
#     key = "mock_api_key"
#     database_info = [
#         ["dbname", "user", "password", "host", "port"],
#         ["mydb", "myuser", "mypassword", "localhost", "port"]]
#
#     aws = as_csv_file(aws_info)
#     db = as_csv_file(database_info)
#
#     # Act
#     _, res = get_item(data, key=key, aws_csv_file=aws, database_csv_file=db)
#
#     # Assert
#     assert res is False, f"expected search not to return most similar item but {res}"
