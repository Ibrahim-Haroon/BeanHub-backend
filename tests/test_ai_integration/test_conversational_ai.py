import pytest
from os import environ
from typing import Final
from unittest.mock import patch, MagicMock
from src.ai_integration.conversational_ai import conv_ai, local_conv_ai

script_path: Final[str] = 'src.ai_integration.conversational_ai'


@pytest.fixture()
def mock_environment_variables(

) -> None:
    environ['OPENAI_API_KEY'] = 'foo'


@pytest.fixture
def mock_client(

):
    with patch(script_path + ".OpenAI") as mock:
        yield mock


def test_conv_ai_without_deal(
        mock_client, mock_environment_variables
) -> None:
    # Arrange
    expected_response = "Response without deal"
    mock_client.return_value.chat.completions.create.return_value = iter(
        [
            MagicMock(
                choices=[
                    MagicMock(
                        delta=MagicMock(
                            content=expected_response
                        )
                    )
                ]
            )
        ]
    )

    # Act
    response = conv_ai(
        "Order: One coffee",
        "Coffee: $3",
        "Hello",
        max_tokens=50)
    result = next(response)

    # Assert
    assert result == "Response without deal"


def test_conv_ai_with_deal(
        mock_client, mock_environment_variables
) -> None:
    # Arrange
    expected_response = "Response with deal"
    mock_client.return_value.chat.completions.create.return_value = iter(
        [
            MagicMock(
                choices=[
                    MagicMock(
                        delta=MagicMock(
                            content=expected_response
                        )
                    )
                ]
            )
        ]
    )

    # Act
    response = conv_ai(
        "Order: One burger",
        "Burger: $5",
        "Hi",
        "Special deal",
        max_tokens=50)
    result = next(response)

    # Assert
    assert result == expected_response


def test_local_conv_ai_without_deal(
        mock_client
) -> None:
    # Arrange
    expected_response = "Local Response without deal"
    mock_client.return_value.chat.completions.create.return_value = iter(
        [
            MagicMock(
                choices=[
                    MagicMock(
                        delta=MagicMock(
                            content=expected_response
                        )
                    )
                ]
            )
        ]
    )

    # Act
    response = local_conv_ai(
        "Order: One pizza",
        "Pizza: $10",
        "Hey there",
        api_key="dummy-key"
    )
    result = next(response)

    # Assert
    assert result == "Local Response without deal"


def test_local_conv_ai_with_deal(
        mock_client
) -> None:
    # Arrange
    expected_response = "Local Response with deal"
    mock_client.return_value.chat.completions.create.return_value = iter(
        [
            MagicMock(
                choices=[
                    MagicMock(
                        delta=MagicMock(
                            content=expected_response
                        )
                    )
                ]
            )
        ]
    )

    # Act
    response = local_conv_ai(
        "Order: One salad",
        "Salad: $4", "Good morning",
        "Lunch special",
        api_key="dummy-key"
    )
    result = next(response)

    # Assert
    assert result == "Local Response with deal"
