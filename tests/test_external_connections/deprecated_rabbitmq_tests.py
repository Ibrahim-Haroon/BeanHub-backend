"""
This module contains deprecated tests for the RabbitMQ connection used in ConnectionManager.
"""

'rabbitmq_connection_pool': mocker.patch(script_path + ".RabbitMQConnectionPool", return_value=MagicMock())

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