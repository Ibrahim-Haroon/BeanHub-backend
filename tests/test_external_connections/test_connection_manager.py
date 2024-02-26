import os
import pytest
from mock import patch, MagicMock
from typing import Final
from src.external_connections.connection_manager import ConnectionManager

script_path: Final[str] = 'src.external_connections.connection_manager'


@pytest.fixture(autouse=True)
def mock_environment_variables(

) -> MagicMock:
    with patch.dict(
            os.environ,
            {
                "SECRET_NAME": "test_secret_name",
                "AWS_DEFAULT_REGION": "test_aws_default_region",
                "AWS_ACCESS_KEY_ID": "test_access_key_id",
                "AWS_SECRET_ACCESS_KEY": "test_secret_access_key",
                "S3_BUCKET_NAME": "test_bucket_name",
                "REDIS_HOST": "test_redis_host",
                "REDIS_PORT": "test_redis_port",
                "RDS_DB_NAME": "test_db",
                "RDS_HOSTNAME": "test_host",
                "RDS_USERNAME": "test_user",
                "RDS_PASSWORD": "test_password",
                "RDS_PORT": "1234"
            }
    ):
        yield


@pytest.fixture
def mock_components(
        mocker
) -> dict:

    return {
        'botocore.session.Session': mocker.patch('boto3.session.Session.client', return_value=MagicMock()),
        'rabbitmq_connection_pool': mocker.patch(script_path + ".RabbitMQConnectionPool", return_value=MagicMock()),
        'psycopg2.pool.SimpleConnectionPool': mocker.patch(script_path + ".psycopg2.pool.SimpleConnectionPool"),
    }


@pytest.fixture(autouse=True)
def reset_connection_manager():
    ConnectionManager._ConnectionManager__instance = None
    yield


def test_connection_manager_singleton(
        mocker, mock_components
) -> None:
    # Arrange

    # Act
    manager1 = ConnectionManager.connect()
    manager2 = ConnectionManager.connect()

    # Assert
    assert manager1 is manager2, \
        f"expected {manager1}, got {manager2}"


@patch(script_path + ".boto3.client")
def test_connect_to_s3_success(
        mock_boto_client, mock_environment_variables, mock_components
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
        mock_strict_redis, mock_environment_variables, db_type, expected_attribute, mock_components
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
        mock_rabbitmq_pool, mock_environment_variables, mock_components
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
def test_connect_to_postgresql_success(
        mock_simple_connection_pool, mock_environment_variables, mock_components
) -> None:
    # Arrange

    # Act
    manager = ConnectionManager.connect()
    connection_pool = manager.connection_pool()

    # Assert
    mock_simple_connection_pool.assert_called_once()
    assert connection_pool == mock_simple_connection_pool.return_value, \
        "Expected PostgreSQL connection pool to be initialized successfully"
