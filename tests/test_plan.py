import pytest
from plan import run_strategic_plan
from io import BytesIO

class MockSay:
    def __init__(self):
        self.said_text = []
    def __call__(self, text, thread_ts):
        self.said_text.append(text)

class MockClient:
    def __init__(self):
        self.upload_called = False
        self.filename = None
    def files_upload_v2(self, channel, file, filename, title, initial_comment, thread_ts):
        self.upload_called = True
        self.filename = filename
        assert isinstance(file, bytes)

@pytest.fixture
def mock_say():
    return MockSay()

@pytest.fixture
def mock_client():
    return MockClient()

def test_run_strategic_plan_success(mocker, mock_say, mock_client):
    # Arrange
    mock_target = {"monthly_detail": [{"month": "dec", "target_budget_clean": 100000}]}
    mock_actuals = {"monthly_data": [{"summary": {"total_spend_eur": 17000}, "details": [{"influencer_name": "booked_inf"}]}]}
    # Mocking tier data to match expected structure from discovery_tiers view
    mock_tier_data = {
        "gold": [{"influencer_name": "gold_inf", "total_spend_eur": 500, "campaigns": 2}],
        "silver": [{"influencer_name": "silver_inf", "total_spend_eur": 300, "campaigns": 1}],
        "bronze": []
    }
    
    mock_llm_response = mocker.Mock()
    mock_llm_response.text = "Strategic Insights here."

    mocker.patch("common.utils.query_api", side_effect=[mock_target, mock_actuals, mock_tier_data, mock_tier_data, mock_tier_data])
    mocker.patch("common.config.gemini_model.generate_content", return_value=mock_llm_response)
    mocker.patch("plan.create_excel_report", return_value=BytesIO(b"excel data"))

    params = {'market': 'France', 'month_abbr': 'Dec', 'month_full': 'December', 'year': 2025}
    event = {'channel': 'C123'}
    thread_context = {}

    # Act
    run_strategic_plan(mock_client, mock_say, event, "ts123", params, thread_context)

    # Assert
    assert mock_say.said_text[0].startswith("📊 Creating a strategic plan")
    assert mock_client.upload_called
    assert "Strategic_Plan_France_December_2025.xlsx" in mock_client.filename
    assert any("Strategic Insights here." in s for s in mock_say.said_text)
    assert "strategic_plan" in thread_context["ts123"]["type"]

def test_run_strategic_plan_budget_overspent(mocker, mock_say, mock_client):
    # Arrange (convert_eur_to_local for France is 1:1, so 15000 EUR spend > 10000 target)
    mock_target = {"monthly_detail": [{"month": "dec", "target_budget_clean": 10000}]}
    mock_actuals = {"monthly_data": [{"summary": {"total_spend_eur": 15000}, "details": []}]}
    mocker.patch("common.utils.query_api", side_effect=[mock_target, mock_actuals])
    params = {'market': 'France', 'month_abbr': 'Dec', 'month_full': 'December', 'year': 2025}

    # Act
    run_strategic_plan(mock_client, mock_say, {}, "ts123", params, {})

    # Assert
    assert "budget for this period has already been fully utilized" in mock_say.said_text[1]
