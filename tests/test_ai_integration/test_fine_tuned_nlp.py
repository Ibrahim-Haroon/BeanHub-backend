import os
import pytest
from mock import MagicMock
from src.ai_integration.fine_tuned_nlp import ner_transformer, Order


@pytest.fixture
def mock_ner_model(
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
    mock_fetchall = mocker.Mock()
    mock_fetchall.fetchall.return_value = [(7, 'test', 6, 'test', '(60,120)', 10.0)]

    mock_cursor = mocker.Mock()
    mock_cursor.cursor.return_value = mock_fetchall

    mock_connection_pool = mocker.patch('src.ai_integration.fine_tuned_nlp.psycopg2.pool.SimpleConnectionPool')
    mock_connection_pool.return_value.getconn.return_value = mock_cursor

    mock_embedding_api = mocker.patch('src.vector_db.get_item.openai_embedding_api')
    mock_embedding_api.return_value = [0.1, 0.2, 0.3]

    return {
        'register_vector': mocker.patch('pgvector.psycopg2.register_vector'),
        'pool': mock_connection_pool,
        'embedding_api': mock_embedding_api,
        'input': mocker.patch('builtins.input'),
    }


@pytest.fixture
def mock_boto3_session_client(
        mocker
) -> MagicMock:
    return mocker.patch('boto3.session.Session.client', return_value=MagicMock())


def test_that_ner_transformer_returns_prediction_given_string_and_does_not_print_out_prediction(
        mock_ner_model
) -> None:
    # Arrange
    expected_prediction = [[{'test': 'O'}]]

    # Act
    prediction = ner_transformer("test")

    # Assert
    assert prediction == expected_prediction, \
        f"expected prediction to be {expected_prediction} but got {prediction}"


def test_that_ner_transformer_returns_prediction_given_string_and_does_print_out_prediction(
        mock_ner_model, capsys
) -> None:
    # Arrange
    expected_prediction = [[{'test': 'O'}]]

    # Act
    prediction = ner_transformer("test", print_prediction=True)
    captured = capsys.readouterr()

    # Assert
    assert "[[{'test': 'O'}]]" in captured.out
    assert prediction == expected_prediction,\
        f"expected prediction to be {expected_prediction} but got {prediction}"


def test_that_ner_transformer_returns_empty_list_when_given_empty_string(
        mock_ner_model
) -> None:
    # Arrange
    empty_string = ""
    expected_prediction = []

    # Act
    prediction = ner_transformer(empty_string)

    # Assert
    assert prediction == expected_prediction,\
        f"expected prediction to be {expected_prediction} but got {prediction}"


def test_that_make_order_in_Order_class_returns_expected_dict_for_coffee_item(
        mocker, mock_boto3_session_client, mock_database_components
) -> None:
    # Arrange
    mocker.patch.dict(os.environ, {
        "OPENAI_API_KEY": "test_api_key",
        "AWS_ACCESS_KEY_ID": "test_access_key_id",
        "AWS_SECRET_ACCESS_KEY": "test_secret_access_key",
        "AWS_DEFAULT_REGION": "test_region",
        "SECRET_NAME": "test_secret_name",
        "RDS_DB_NAME": "test_db_name",
        "RDS_USERNAME": "test_username",
        "RDS_PASSWORD": "test_password",
        "RDS_HOSTNAME": "test_hostname",
        "RDS_PORT": "test_port"
    })

    expected_return_value = {
        'CoffeeItem': {
            'item_name': 'black coffee',
            'quantity': [1, 1, 1, 1],
            'price': [10.0, 10.0, 10.0, 10.0],
            'temp': 'regular',
            'add_ons': ['pump of caramel'],
            'milk_type': 'cream',
            'sweeteners': ['sugar'],
            'size': 'regular',
            'cart_action': 'insertion',
            'common_allergies_in_item': 'test',
            'num_calories': ['(60,120)', '(60,120)', '(60,120)', '(60,120)']
        }
    }
    mock_coffee_order = "One black coffee with one cream and one sugar and a pump of caramel"

    # Act
    actual_return_value = Order(mock_coffee_order).make_order()

    # Assert
    assert actual_return_value == expected_return_value,\
        f"expected return value to be {expected_return_value} but got {actual_return_value}"


def test_that_make_order_in_Order_class_returns_expected_dict_for_beverage_item(
    mocker, mock_boto3_session_client, mock_database_components
) -> None:
    # Arrange
    mocker.patch.dict(os.environ, {
        "OPENAI_API_KEY": "test_api_key",
        "AWS_ACCESS_KEY_ID": "test_access_key_id",
        "AWS_SECRET_ACCESS_KEY": "test_secret_access_key",
        "AWS_DEFAULT_REGION": "test_region",
        "SECRET_NAME": "test_secret_name",
        "RDS_DB_NAME": "test_db_name",
        "RDS_USERNAME": "test_username",
        "RDS_PASSWORD": "test_password",
        "RDS_HOSTNAME": "test_hostname",
        "RDS_PORT": "test_port"
    })

    expected_return_value = {
        'BeverageItem': {
            'add_ons': [],
            'cart_action': 'insertion',
            'common_allergies_in_item': 'test',
            'item_name': 'water',
            'num_calories': ['(60,120)'],
            'price': [10.0],
            'quantity': [1],
            'size': 'regular',
            'sweeteners': [],
            'temp': 'regular'}
    }
    mock_beverage_order = "1 water"

    # Act
    actual_return_value = Order(mock_beverage_order).make_order()

    # Assert
    assert actual_return_value == expected_return_value,\
        f"expected return value to be {expected_return_value} but got {actual_return_value}"


def test_that_make_order_in_Order_class_returns_expected_dict_for_food_item(
    mocker, mock_boto3_session_client, mock_database_components
) -> None:
    # Arrange
    mocker.patch.dict(os.environ, {
        "OPENAI_API_KEY": "test_api_key",
        "AWS_ACCESS_KEY_ID": "test_access_key_id",
        "AWS_SECRET_ACCESS_KEY": "test_secret_access_key",
        "AWS_DEFAULT_REGION": "test_region",
        "SECRET_NAME": "test_secret_name",
        "RDS_DB_NAME": "test_db_name",
        "RDS_USERNAME": "test_username",
        "RDS_PASSWORD": "test_password",
        "RDS_HOSTNAME": "test_hostname",
        "RDS_PORT": "test_port"
    })

    expected_return_value = {
        'FoodItem': {
            'cart_action': 'modification',
            'common_allergies_in_item': 'test',
            'item_name': 'egg and cheese croissant',
            'num_calories': ['(60,120)'],
            'price': [10.0],
            'quantity': [-1]
        }
    }
    mock_food_order = "remove the egg and cheese croissant"

    # Act
    actual_return_value = Order(mock_food_order).make_order()

    # Assert
    assert actual_return_value == expected_return_value, \
        f"expected return value to be {expected_return_value} but got {actual_return_value}"



def test_that_make_order_in_Order_class_returns_expected_dict_for_bakery_item(
    mocker, mock_boto3_session_client, mock_database_components
) -> None:
    # Arrange
    mocker.patch.dict(os.environ, {
        "OPENAI_API_KEY": "test_api_key",
        "AWS_ACCESS_KEY_ID": "test_access_key_id",
        "AWS_SECRET_ACCESS_KEY": "test_secret_access_key",
        "AWS_DEFAULT_REGION": "test_region",
        "SECRET_NAME": "test_secret_name",
        "RDS_DB_NAME": "test_db_name",
        "RDS_USERNAME": "test_username",
        "RDS_PASSWORD": "test_password",
        "RDS_HOSTNAME": "test_hostname",
        "RDS_PORT": "test_port"
    })

    expected_return_value = {
        'BakeryItem': {
            'cart_action': 'question',
            'common_allergies_in_item': 'test',
            'item_name': 'glazed donut',
            'num_calories': ['(60,120)'],
            'price': [10.0],
            'quantity': [6]
        }
    }
    mock_bakery_order = "Do you sell glazed donut"

    # Act
    actual_return_value = Order(mock_bakery_order).make_order()

    # Assert
    assert actual_return_value == expected_return_value,\
        f"expected return value to be {expected_return_value} but got {actual_return_value}"


def test_that_make_order_in_Order_class_returns_empty_dict_for_item_of_invalid_type(
    mocker, mock_boto3_session_client, mock_database_components
) -> None:
    # Arrange
    mocker.patch.dict(os.environ, {
        "OPENAI_API_KEY": "test_api_key",
        "AWS_ACCESS_KEY_ID": "test_access_key_id",
        "AWS_SECRET_ACCESS_KEY": "test_secret_access_key",
        "AWS_DEFAULT_REGION": "test_region",
        "SECRET_NAME": "test_secret_name",
        "RDS_DB_NAME": "test_db_name",
        "RDS_USERNAME": "test_username",
        "RDS_PASSWORD": "test_password",
        "RDS_HOSTNAME": "test_hostname",
        "RDS_PORT": "test_port"
    })
    expected_return_value = {}
    mock_bakery_order = "1 invalid item"

    # Act
    actual_return_value = Order(mock_bakery_order).make_order()

    # Assert
    assert actual_return_value == expected_return_value, \
        f"expected return value to be {expected_return_value} but got {actual_return_value}"
