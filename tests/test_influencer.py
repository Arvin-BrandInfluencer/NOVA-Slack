import pytest
from influencer import run_influencer_analysis

class MockSay:
    def __init__(self):
        self.said_text = []
    def __call__(self, text, thread_ts):
        self.said_text.append(text)

@pytest.fixture
def mock_say():
    return MockSay()

def test_run_influencer_analysis_success(mocker, mock_say):
    # Arrange
    mock_api_data = {
        "campaigns": [
            {"market": "UK", "total_budget_clean": 850, "currency": "GBP", "actual_conversions_clean": 10, "ctr": 0.05}
        ]
    }
    mock_llm_response = mocker.Mock()
    mock_llm_response.text = "Analysis of InfluencerX."
    mocker.patch("common.utils.query_api", return_value=mock_api_data)
    mocker.patch("common.config.gemini_model.generate_content", return_value=mock_llm_response)
    mocker.patch("common.utils.split_message_for_slack", return_value=["Analysis of InfluencerX."])
    
    params = {'influencer_name': 'InfluencerX', 'year': 2025}
    thread_context = {}

    # Act
    run_influencer_analysis(mock_say, "ts123", params, thread_context)

    # Assert
    assert "Analysis of InfluencerX." in mock_say.said_text
    assert thread_context["ts123"]["type"] == "influencer_analysis"
    # 850 GBP / 0.85 rate = 1000 EUR. 1000 EUR / 10 conversions = 100 CAC
    assert thread_context["ts123"]["raw_api_data"] == mock_api_data
    
def test_run_influencer_analysis_no_campaigns(mocker, mock_say):
    # Arrange
    mocker.patch("common.utils.query_api", return_value={"campaigns": []})
    params = {'influencer_name': 'GhostInfluencer'}

    # Act
    run_influencer_analysis(mock_say, "ts123", params, {})

    # Assert
    assert "No campaigns found for 'GhostInfluencer'" in mock_say.said_text[0]
