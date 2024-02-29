import pika
import pytest
from mock import patch, MagicMock
from typing import Final
from src.external_connections.rabbitmq_connection_pool import RabbitMQConnectionPool
import os

script_path: Final[str] = 'src.external_connections.rabbitmq_connection_pool'


@pytest.fixture()
def mock_environment_variables(

) -> None:
    os.environ['RABBITMQ_HOST'] = 'foo'


@patch('pika.BlockingConnection')
def test_rabbitmq_connection_pool_initializes_with_max_size_connections(
        mock_pika_blocking_connection: MagicMock, mock_environment_variables
) -> None:
    # Arrange
    pool = RabbitMQConnectionPool.__new__(RabbitMQConnectionPool)
    num_connections = 5

    # Act
    pool.__init__(num_connections)

    # Assert
    assert pool._connections.qsize() == num_connections, \
        f"expected {num_connections} connections, got {pool._connections.qsize()}"


@patch('pika.BlockingConnection')
def test_get_connection_returns_existing_connection(
        mock_pika_blocking_connection: MagicMock, mock_environment_variables
) -> None:
    # Arrange
    pool = RabbitMQConnectionPool.__new__(RabbitMQConnectionPool)
    mock_pika_blocking_connection.return_value = "connection"
    num_connections = 5

    # Act
    pool.__init__(num_connections)
    connection = pool.get_connection()

    # Assert
    assert connection == "connection", f"expected connection, got {connection}"
    assert pool._connections.qsize() == num_connections - 1, \
        f"expected {num_connections - 1} connections, got {pool._connections.qsize()}"


@patch('pika.BlockingConnection')
def test_get_connection_creates_new_connection_when_pool_is_empty(
        mock_pika_blocking_connection: MagicMock, mock_environment_variables
) -> None:
    # Arrange
    pool = RabbitMQConnectionPool.__new__(RabbitMQConnectionPool)
    mock_pika_blocking_connection.return_value = "connection"
    num_connections = 1

    # Act
    pool.__init__(num_connections)
    connection = pool.get_connection()
    connection = pool.get_connection()

    # Assert
    assert connection == "connection", f"expected connection, got {connection}"
    assert pool._connections.qsize() == num_connections - 1, \
        f"expected {num_connections} connections, got {pool._connections.qsize()}"


@patch('pika.BlockingConnection')
@patch('time.sleep', return_value=None)
def test_create_new_connection_retries_on_failure(
        mock_sleep: MagicMock, mock_pika_blocking_connection: MagicMock, mock_environment_variables
) -> None:
    # Arrange
    pool = RabbitMQConnectionPool.__new__(RabbitMQConnectionPool)
    mock_pika_blocking_connection.side_effect = [Exception("Connection failed"), "successful_connection"]
    num_connections = 1

    # Act
    pool.__init__(num_connections)
    connection = pool.get_connection()

    # Assert
    assert connection == "successful_connection", \
        f"Expected successful connection, got {connection}"
