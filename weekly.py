# ================================================
# FILE: weekly.py
# ================================================
import json
from common.config import gemini_model, logger, UNIFIED_API_URL
from common.utils import query_api, split_message_for_slack

def create_range_prompt(user_query, market, start_date, end_date, api_data):
    return f"""
    You are Nova, a marketing analyst. Generate a concise performance review for the specified date range.
    **Data Context for {market.upper()} from {start_date} to {end_date}:**
    {json.dumps(api_data, indent=2)}
    **User's Request:** "{user_query}"
    **Instructions:** Analyze the data. Provide a clear performance summary using bold for key metrics. Identify the top-performing influencer. If data is empty, state that clearly. Present insights naturally.
    """

def create_week_number_prompt(user_query, market, week_number, year, api_data):
    return f"""
    You are Nova, a marketing analyst. Generate a concise performance review for the specified week number.
    **Data Context for {market.upper()} for Week {week_number}, {year}:**
    {json.dumps(api_data, indent=2)}
    **User's Request:** "{user_query}"
    **Instructions:** Analyze the data. Provide a clear performance summary using bold for key metrics. Identify the top-performing influencer for that week. If data is empty, state that clearly. Present insights naturally.
    """

def run_weekly_review_by_range(say, thread_ts, params, thread_context_store, user_query=None):
    try:
        market, start_date, end_date = params['market'], params['start_date'], params['end_date']
        year = params.get('year', 2025)
    except KeyError as e:
        say(f"A required parameter ({e}) was missing for the date range review.", thread_ts=thread_ts); return

    payload = {"source": "influencer_analytics", "view": "custom_range_breakdown", "filters": {"market": market, "year": year, "date_from": start_date, "date_to": end_date}}
    api_data = query_api(UNIFIED_API_URL, payload, "Date Range Breakdown")
    if "error" in api_data:
        say(f"API Error: `{api_data['error']}`", thread_ts=thread_ts); return
    
    if not api_data.get("summary") or not api_data.get("details"):
        say(f"No performance data found for {market.upper()} between {start_date} and {end_date}.", thread_ts=thread_ts); return

    try:
        prompt = create_range_prompt(user_query, market, start_date, end_date, api_data)
        response = gemini_model.generate_content(prompt)
        ai_answer = response.text
        
        thread_context_store[thread_ts] = {'type': 'weekly_review_by_range', 'params': params, 'raw_api_data': api_data, 'bot_response': ai_answer}
        
        for chunk in split_message_for_slack(ai_answer): say(text=chunk, thread_ts=thread_ts)
    except Exception as e:
        logger.error(f"Error during AI date range review generation: {e}"); say(f"An error occurred generating the AI summary: {str(e)}", thread_ts=thread_ts)
    logger.success(f"Date range review completed for {market} from {start_date} to {end_date}")

def run_weekly_review_by_number(say, thread_ts, params, thread_context_store, user_query=None):
    try:
        market, week_number = params['market'], params['week_number']
        year = params.get('year', 2025)
    except KeyError as e:
        say(f"A required parameter ({e}) was missing for the week number review.", thread_ts=thread_ts); return

    payload = {"source": "influencer_analytics", "view": "weekly_breakdown_by_number", "filters": {"market": market, "year": year, "week_number": week_number}}
    api_data = query_api(UNIFIED_API_URL, payload, "Week Number Breakdown")
    if "error" in api_data:
        say(f"API Error: `{api_data['error']}`", thread_ts=thread_ts); return

    if not api_data.get("summary") or not api_data.get("details"):
        say(f"No performance data found for {market.upper()} in week {week_number} of {year}.", thread_ts=thread_ts); return

    try:
        prompt = create_week_number_prompt(user_query, market, week_number, year, api_data)
        response = gemini_model.generate_content(prompt)
        ai_answer = response.text

        thread_context_store[thread_ts] = {'type': 'weekly_review_by_number', 'params': params, 'raw_api_data': api_data, 'bot_response': ai_answer}

        for chunk in split_message_for_slack(ai_answer): say(text=chunk, thread_ts=thread_ts)
    except Exception as e:
        logger.error(f"Error during AI week number review generation: {e}"); say(f"An error occurred generating the AI summary: {str(e)}", thread_ts=thread_ts)
    logger.success(f"Week number review completed for {market}, week {week_number} of {year}")

def handle_thread_messages(event, say, client, context):
    user_message = event.get("text", "").strip()
    thread_ts = event["thread_ts"]
    context_type = context.get("type", "unknown")
    params = context.get('params', {})
    
    logger.info(f"Handling follow-up for {context_type} in thread {thread_ts}")

    if context_type == 'weekly_review_by_range':
        context_description = f"A performance review for **{params.get('market')}** for the period **{params.get('start_date')} to {params.get('end_date')}**."
    elif context_type == 'weekly_review_by_number':
        context_description = f"A performance review for **{params.get('market')}** for **Week {params.get('week_number')}, {params.get('year')}**."
    else:
        say("I'm sorry, I've lost the specific context for this weekly review.", thread_ts=thread_ts)
        return

    try:
        context_prompt = f"""
        You are a helpful marketing analyst assistant.
        **Current Context:** {context_description}
        **Available Data:** You have the full JSON data for this specific review: {json.dumps(context.get('raw_api_data', {}))}
        
        **User's Follow-up:** "{user_message}"
        
        **Instructions:**
        1. Answer the user's question **ONLY** using the data provided in the "Available Data" section.
        2. If the user asks about a different time period, market, or requires a comparison to data not present, you MUST state that you don't have that data in your current context.
        3. Present your answer naturally.
        """
        response = gemini_model.generate_content(context_prompt)
        for chunk in split_message_for_slack(response.text): say(text=chunk, thread_ts=thread_ts)
    except Exception as e:
        logger.error(f"Error handling thread message in weekly.py: {e}"); say(text="Sorry, I encountered an error.", thread_ts=thread_ts)
