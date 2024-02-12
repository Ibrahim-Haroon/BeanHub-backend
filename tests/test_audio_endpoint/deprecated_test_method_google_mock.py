

@patch(speech_to_text_path + '.speech.Recognizer')
def test_patch_sends_successful_response_when_user_accepts_deal_and_nothing_else_and_deal_is_coffee_item(
        self, mock_google_transcribe
) -> None:
    # Arrange
    data = {
        "file_path": "test.wav",
        "unique_id": "test",
    }

    mock_deal_data = (
        '{'
        '    "deal_accepted": "foo",'
        '    "deal_object": {'
        '        "CoffeeItem": {'
        '            "item_name": "black coffee",'
        '            "quantity": [1],'
        '            "price": [2.0],'
        '            "cart_action": "insertion"'
        '        }'
        '    }'
        '}'
    )

    self.mock_deal_client.get = MagicMock(return_value=mock_deal_data)

    mock_google_instance = MagicMock()
    mock_google_transcribe.return_value = mock_google_instance
    mock_google_transcription = "yes"
    mock_google_instance.recognize_google.return_value = mock_google_transcription

    # Act
    response = self.client.patch('/audio_endpoint/', data, content_type='application/json')

    # Assert
    self.assertEqual(response.status_code, 200)
    self.assertTrue('file_path' in response.json())
    self.assertTrue('unique_id' in response.json())
    self.assertTrue('json_order' in response.json())


@patch(speech_to_text_path + '.speech.Recognizer')
def test_that_patch_returns_200_success_response_when_customer_accepts_deal_and_orders_another_item_in_same_request(
        self, mock_google_transcribe
) -> None:
    # Arrange
    data = {
        "file_path": "test.wav",
        "unique_id": "test",
    }

    mock_deal_data = (
        '{'
        '    "deal_accepted": "foo",'
        '    "deal_object": {'
        '        "CoffeeItem": {'
        '            "item_name": "latte",'
        '            "quantity": [1],'
        '            "price": [2.0],'
        '            "cart_action": "insertion"'
        '        }'
        '    }'
        '}'
    )

    mock_google_instance = MagicMock()
    mock_google_transcribe.return_value = mock_google_instance
    mock_google_transcription = "yes and one latte please"
    mock_google_instance.recognize_google.return_value = mock_google_transcription

    self.mock_deal_client.get = MagicMock(side_effect=[mock_deal_data, json.dumps(False)])

    # Act
    response = self.client.patch('/audio_endpoint/', data, content_type='application/json')

    # Assert
    self.assertEqual(response.status_code, 200)
    self.assertTrue('file_path' in response.json())
    self.assertTrue('unique_id' in response.json())
    self.assertTrue('json_order' in response.json())


@patch(speech_to_text_path + '.speech.Recognizer')
def test_patch_sends_400_error_response_when_user_deal_invalid(
        self, mock_google_transcribe
) -> None:
    # Arrange
    data = {
        "file_path": "test.wav",
        "unique_id": "test",
    }

    mock_google_instance = MagicMock()
    mock_google_transcribe.return_value = mock_google_instance
    mock_google_transcription = "yes"
    mock_google_instance.recognize_google.return_value = mock_google_transcription

    # Act
    response = self.client.patch('/audio_endpoint/', data, content_type='application/json')

    # Assert
    self.assertEqual(response.status_code, 400)
    self.assertEqual(response.json(), {'error': 'item_type not found'})


@patch(speech_to_text_path + '.speech.Recognizer')
def test_that_deal_cache_appends_deal_accepted_once_user_accepts_deal(
        self, mock_google_transcribe
) -> None:
    # Arrange
    data = {
        "file_path": "test.wav",
        "unique_id": "test",
    }

    mock_google_instance = MagicMock()
    mock_google_transcribe.return_value = mock_google_instance
    mock_google_transcription = "yes"
    mock_google_instance.recognize_google.return_value = mock_google_transcription

    # Act
    self.client.patch('/audio_endpoint/', data, content_type='application/json')

    # Assert
    assert bool(json.loads(self.mock_deal_client.get(f'deal_accepted_{data["unique_id"]}'))) is True, \
        "deal_accepted not appended to cache"