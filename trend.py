# ================================================
# FILE: trend.py
# ================================================
import json
from common.config import gemini_model, logger, UNIFIED_API_URL
from common.utils import query_api, split_message_for_slack

def create_leaderboard_reports(all_influencers, filters):
    reports = {}
    filter_str = " | ".join(f"{k.title()}: {v}" for k, v in filters.items() if v)
    
    # Leaderboard by Conversions
    by_conversions = sorted(all_influencers, key=lambda x: x.get('total_conversions', 0), reverse=True)[:15]
    conv_table = f"```\n🏆 TOP 15 BY CONVERSIONS ({filter_str})\n"
    conv_table += "Rank | Name                 | Conversions | CAC (€) | Spend (€)\n"
    conv_table += "-"*65 + "\n"
    for i, inf in enumerate(by_conversions, 1):
        conv_table += f"{i:2d} | {inf.get('influencer_name', 'N/A')[:20]:<20} | {int(inf.get('total_conversions', 0)):>11} | {inf.get('effective_cac_eur', 0):>7.2f} | {inf.get('total_spend_eur', 0):>9.2f}\n"
    reports['conversions'] = conv_table + "```"

    # Leaderboard by CAC
    with_conv = [x for x in all_influencers if x.get('total_conversions', 0) > 0 and x.get('effective_cac_eur', 0) > 0]
    by_cac = sorted(with_conv, key=lambda x: x.get('effective_cac_eur', float('inf')))[:15]
    cac_table = f"```\n💰 TOP 15 BY CAC (Lowest Cost) ({filter_str})\n"
    cac_table += "Rank | Name                 | CAC (€)   | Conversions\n"
    cac_table += "-"*55 + "\n"
    for i, inf in enumerate(by_cac, 1):
        cac_table += f"{i:2d} | {inf.get('influencer_name', 'N/A')[:20]:<20} | {inf.get('effective_cac_eur', 0):>7.2f} | {int(inf.get('total_conversions', 0)):>11}\n"
    reports['cac'] = cac_table + "```"
    
    return reports

def run_influencer_trend(say, thread_ts, params, thread_context_store, user_query=None):
    filters = {k: v for k, v in params.items() if k in ['market', 'year', 'month_full', 'tier']}
    if 'month_full' in filters:
        filters['month'] = filters.pop('month_full')
        
    payload = {"source": "influencer_analytics", "view": "discovery_tiers", "filters": filters}
    data = query_api(UNIFIED_API_URL, payload, "Influencer Trends")
    
    if "error" in data:
        say(f"{data['error']} Please try again shortly.", thread_ts=thread_ts)
        return

    # Combine all tiers into a single list for leaderboard generation.
    gold_tier = data.get("gold", [])
    silver_tier = data.get("silver", [])
    bronze_tier = data.get("bronze", [])
    all_influencers = gold_tier + silver_tier + bronze_tier

    if not all_influencers:
        filter_str = " | ".join(f"{k.title()}: {v}" for k, v in filters.items() if v)
        say(f"I couldn't find any trend data for the filters: `{filter_str}`. You might want to try a broader search.", thread_ts=thread_ts)
        return
        
    try:
        logger.info("Generating full trend leaderboards.")
        leaderboards = create_leaderboard_reports(all_influencers, filters)
        say(f"Of course! Here are the influencer trend leaderboards for your requested filters.", thread_ts=thread_ts)
        for report_text in leaderboards.values():
            say(text=report_text, thread_ts=thread_ts)
        
        thread_context_store[thread_ts] = {'type': 'influencer_trend', 'params': params, 'raw_api_data': data, 'bot_response': "Leaderboard reports were generated."}
        logger.success(f"Trend analysis completed for filters: {filters}")
    except Exception as e:
        logger.error(f"An unexpected error occurred in trend.py: {e}", exc_info=True)
        say(f"I'm sorry, a system error occurred while preparing your trend report.", thread_ts=thread_ts)

def handle_thread_messages(event, say, client, context):
    user_message = event.get("text", "").strip()
    thread_ts = event["thread_ts"]
    logger.info(f"Handling follow-up for influencer_trend in thread {thread_ts}")
    try:
        context_prompt = f"""
        You are a helpful marketing analyst assistant.
        **Current Context:** An Influencer Trend report for the filters: **{json.dumps(context.get('params', {}))}**.
        **Available Data:** You have the full JSON data for this specific trend report: {json.dumps(context.get('raw_api_data', {}))}
        
        **User's Follow-up Message:** "{user_message}"
        
        **Your Task - Follow these steps in order:**
        1.  **Analyze and Answer:** Answer the user's question by analyzing the **Available Data** for the current trend report.
        2.  **State Missing Data:** If the question asks for something not in the data, or requires comparing to data outside of the current filters, you MUST state that you don't have that data in your current context.
        3. **Natural Language:** Frame your response naturally. Avoid phrases like "Based on the data,".
        """
        response = gemini_model.generate_content(context_prompt)
        ai_response = response.text.strip()
        
        for chunk in split_message_for_slack(ai_response): 
            say(text=chunk, thread_ts=thread_ts)
    except Exception as e:
        logger.error(f"Error handling thread message in trend.py: {e}"); say(text="My apologies, I had trouble processing that follow-up.", thread_ts=thread_ts)
