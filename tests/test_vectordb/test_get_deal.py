import csv
import json
import queue
import pytest
from io import StringIO
from mock import MagicMock, patch
from src.vector_db.get_deal import get_deal


@pytest.fixture
def mock_components(
        mocker
) -> dict:
    mock_embedding_api = mocker.patch('src.vector_db.get_deal.openai_embedding_api')
    mock_embedding_api.return_value = [0.1, 0.2, 0.3]

    return {
        'openai_embedding_api': mock_embedding_api,
        'connection_string': mocker.patch('src.vector_db.aws_database_auth.connection_string'),
    }


@pytest.fixture()
def mock_normal_connect(
        mocker
) -> MagicMock:
    mock_connect = mocker.patch('src.vector_db.get_deal.psycopg2.connect')
    mock_connect.return_value.cursor.return_value.fetchall.return_value = [(7, 'test', 6, 'test', '(60,120)', 10.0)]

    return mock_connect


@pytest.fixture()
def mock_connection_pool(
        mocker
) -> MagicMock:
    mock_fetchall = mocker.Mock()
    mock_fetchall.fetchall.return_value = [(7, 'test', 6, 'test', '(60,120)', 10.0)]
    mock_cursor = mocker.Mock()
    mock_cursor.cursor.return_value = mock_fetchall
    mock_pool = mocker.patch('src.vector_db.get_deal.psycopg2.pool.SimpleConnectionPool')
    mock_pool.return_value.getconn.return_value = mock_cursor

    return mock_pool


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


def test_get_deal_returns_true_when_successfully_found_closest_item_and_adds_to_cache(
        mocker, mock_boto3_session_client, mock_components, mock_normal_connect
) -> None:
    # Arrange
    mock_redis = mocker.Mock()
    mock_redis.set = MagicMock()
    mock_redis.exists = MagicMock(return_value=False)
    mock_redis.get = MagicMock(return_value=json.dumps([0.1, 0.2, 0.3]))
    order = {
        "CoffeeItem": {
            "cart_action": "add",
            "item_name": "test"
        }
    }
    database_info = [
        ["dbname", "user", "password", "host", "port"],
        ["mydb", "myuser", "mypassword", "localhost", "port"]]
    db = as_csv_file(database_info)

    # Act
    _, _, res = get_deal(order=order, api_key="test_key", embedding_cache=mock_redis, database_csv_file=db)

    # Assert
    assert res is True, f"expected search to be successful but {res}"


def test_get_deal_returns_true_when_successfully_found_closest_item_and_cache_hit(
        mocker, mock_boto3_session_client, mock_components, mock_normal_connect
) -> None:
    # Arrange
    mock_redis = mocker.Mock()
    mock_redis.set = MagicMock()
    mock_redis.exists = MagicMock(return_value=True)
    mock_redis.get = MagicMock(return_value=json.dumps([0.1, 0.2, 0.3]))
    order = {
        "CoffeeItem": {
            "cart_action": "add",
            "item_name": "test"
        }
    }
    database_info = [
        ["dbname", "user", "password", "host", "port"],
        ["mydb", "myuser", "mypassword", "localhost", "port"]]
    db = as_csv_file(database_info)

    # Act
    _, _, res = get_deal(order=order, api_key="test_key", embedding_cache=mock_redis, database_csv_file=db)

    # Assert
    assert res is True, f"expected search to be successful but {res}"



def test_get_deal_returns_true_when_successfully_found_closest_item_without_being_passed_embedding_cache(
        mock_boto3_session_client, mock_components, mock_normal_connect
) -> None:
    # Arrange
    order = {
        "CoffeeItem": {
            "cart_action": "add",
            "item_name": "test"
        }
    }
    database_info = [
        ["dbname", "user", "password", "host", "port"],
        ["mydb", "myuser", "mypassword", "localhost", "port"]]
    db = as_csv_file(database_info)

    # Act
    _, _, res = get_deal(order=order, api_key="test_key", embedding_cache=None, database_csv_file=db)

    # Assert
    assert res is True, f"expected search to be successful but {res}"


def test_get_deal_returns_false_when_item_type_is_invalid(
        mock_boto3_session_client, mock_components, mock_normal_connect
) -> None:
    # Arrange
    order = {
        "Foo": {
            "cart_action": "add",
            "item_name": "test"
        }
    }
    # Act
    _, _, res = get_deal(order)

    # Assert
    assert res is False, f"expected search to be unsuccessful but {res}"


def test_get_deal_returns_true_when_successfully_found_closest_item_using_embedding_cache(
        mocker, mock_boto3_session_client, mock_components, mock_connection_pool
) -> None:
    # Arrange
    mock_redis = mocker.Mock()
    mock_redis.set = MagicMock()
    mock_redis.exists = MagicMock(return_value=True)
    mock_redis.get = MagicMock(return_value=json.dumps([0.1, 0.2, 0.3]))

    order = {
        "CoffeeItem": {
            "cart_action": "add",
            "item_name": "test"
        }
    }
    database_info = [
        ["dbname", "user", "password", "host", "port"],
        ["mydb", "myuser", "mypassword", "localhost", "port"]]
    db = as_csv_file(database_info)

    # Act
    _, _, res = get_deal(order=order, api_key="test_key", connection_pool=mock_connection_pool, embedding_cache=mock_redis, database_csv_file=db)

    # Assert
    assert res is True, f"expected search to be successful but {res}"


def test_get_deal_returns_false_when_given_invalid_params(
        mock_boto3_session_client, mock_components, mock_normal_connect
) -> None:
    # Arrange
    data = None

    # Act
    _, _, res = get_deal(data)

    # Assert
    assert res is False, f"expected search to be unsuccessful but {res}"


def test_get_deal_throws_correct_exception_when_queue_empty(
        mocker, mock_components, mock_normal_connect
) -> None:
    # Mock the queue to raise queue.Empty
    mock_queue = MagicMock(spec=queue.Queue)
    mock_queue.get.side_effect = queue.Empty

    # Patch the queue.Queue class in the get_deal module
    mocker.patch('src.vector_db.get_deal.queue.Queue', return_value=mock_queue)

    # Setup the test with mock data and dependencies
    order = {
        "CoffeeItem": {
            "cart_action": "add",
            "item_name": "test"
        }
    }
    database_info = [
        ["dbname", "user", "password", "host", "port"],
        ["mydb", "myuser", "mypassword", "localhost", "port"]]
    db = as_csv_file(database_info)

    # Call the function under test
    error_message, _, success_flag = get_deal(order=order, api_key="test_key", database_csv_file=db)

    # Assertions
    assert error_message == "Error, return_queue.get turned into a deadlock. Check the `get_embedding` function"
    assert success_flag is False
