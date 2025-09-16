import pytest
from month import run_monthly_review

# Mock the 'say' function to capture its output
class MockSay:
    def __init__(self):
        self.said_text = []
    def __call__(self, text, thread_ts):
        self.said_text.append(text)

@pytest.fixture
def mock_say():
    return MockSay()

def test_run_monthly_review_success(mocker, mock_say):
    # Arrange: Mock API responses and LLM response
    mock_target_data = {"monthly_detail": [{"month": "Nov", "target_budget_clean": 50000}]}
    mock_actual_data = {"monthly_data": [{"summary": {"total_spend_eur": 45000}, "details": []}]}
    mock_llm_response = mocker.Mock()
    mock_llm_response.text = "This is a great monthly review."

    mocker.patch("common.utils.query_api", side_effect=[mock_target_data, mock_actual_data])
    mocker.patch("common.config.gemini_model.generate_content", return_value=mock_llm_response)
    mocker.patch("common.utils.split_message_for_slack", return_value=["This is a great monthly review."])

    params = {'market': 'UK', 'month_abbr': 'Nov', 'month_full': 'November', 'year': 2025}
    thread_context_store = {}

    # Act: Run the function
    run_monthly_review(mock_say, "ts123", params, thread_context_store)

    # Assert: Check if the final message was sent
    assert "This is a great monthly review." in mock_say.said_text
    assert thread_context_store["ts123"]["type"] == "monthly_review"
    assert "raw_target_data" in thread_context_store["ts123"]

def test_run_monthly_review_api_error(mocker, mock_say):
    # Arrange: Mock API to return an error
    mocker.patch("common.utils.query_api", return_value={"error": "Connection failed"})
    params = {'market': 'UK', 'month_abbr': 'Nov', 'month_full': 'November', 'year': 2025}

    # Act
    run_monthly_review(mock_say, "ts123", params, {})

    # Assert
    assert "API Error: `Connection failed`" in mock_say.said_text[0]

def test_run_monthly_review_no_data(mocker, mock_say):
    # Arrange: Mock API to return no actuals data
    mock_target_data = {"monthly_detail": [{"month": "Nov", "target_budget_clean": 50000}]}
    mock_actual_data_empty = {"monthly_data": []}
    mocker.patch("common.utils.query_api", side_effect=[mock_target_data, mock_actual_data_empty])
    params = {'market': 'UK', 'month_abbr': 'Nov', 'month_full': 'November', 'year': 2025}

    # Act
    run_monthly_review(mock_say, "ts123", params, {})

    # Assert
    assert "No performance data found for UK November 2025." in mock_say.said_text[0]
