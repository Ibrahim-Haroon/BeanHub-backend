from src.ai_integration.openai_text_api import openai_text_api
import pytest
from mock import MagicMock, patch
from typing import Final

script_path: Final[str] = 'scripts.ai_integration.openai_text_api'


@pytest.fixture
def mock_openai(mocker):
    return mocker.patch(script_path + '.OpenAI')


def test_openai_text_api(mock_openai):
    # Arrange
    mock_completion = MagicMock()
    mock_completion.choices[0].message.content = "mocked_response"
    mock_openai.return_value.chat.completions.create.return_value = mock_completion

    # Act
    with patch(script_path + '.OpenAI', return_value=mock_openai.return_value):
        result = openai_text_api(prompt="Test prompt", model_behavior="System message", api_key="foo_key")

    # Assert
    assert result == "mocked_response", f"expected response to be \"mocked response\" but got {result}"
    mock_openai.return_value.chat.completions.create.assert_called_once_with(
        messages=[
            {"role": "system", "content": "System message"},
            {"role": "user", "content": "Test prompt"}
        ],
        model="gpt-4-1106-preview"
    )