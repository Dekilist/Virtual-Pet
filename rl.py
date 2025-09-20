# ============================
# rl.py — Tabular Agent (Q-learning baseline)
# ============================
# Sections:
# 1) Action space
# 2) TabularAgent with ε-greedy & incremental Q-update
# Technique: Minimal dependency, easy to swap for DQN later.

import random
from collections import defaultdict
from typing import Tuple, List

# 1) Agent action space (expandable)
ACTIONS_AGENT: List[str] = [
    "self_idle",
    "self_sleep",
    "prompt_user_play",
    "prompt_user_feed",
    "prompt_user_bath",
]

class TabularAgent:
    """
    Minimal Q-learning agent on discretized states (tuples).
    API:
      - select_action(state_tuple) -> (action_index, action_str)
      - observe(next_state_tuple, reward, done=False)
    """
    def __init__(self, actions: List[str] | None = None, eps: float = 0.2, alpha: float = 0.3, gamma: float = 0.95):
        self.actions = actions or ACTIONS_AGENT
        self.eps = eps
        self.alpha = alpha
        self.gamma = gamma
        self.Q = defaultdict(lambda: [0.0] * len(self.actions))
        self._last: Tuple[tuple, int] | None = None

    def select_action(self, state_tuple: tuple) -> Tuple[int, str]:
        # ε-greedy exploration
        if random.random() < self.eps:
            a_idx = random.randrange(len(self.actions))
        else:
            qs = self.Q[state_tuple]
            a_idx = max(range(len(qs)), key=lambda i: qs[i])
        self._last = (state_tuple, a_idx)
        return a_idx, self.actions[a_idx]

    def observe(self, next_state_tuple: tuple, reward: float, done: bool = False):
        if self._last is None:
            return
        s, a_idx = self._last
        qsa = self.Q[s][a_idx]
        future = 0.0 if done else max(self.Q[next_state_tuple])
        target = reward + self.gamma * future
        self.Q[s][a_idx] = qsa + self.alpha * (target - qsa)
        if done:
            self._last = None
