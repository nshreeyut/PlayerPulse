"""
LangChain Churn Analyst Agent
==============================
This is the AI analyst — the brain behind the chatbot.

WHAT IS A LANGCHAIN AGENT?
---------------------------
An agent is an LLM that can USE TOOLS to answer questions.
Instead of relying only on training data, it can:
  - Look up real player data from your parquet file
  - Run your actual trained ML model
  - Read SHAP values to explain predictions
  - Then summarize everything in plain English

The LLM decides WHICH tool to call and WHEN based on the user's question.
You define the tools. The LLM figures out how to use them.

YOUR TOOLS:
-----------
  get_player_data(player_id, platform)
    → Returns the player's features + churn prediction
    → Used for: "What's Player X's risk score?"

  explain_prediction(player_id, platform)
    → Reads SHAP values and formats a plain-English explanation
    → Used for: "Why is Player X predicted to churn?"

  get_dataset_context()
    → Returns overall dataset statistics
    → Used for: "What's the overall churn rate?" / "What does engagement score mean?"

  suggest_retention_strategy(player_id, platform)
    → Maps the player's top SHAP risk factors to actionable interventions
    → Used for: "How do we keep Player X engaged?"

HOW TOOL CALLING WORKS:
------------------------
1. User asks: "Why is hikaru at risk?"
2. LLM sees: I have a tool called `explain_prediction` — I should call it
3. LLM calls: explain_prediction(player_id="12345", platform="opendota")
4. Tool runs: fetches SHAP values, formats them as text
5. LLM receives: the tool's output
6. LLM generates: a plain-English summary using the real data

LEARN MORE:
  LangChain agents:    https://python.langchain.com/docs/concepts/agents/
  Tool calling:        https://python.langchain.com/docs/concepts/tool_calling/
  @tool decorator:     https://python.langchain.com/docs/concepts/tools/
  AgentExecutor:       https://python.langchain.com/docs/concepts/agent_executor/
"""

from langchain_core.tools import tool
from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

from api.services.data_service import get_player, get_dataset_summary
from api.services.model_service import predict_churn
from api.services.shap_service import get_player_shap, FEATURE_LABELS
from api.config import get_llm

# ---------------------------------------------------------
# SYSTEM PROMPT
# ---------------------------------------------------------
# This tells the LLM who it is and how to behave.
# Be specific — vague prompts produce vague answers.
# The more context you give here, the better the responses will be.
SYSTEM_PROMPT = """You are a game analytics expert specializing in player churn prediction.

You have access to a machine learning system that:
  - Predicts whether players are about to stop playing their games (churn probability 0–1)
  - Explains WHY using SHAP feature importance values
  - Covers multiple platforms: OpenDota (Dota 2) and Steam

Your audience includes game designers, business stakeholders, and data science students.

Guidelines:
- Always use your tools to look up real data before answering questions about specific players
- Explain technical terms in plain English (e.g., explain what "SHAP value" means if asked)
- Be specific — reference actual numbers from the player's data
- Suggest concrete, actionable retention strategies when asked
- Keep responses clear and concise — avoid unnecessary jargon
- If player_context is provided in the conversation, you already have their data loaded
"""

# ---------------------------------------------------------
# TOOL DEFINITIONS
# ---------------------------------------------------------
# @tool turns a Python function into a LangChain tool.
# The DOCSTRING becomes the tool's description — the LLM reads this to decide
# when and why to call each tool. Write clear, specific docstrings.

@tool
def get_player_data(player_id: str, platform: str) -> dict:
    """
    Fetch a player's features and churn prediction from the ML system.
    Use this when the user asks about a specific player's risk level or statistics.

    Args:
        player_id: The player's ID (e.g., "12345" for OpenDota)
        platform:  The gaming platform key (opendota, steam)

    Returns a dict with player features and the churn prediction.

    TODO: Implement this tool.
    Steps:
      1. Call get_player(player_id, platform)
         If None: return {"error": f"Player {player_id} not found on {platform}"}
      2. Call predict_churn(features)
      3. Return {"player_id": ..., "platform": ..., "features": ..., "prediction": ...}
    """
    raise NotImplementedError("TODO: implement get_player_data tool")


@tool
def explain_prediction(player_id: str, platform: str) -> str:
    """
    Get a plain-English explanation of WHY the model predicts churn for this player.
    Use this when the user asks why a player is at risk or what factors are driving their score.

    Returns a formatted string listing the top features influencing the prediction,
    with human-readable descriptions and their directional impact.

    TODO: Implement this tool.
    Steps:
      1. shap_values = get_player_shap(player_id, platform)
         If None: return "No SHAP explanation available for this player."
      2. Take the top 5 features (already sorted by impact)
      3. For each, build a sentence like:
         "• Days since their last game (+0.42): strongly increases churn risk"
         "• Games played in the last 7 days (-0.18): slightly reduces churn risk"
      4. Join into a readable string and return it
    """
    raise NotImplementedError("TODO: implement explain_prediction tool")


@tool
def get_dataset_context() -> dict:
    """
    Get overall statistics about the game churn dataset.
    Use this when the user asks general questions about churn rates,
    what platforms are covered, or how features like 'engagement score' are defined.

    TODO: Call get_dataset_summary() and return the result.
    """
    raise NotImplementedError("TODO: implement get_dataset_context tool")


@tool
def suggest_retention_strategy(player_id: str, platform: str) -> str:
    """
    Generate personalized retention recommendations for a specific at-risk player.
    Use this when the user asks how to retain a player or what actions to take.

    Maps the player's top SHAP risk factors to specific, actionable interventions.

    TODO: Implement this tool.
    Steps:
      1. Get SHAP values with get_player_shap(player_id, platform)
         If None: return a generic set of recommendations
      2. Look at the top 3 positive SHAP features (the ones driving churn)
      3. Map them to interventions using this logic:
           "days_since_last_game" high   → "Send a 're-engagement' notification or email"
           "games_7d" / "games_trend"    → "Offer a time-limited reward for logging in this week"
           "win_rate_7d" low             → "Adjust matchmaking — the player may be frustrated by losses"
           "unique_peers_30d" low        → "Promote social/team features; suggest finding regular teammates"
           "max_gap_days_30d" high       → "The player already takes long breaks — consider a streak reward system"
      4. Return a bulleted list of 2–3 specific recommendations
    """
    raise NotImplementedError("TODO: implement suggest_retention_strategy tool")


# ---------------------------------------------------------
# AGENT SETUP
# ---------------------------------------------------------

def get_agent() -> AgentExecutor:
    """
    Build and return the LangChain agent with all tools wired up.

    create_tool_calling_agent uses the LLM's native function-calling capability
    (OpenAI function calling) to select and invoke the right tool.

    TODO: Implement this function.
    Steps:
      1. llm = get_llm(streaming=True)

      2. tools = [get_player_data, explain_prediction, get_dataset_context, suggest_retention_strategy]

      3. prompt = ChatPromptTemplate.from_messages([
             ("system", SYSTEM_PROMPT),
             MessagesPlaceholder("chat_history", optional=True),
             ("human", "{input}"),
             MessagesPlaceholder("agent_scratchpad"),  # required by the agent framework
         ])

      4. agent = create_tool_calling_agent(llm, tools, prompt)

      5. return AgentExecutor(agent=agent, tools=tools, verbose=True, max_iterations=5)

    NOTE: verbose=True prints tool calls to your terminal during development —
    very useful for debugging. Set it to False in production.
    """
    raise NotImplementedError("TODO: implement get_agent()")
