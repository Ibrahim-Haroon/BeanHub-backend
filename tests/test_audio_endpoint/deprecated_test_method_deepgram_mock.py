# TODO: Add back to test_views and test_urls if revert to using deepgram (currently using google cloud)

self.mock_deepgram_file = patch('builtins.open', new_callable=mock_open, read_data='fake_deepgram_api_key')
self.mock_deepgram_file.start()

self.mock_deepgram_class = patch(speech_to_text_path + '.Deepgram')
mock_deepgram_instance = MagicMock()
self.mock_deepgram_class.start().return_value = mock_deepgram_instance
nova_response = {
    'results': {
        'channels': [
            {'alternatives': [{'transcript': 'this is a test'}]}
        ]
    }
}
mock_deepgram_instance.transcription.sync_prerecorded.return_value = nova_response


@patch(speech_to_text_path="" + '.Deepgram')
def test_patch_sends_successful_response_when_user_accepts_deal_and_deal_is_coffee_item(
        self, mock_deepgram
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

    mock_deepgram_instance = MagicMock()
    mock_deepgram.return_value = mock_deepgram_instance
    nova_response = {
        'results': {
            'channels': [
                {'alternatives': [{'transcript': 'yes'}]}
            ]
        }
    }
    mock_deepgram_instance.transcription.sync_prerecorded.return_value = nova_response

    # Act
    response = self.client.patch('/audio_endpoint/', data, content_type='application/json')

    # Assert
    self.assertEqual(response.status_code, 200)
    self.assertTrue('file_path' in response.json())
    self.assertTrue('unique_id' in response.json())
    self.assertTrue('json_order' in response.json())


@patch(speech_to_text_path="" + '.Deepgram')
def test_patch_sends_400_error_response_when_user_deal_invalid(
        self, mock_deepgram
) -> None:
    # Arrange
    data = {
        "file_path": "test.wav",
        "unique_id": "test",
    }

    mock_deepgram_instance = MagicMock()
    mock_deepgram.return_value = mock_deepgram_instance
    nova_response = {
        'results': {
            'channels': [
                {'alternatives': [{'transcript': 'yes'}]}
            ]
        }
    }
    mock_deepgram_instance.transcription.sync_prerecorded.return_value = nova_response

    # Act
    response = self.client.patch('/audio_endpoint/', data, content_type='application/json')

    # Assert
    self.assertEqual(response.status_code, 400)
    self.assertEqual(response.json(), {'error': 'item_type not found'})