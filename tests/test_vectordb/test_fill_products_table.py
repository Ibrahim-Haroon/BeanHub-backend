import csv
import pytest
from io import StringIO
from mock import patch, MagicMock
from src.vector_db.fill_products_table import fill_products_table


@pytest.fixture
def mock_components(
        mocker
) -> dict:
    return {
        'openai_embedding_api': mocker.patch('src.vector_db.fill_products_table.openai_embedding_api'),
        'connection_string': mocker.patch('src.vector_db.aws_database_auth.connection_string'),
        'register_vector': mocker.patch('pgvector.psycopg2.register_vector'),
        'connect': mocker.patch('src.vector_db.fill_products_table.psycopg2.connect'),
        'input': mocker.patch('builtins.input'),
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


@patch('builtins.input', side_effect=["YES", "beanKnowsWhatBeanWants"])
def test_fill_products_table_returns_true_if_pass_auth(
        mocker, mock_components, mock_boto3_session_client
) -> None:
    # Arrange
    data = [
        {
            "MenuItem": {
                "item_name": "TestItem",
                "item_quantity": "5",
                "common_allergin": "peanuts",
                "num_calories": "500",
                "price": 10.0
            }
        }
    ]
    key = "mock_api_key"
    database_info = [
        ["dbname", "user", "password", "host", "port"],
        ["mydb", "myuser", "mypassword", "localhost", "port"]]
    aws_info = [
        ["secret_name", "region_name", "aws_access_key_id", "aws_secret_access_key"],
        ["name", "us-east-1", "aws_access_key_id", "aws_secret_access_key"]]

    # Act
    result = fill_products_table(data, key, as_csv_file(aws_info), as_csv_file(database_info))

    # Assert
    assert result is True, f"expect True but got {result}"


@patch('builtins.input', side_effect=["YES", "wrong_passkey"])
def test_fill_products_table_exits_when_wrong_passkey_given(
        mock_components
) -> None:
    # Arrange
    data = [
        {
            "MenuItem": {
                "item_name": "TestItem",
                "common_allergin": "peanuts",
                "num_calories": "500",
                "price": 10.0
            }
        }
    ]
    key = "mock_key"

    # Act
    result = fill_products_table(data, key)

    # Assert
    assert result is False, f"expected False but got {result}"


@patch('builtins.input', return_value="NO")
def test_fill_products_table_exits_when_no_entered(
        mock_components
) -> None:
    # Arrange
    data = [
        {
            "MenuItem":
            {
                "item_name": "TestItem",
                "common_allergin": "peanuts",
                "num_calories": "500",
                "price": 10.0
            }
        }
    ]
    key = "mock_key"

    # Act
    result = fill_products_table(data, key)

    # Assert
    assert result is False, f"expect False but got {result}"
