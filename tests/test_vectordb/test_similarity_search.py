import pytest
from mock import patch, MagicMock
from io import StringIO
import csv
from src.vector_db.similarity_search import similarity_search


@pytest.fixture
def mock_components(
        mocker
) -> dict:
    ner_model_mock = mocker.patch('src.ai_integration.fine_tuned_nlp.NERModel')
    mock_instance = ner_model_mock.return_value

    mock_instance.predict.return_value = ([{"entity": "example", "score": 0.99}], None)

    return {
        'ner_model_mock': ner_model_mock,
        'openai_embedding_api': mocker.patch('src.vector_db.similarity_search.openai_embedding_api'),
        'connection_string': mocker.patch('src.vector_db.aws_database_auth.connection_string'),
        'connect': mocker.patch('src.vector_db.similarity_search.psycopg2.connect'),
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


def test_similarity_search_returns_true_when_given_valid_params(
        mocker, mock_boto3_session_client, mock_components
) -> None:
    # Arrange
    data = str({"input": {"Test"}})
    key = "mock_api_key"
    database_info = [
        ["dbname", "user", "password", "host", "port"],
        ["mydb", "myuser", "mypassword", "localhost", "port"]]
    aws_info = [
        ["secret_name", "region_name", "aws_access_key_id", "aws_secret_access_key"],
        ["name", "us-east-1", "aws_access_key_id", "aws_secret_access_key"]]

    aws = as_csv_file(aws_info)
    db = as_csv_file(database_info)

    # Act
    _, res = similarity_search(data, key=key, aws_csv_file=aws, database_csv_file=db)

    # Assert
    assert res is True, f"expected search to be successful but {res}"


def test_similarity_search_returns_valid_object_when_given_valid_params(
        mocker, mock_boto3_session_client, mock_components
) -> None:
    # Arrange
    expected_res = 'connect().cursor().fetchall()'
    data = str({"input": {"Test"}})
    key = "mock_api_key"
    database_info = [
        ["dbname", "user", "password", "host", "port"],
        ["mydb", "myuser", "mypassword", "localhost", "port"]]
    aws_info = [
        ["secret_name", "region_name", "aws_access_key_id", "aws_secret_access_key"],
        ["name", "us-east-1", "aws_access_key_id", "aws_secret_access_key"]]

    # Act
    res, _ = similarity_search(data, key=key, aws_csv_file=as_csv_file(aws_info), database_csv_file=as_csv_file(database_info))
    res_name = str(res).split(" name='")[1].split("' id")[0]

    # Assert
    assert res_name == expected_res, f"expected search to be successful and return valid menu objects but got {res}"


def test_similarity_search_returns_false_when_given_invalid_params(
        mocker, mock_boto3_session_client, mock_components
) -> None:
    # Arrange
    data = None

    # Act
    _, res = similarity_search(data)

    # Assert
    assert res is False, f"expected search to be unsuccessful but {res}"
