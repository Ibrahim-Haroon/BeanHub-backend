import pytest
from src.ai_integration.fine_tuned_nlp import *


@pytest.fixture
def mock_components(mocker):
    ner_model_mock = mocker.patch('src.ai_integration.fine_tuned_nlp.NERModel')
    mock_instance = ner_model_mock.return_value

    mock_instance.predict.return_value = ([{"entity": "example", "score": 0.99}], None)

    return {
        'ner_model_mock': ner_model_mock
    }


def test_that_ner_transformer_returns_prediction_given_string(mock_components):
    # Arrange
    expected_prediction = [{"entity": "example", "score": 0.99}]

    # Act
    prediction = ner_transformer("test")

    # Assert
    assert prediction == expected_prediction, f"expected prediction to be {expected_prediction} but got {prediction}"


def test_that_ner_transformer_returns_empty_list_when_given_empty_string(mock_components):
    # Arrange
    empty_string = ""
    expected_prediction = []

    # Act
    prediction = ner_transformer(empty_string)

    # Assert
    assert prediction == expected_prediction, f"expected prediction to be {expected_prediction} but got {prediction}"
