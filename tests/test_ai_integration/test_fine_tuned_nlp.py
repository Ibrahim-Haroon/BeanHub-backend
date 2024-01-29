import os
import pytest
from mock import MagicMock
from src.ai_integration.fine_tuned_nlp import ner_transformer, Order


@pytest.fixture
def mock_components(
        mocker
) -> dict:
    ner_model_mock = mocker.patch('src.ai_integration.fine_tuned_nlp.NERModel')
    mock_instance = ner_model_mock.return_value

    mock_instance.predict.return_value = ([[{'test': 'O'}]], None)

    return {
        'ner_model_mock': ner_model_mock
    }


@pytest.fixture
def mock_database_components(
        mocker
) -> dict:
    return {
        'register_vector': mocker.patch('pgvector.psycopg2.register_vector'),
        'connect': mocker.patch('src.vector_db.get_item.psycopg2.connect'),
        'input': mocker.patch('builtins.input'),
    }


@pytest.fixture
def mock_boto3_session_client(
        mocker
) -> MagicMock:
    return mocker.patch('boto3.session.Session.client', return_value=MagicMock())


def test_that_ner_transformer_returns_prediction_given_string_and_does_not_print_out_prediction(
        mock_components
) -> None:
    # Arrange
    expected_prediction = [[{'test': 'O'}]]

    # Act
    prediction = ner_transformer("test")

    # Assert
    assert prediction == expected_prediction, f"expected prediction to be {expected_prediction} but got {prediction}"


def test_that_ner_transformer_returns_prediction_given_string_and_does_print_out_prediction(
        mock_components, capsys
) -> None:
    # Arrange
    expected_prediction = [[{'test': 'O'}]]

    # Act
    prediction = ner_transformer("test", print_prediction=True)
    captured = capsys.readouterr()

    # Assert
    assert "[[{'test': 'O'}]]" in captured.out
    assert prediction == expected_prediction, f"expected prediction to be {expected_prediction} but got {prediction}"


def test_that_ner_transformer_returns_empty_list_when_given_empty_string(
        mock_components
) -> None:
    # Arrange
    empty_string = ""
    expected_prediction = []

    # Act
    prediction = ner_transformer(empty_string)

    # Assert
    assert prediction == expected_prediction, f"expected prediction to be {expected_prediction} but got {prediction}"


