import csv
import json
import pytest
from io import StringIO
from mock import MagicMock
from src.vector_db.get_deal import get_deal


@pytest.fixture
def mock_components(
        mocker
) -> dict:
    mock_db_instance = mocker.patch('src.vector_db.get_deal.psycopg2.connect')
    mock_db_instance.return_value.cursor.return_value.fetchall.return_value = [(7, 'test', 6, 'test', '(60,120)', 10.0)]

    mock_embedding_api = mocker.patch('src.vector_db.get_deal.openai_embedding_api')
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


def test_get_deal_returns_true_when_successfully_found_closest_item_and_adds_to_cache(
        mocker, mock_boto3_session_client, mock_components
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
        mocker, mock_boto3_session_client, mock_components
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
        mock_boto3_session_client, mock_components
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
        mock_boto3_session_client, mock_components
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


def test_get_deal_returns_false_when_given_invalid_params(
        mock_boto3_session_client, mock_components
) -> None:
    # Arrange
    data = None

    # Act
    _, _, res = get_deal(data)

    # Assert
    assert res is False, f"expected search to be unsuccessful but {res}"
