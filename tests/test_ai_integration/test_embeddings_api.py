import pytest
import pandas as pd
from typing import Final
from mock import MagicMock, patch
from src.ai_integration.embeddings_api import openai_embedding_api, parse_menu_csv, parse_deals_csv

script_path: Final[str] = 'src.ai_integration.embeddings_api'


@pytest.fixture
def mock_openai(
        mocker
) -> MagicMock:
    return mocker.patch(script_path + '.OpenAIEmbeddings')


def test_openai_embeddings_api(
        mock_openai
) -> None:
    # Arrange
    expected_embeddings_instance = MagicMock()
    mock_openai.return_value = expected_embeddings_instance
    expected_vector = [1]
    expected_embeddings_instance.embed_query.side_effect = expected_vector

    # Act
    result_vector = openai_embedding_api(text="test", api_key="foo_key")

    # Assert
    assert result_vector == expected_vector[0], f"expected resulting vector to be {expected_vector} but {result_vector}"
    mock_openai.assert_called_once_with(api_key="foo_key")



def test_parse_menu_csv(
        mocker
) -> None:
    # Arrange
    expected_output = [{"MenuItem": {
        "item_name": "item_name",
        "item_quantity": 2,
        "common_allergin": "common_allergin",
        "num_calories": ('0', '0'),
        "price": 0.0}
    }]

    mocker.patch('pandas.read_csv', return_value=pd.DataFrame({
        "item_name": ["item_name"],
        "item_quantity": [2],
        "common_allergin": ["common_allergin"],
        "num_calories": ["0-0"],
        "price": [0.0]})
    )

    # Act
    result = parse_menu_csv()

    # Assert
    assert result == expected_output, f"expected parsing to be {expected_output} but got {result}"


def test_parse_deal_csv(
        mocker
) -> None:
    # Arrange
    expected_output = [{
            "Deal": {
                "deal": "test_deal",
                "item_name": "test_item_name",
                "item_quantity": 2,
                "item_type": "test_item_type",
                "price": 0.0,
                "related_items": "test_related_items"
            }
        }]

    mocker.patch('pandas.read_csv', return_value=pd.DataFrame({
        "deal": ["test_deal"],
        "item_name": ["test_item_name"],
        'quantity': [2],
        "item_type": ["test_item_type"],
        "price": [0.0],
        "related_items": ["test_related_items"]})
    )

    # Act
    result = parse_deals_csv()

    # Assert
    assert result == expected_output, f"expected parsing to be {expected_output} but got {result}"
