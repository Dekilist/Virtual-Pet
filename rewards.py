# ============================
# rewards.py — Reward Shaping
# ============================
# Sections:
# 1) Mood ranking
# 2) compute_reward(prev_state, agent_action, next_state, user_event)
# Technique: Pure functional reward; small shaping helps stable learning.

def _mood_rank(m: str) -> int:
    order = {"Emo": 0, "bored": 1, "Happy Happy Happy": 2, "KIMOJI!!": 3}
    return order.get(m, 1)

def compute_reward(prev_state: dict,
                   agent_action: str | None,
                   next_state: dict,
                   user_event: str | None) -> float:
    # 1) mood delta (primary objective)
    r = 2.0 * (_mood_rank(next_state["mood"]) - _mood_rank(prev_state["mood"]))

    # 2) small time penalty to encourage purposeful actions
    r -= 0.2

    # 3) engagement credit for prompts (if/when you add UI prompts)
    if agent_action and agent_action.startswith("prompt_user_"):
        r += 1.0 if (user_event and user_event != "idle") else -1.0

    # clip reward to stabilize training
    return max(-3.0, min(3.0, r))
