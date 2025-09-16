import pytest
from weekly import run_weekly_review_by_range, run_weekly_review_by_number

class MockSay:
    def __init__(self):
        self.said_text = []
    def __call__(self, text, thread_ts):
        self.said_text.append(text)

@pytest.fixture
def mock_say():
    return MockSay()

def test_run_weekly_review_by_range_success(mocker, mock_say):
    # Arrange
    mock_api_data = {"summary": {"total_spend_eur": 1000}, "details": [{"influencer_name": "test_inf"}]}
    mock_llm_response = mocker.Mock()
    mock_llm_response.text = "Weekly range review looks good."
    
    mocker.patch("common.utils.query_api", return_value=mock_api_data)
    mocker.patch("common.config.gemini_model.generate_content", return_value=mock_llm_response)
    mocker.patch("common.utils.split_message_for_slack", return_value=["Weekly range review looks good."])
    
    params = {'market': 'UK', 'start_date': '2025-01-01', 'end_date': '2025-01-07'}
    thread_context = {}

    # Act
    run_weekly_review_by_range(mock_say, "ts123", params, thread_context)

    # Assert
    assert "Weekly range review looks good." in mock_say.said_text
    assert thread_context["ts123"]["type"] == "weekly_review_by_range"
    assert thread_context["ts123"]['params']['start_date'] == '2025-01-01'

def test_run_weekly_review_by_number_no_data(mocker, mock_say):
    # Arrange
    mocker.patch("common.utils.query_api", return_value={"summary": {}, "details": []})
    params = {'market': 'France', 'week_number': 53, 'year': 2025}
    
    # Act
    run_weekly_review_by_number(mock_say, "ts123", params, {})
    
    # Assert
    assert "No performance data found for France in week 53 of 2025." in mock_say.said_text[0]
