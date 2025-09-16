import pytest
from trend import run_influencer_trend

class MockSay:
    def __init__(self):
        self.said_text = []
    def __call__(self, text, thread_ts=None):
        self.said_text.append(text)

@pytest.fixture
def mock_say():
    return MockSay()

def test_run_influencer_trend_success(mocker, mock_say):
    # Arrange
    mock_api_data = {
        "gold": [{"influencer_name": "gold_star", "total_conversions": 100, "effective_cac_eur": 50.0, "total_spend_eur": 5000}],
        "silver": [{"influencer_name": "silver_medal", "total_conversions": 50, "effective_cac_eur": 40.0, "total_spend_eur": 2000}],
        "bronze": []
    }
    mocker.patch("common.utils.query_api", return_value=mock_api_data)
    params = {'market': 'UK', 'year': 2025}
    thread_context = {}

    # Act
    run_influencer_trend(mock_say, "ts123", params, thread_context)

    # Assert
    assert len(mock_say.said_text) == 3 # Intro + conversions table + CAC table
    assert "🏆 TOP 15 BY CONVERSIONS" in mock_say.said_text[1]
    assert "💰 TOP 15 BY CAC" in mock_say.said_text[2]
    assert "gold_star" in mock_say.said_text[1]
    assert "silver_medal" in mock_say.said_text[2]
    assert thread_context["ts123"]["type"] == "influencer_trend"

def test_run_influencer_trend_no_data(mocker, mock_say):
    # Arrange
    mocker.patch("common.utils.query_api", return_value={"gold": [], "silver": [], "bronze": []})
    params = {'market': 'Atlantis', 'year': 2025}

    # Act
    run_influencer_trend(mock_say, "ts123", params, {})

    # Assert
    assert "I couldn't find any trend data" in mock_say.said_text[0]
    assert "Market: Atlantis" in mock_say.said_text[0]
