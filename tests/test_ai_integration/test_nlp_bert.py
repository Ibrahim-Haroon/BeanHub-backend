import pytest
from src.ai_integration.nlp_bert import *


@pytest.fixture
def mock_components(mocker):
    ner_model_mock = mocker.patch('scripts.ai_integration.nlp_bert.NERModel')
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

    assert prediction == expected_prediction, f"expected prediction to be {expected_prediction} but got {prediction}"


def test_that_ner_transformer_returns_empty_list_when_given_empty_string(mock_components):
    # Arrange
    empty_string = ""
    expected_prediction = []

    # Act
    prediction = ner_transformer(empty_string)

    assert prediction == expected_prediction, f"expected prediction to be {expected_prediction} but got {prediction}"


def test_that_format_ner_correctly_formats_prediction_correctly_for_list_of_O_tags():
    # Arrange
    prediction = [
        [{'this': 'O'}, {'is': 'O'}, {'a': 'O'}, {'test': 'O'}]
    ]
    expected_res = []


    # Act
    res = format_ner(prediction)


    # Assert
    assert res == expected_res, f"expected formatted string to be {expected_res} but got {res}"


def test_that_format_ner_correctly_formats_prediction_correctly_for_list_of_I_and_B_tags():
    # Arrange
    prediction = [
        [{'Want': 'O'}, {'5': 'B_QUANTITY'}, {'lattes': 'I_COFFEE_TYPE'}, {'and': 'O'}, {'a': 'O'}, {'hug': 'O'}]
    ]
    expected_res = [['lattes', 5]]


    # Act
    res = format_ner(prediction)


    # Assert
    assert res == expected_res, f"expected formatted string to be {expected_res} but got {res}"