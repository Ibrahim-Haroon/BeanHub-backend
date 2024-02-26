import os
import pytest
from mock import patch, MagicMock
from typing import Final
from src.external_connections.connection_manager import ConnectionManager

script_path: Final[str] = 'src.external_connections.connection_manager'


@pytest.fixture()
def mock_environment_variables(

) -> None:
    os.environ['S3_BUCKET_NAME'] = 'foo'
    os.environ['REDIS_HOST'] = 'foo'
    os.environ['REDIS_PORT'] = 'foo'


@pytest.fixture(autouse=True)
def reset_connection_manager():
    ConnectionManager._ConnectionManager__instance = None
    yield


def test_connection_manager_singleton(

) -> None:
    # Arrange and Act
    manager1 = ConnectionManager.connect()
    manager2 = ConnectionManager.connect()

    # Assert
    assert manager1 is manager2, \
        f"expected {manager1}, got {manager2}"


@patch(script_path + ".boto3.client")
def test_connect_to_s3_success(
        mock_boto_client, mock_environment_variables
) -> None:
    # Arrange
    mock_boto_client.return_value = MagicMock(name='s3_client')

    # Act
    manager = ConnectionManager.connect()
    s3_client = manager.s3()

    # Assert
    mock_boto_client.assert_called_once_with('s3')
    assert s3_client == mock_boto_client.return_value, "Expected S3 client to be initialized successfully"


@pytest.mark.parametrize("db_type,expected_attribute", [
    ('conversation', '_ConnectionManager__conversation_cache'),
    ('deal', '_ConnectionManager__deal_cache'),
    ('embedding', '_ConnectionManager__embedding_cache'),
])
@patch(script_path + ".redis.StrictRedis")
def test_connect_to_redis_cache_success(
        mock_strict_redis, mock_environment_variables, db_type, expected_attribute
) -> None:
    # Arrange
    mock_strict_redis.return_value = MagicMock(name=f'{db_type}_cache')

    # Act
    manager = ConnectionManager.connect()
    redis_cache = manager.redis_cache(db_type)

    # Assert
    assert getattr(manager, expected_attribute) == redis_cache, \
        f"Expected {db_type} cache to be initialized successfully"


@patch(script_path + ".RabbitMQConnectionPool")
def test_connect_to_rabbitmq_pool_success(
        mock_rabbitmq_pool, mock_environment_variables
) -> None:
    # Arrange
    mock_rabbitmq_pool.return_value = MagicMock(name='rabbitmq_connection_pool')

    # Act
    manager = ConnectionManager.connect()
    rabbitmq_pool = manager.rabbitmq_connection()

    # Assert
    mock_rabbitmq_pool.assert_called_once_with(manager.rabbitmq_max_connections)
    assert rabbitmq_pool == mock_rabbitmq_pool.return_value.get_connection.return_value, \
        f"Expected RabbitMQ connection pool to be initialized successfully"


@patch(script_path + ".psycopg2.pool.SimpleConnectionPool")
@patch(script_path + ".connection_string")
def test_connect_to_postgresql_success(
        mock_connection_string, mock_simple_connection_pool, mock_environment_variables
) -> None:
    # Arrange
    mock_connection_string.return_value = "postgres_connection_string"
    mock_simple_connection_pool.return_value = MagicMock(name='postgresql_connection_pool')

    # Act
    manager = ConnectionManager.connect()
    connection_pool = manager.connection_pool()

    # Assert
    mock_simple_connection_pool.assert_called_once()
    assert connection_pool == mock_simple_connection_pool.return_value, \
        "Expected PostgreSQL connection pool to be initialized successfully"








