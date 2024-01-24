import pytest
from src.ai_integration.fine_tuned_nlp import *


@pytest.fixture
def mock_components(
        mocker
) -> dict:
    ner_model_mock = mocker.patch('src.ai_integration.fine_tuned_nlp.NERModel')
    mock_instance = ner_model_mock.return_value

    mock_instance.predict.return_value = ([{"entity": "example", "score": 0.99}], None)

    return {
        'ner_model_mock': ner_model_mock
    }


def test_that_ner_transformer_returns_prediction_given_string(
        mock_components
) -> None:
    # Arrange
    expected_prediction = [{"entity": "example", "score": 0.99}]

    # Act
    prediction = ner_transformer("test")

    # Assert
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





def test_sweeteners_assignment():
    # Arrange
    order_details = {
        'beverage': ['example_beverage'],
        'quantities': [1],
        'temperature': ['hot'],
        'sweeteners': ['sugar', 'honey'],
        'add_ons': ['cream'],
        'sizes': ['large']
    }

    # Act
    order_instance = Order("formatted_order", embedding_cache=None, aws_connected=False)
    order_instance.make_beverage_order(order_details)

    # Assert
    assert order_instance.sweeteners == order_details.get('sweeteners', [])

def test_make_food_order():
    # Arrange
    order_details = {
        'food': ['example_food'],
        'quantities': [2]
    }

    # Add the missing keys to match the function's requirements
    order_details['temperature'] = ['example_temperature']
    order_details['add_ons'] = ['example_add_on']
    order_details['sizes'] = ['example_size']

    # Act
    order_instance = Order("formatted_order", embedding_cache=None, aws_connected=False)
    order_instance.make_food_order(order_details)

    # Assert
    assert order_instance.item_name == order_details['food'][0]
    
    # Check if 'quantity' is present in the returned dictionary
    assert 'quantity' in order_instance.make_food_order(order_details)['FoodItem']

def test_make_bakery_order():
    # Arrange
    order_details = {
        'bakery': ['example_bakery'],
        'quantities': [3]
    }

    # Act
    order_instance = Order("formatted_order", embedding_cache=None, aws_connected=False)
    bakery_item = order_instance.make_bakery_order(order_details)['BakeryItem']

    # Assert
    assert order_instance.item_name == order_details['bakery'][0]
    
    # Check if 'quantity' is present in the returned dictionary
    assert 'quantity' in bakery_item

    # Ensure 'quantity' is a positive value
    if isinstance(bakery_item['quantity'], list):
        assert all(qty > 0 for qty in bakery_item['quantity'])
    else:
        assert isinstance(bakery_item['quantity'], int) and bakery_item['quantity'] > 0
