# ================================================
# FILE: month.py
# ================================================
import json
from common.config import gemini_model, logger, UNIFIED_API_URL
from common.utils import query_api, split_message_for_slack, format_currency

def create_prompt(user_query, market, month, year, target_budget_local, actual_data, is_full_review):
    return f"""
    You are Nova, a marketing analyst.
    {"Generate a comprehensive monthly performance review." if is_full_review else "Provide a concise, direct answer to the user's question."}
    **Data Context for {market.upper()} - {month.upper()} {year}:**
    {json.dumps({"Target Budget": format_currency(target_budget_local, market), "Actuals": actual_data}, indent=2)}
    **User's Request:** "{user_query if user_query else "A full monthly review."}"
    **Instructions:** Analyze the request and data. Formulate a clear, well-structured response using bold for key metrics. If data is missing, state it clearly.Present insights naturally without mentioning "based on the data provided".
    """

def run_monthly_review(say, thread_ts, params, thread_context_store, user_query=None):
    try:
        market, month_abbr, month_full, year = params['market'], params['month_abbr'], params['month_full'], params['year']
    except KeyError as e:
        say(f"A required parameter was missing: {e}.", thread_ts=thread_ts); return

    target_payload = {"source": "dashboard", "filters": {"market": market, "year": year}}
    target_data = query_api(UNIFIED_API_URL, target_payload, "Dashboard (Targets)")
    if "error" in target_data:
        say(f"API Error: `{target_data['error']}`", thread_ts=thread_ts); return
    
    target_budget_local = next((float(m.get("target_budget_clean", 0)) for m in target_data.get("monthly_detail", []) if str(m.get("month", "")).lower() == str(month_abbr).lower()), 0)
    
    actuals_payload = {"source": "influencer_analytics", "view": "monthly_breakdown", "filters": {"market": market, "month": month_full, "year": year}}
    actual_data_response = query_api(UNIFIED_API_URL, actuals_payload, "Influencer Analytics (Monthly)")
    if "error" in actual_data_response:
        say(f"API Error: `{actual_data_response['error']}`", thread_ts=thread_ts); return

    if not actual_data_response.get("monthly_data"):
        say(f"No performance data found for {market.upper()} {month_full} {year}.", thread_ts=thread_ts); return
    actual_data = actual_data_response["monthly_data"][0]

    try:
        is_full_review = not user_query or any(kw in user_query.lower() for kw in ["review", "summary", "analysis"])
        prompt = create_prompt(user_query, market, month_full, year, target_budget_local, actual_data, is_full_review)
        
        response = gemini_model.generate_content(prompt)
        ai_answer = response.text
        
        thread_context_store[thread_ts] = {
            'type': 'monthly_review', 'params': params,
            'raw_target_data': target_data, 'raw_actual_data': actual_data_response, 'bot_response': ai_answer
        }
        
        for chunk in split_message_for_slack(ai_answer): say(text=chunk, thread_ts=thread_ts)
    except Exception as e:
        logger.error(f"Error during AI review generation: {e}"); say(f"An error occurred generating the AI summary: {str(e)}", thread_ts=thread_ts)
    logger.success(f"Review completed for {market}-{month_full}-{year}")

def handle_thread_messages(event, say, client, context):
    user_message = event.get("text", "").strip()
    thread_ts = event["thread_ts"]
    logger.info(f"Handling follow-up for monthly_review in thread {thread_ts}")
    try:
        context_prompt = f"""
        You are a helpful marketing analyst assistant.
        **Current Context:** A Monthly Review for **{context['params']['market']}** for **{context['params']['month_full']} {context['params']['year']}**.
        **Available Data:** You have the full JSON data for this specific review: {json.dumps({'targets': context.get('raw_target_data', {}), 'actuals': context.get('raw_actual_data', {})})}
        
        **User's Follow-up:** "{user_message}"
        
        **Instructions:**
        1. Answer the user's question **ONLY** using the data provided in the "Available Data" section.
        2. If the user asks about a different month, market, or requires a comparison to data not present, you MUST state that you don't have that data in your current context. Example: "I can't answer that, as my current context is only for the June UK review. To compare with November, you would need to ask me to run a new analysis for November."
        3. Present your answer naturally, without phrases like "based on the provided data".
        """
        response = gemini_model.generate_content(context_prompt)
        ai_response = response.text
        for chunk in split_message_for_slack(ai_response): say(text=chunk, thread_ts=thread_ts)
    except Exception as e:
        logger.error(f"Error handling thread message in month.py: {e}"); say(text="Sorry, I encountered an error.", thread_ts=thread_ts)
