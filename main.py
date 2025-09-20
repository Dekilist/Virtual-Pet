# ============================
# main.py — App Runner with Optional RL/NLP
# ============================
# Sections:
# 1) Imports & configuration
# 2) App wiring (handlers, logging)
# 3) Tick loop with optional RL step
# 4) Boot
# Techniques:
# - Timer-driven GUI loop (Tkinter .after)
# - Optional integrations (RL/NLP) with safe defaults
# - JSONL session logging for later analysis

import json
import time
from pathlib import Path

from pet import VirtualPet
from interaction import PetApp

# --- Optional modules (safe fallbacks) ---
try:
    from nlp import predict_intent
except Exception:
    predict_intent = None

try:
    from rl import TabularAgent, ACTIONS_AGENT
except Exception:
    TabularAgent, ACTIONS_AGENT = None, []

try:
    from rewards import compute_reward
except Exception:
    compute_reward = None

# --- Configuration (centralize simple knobs here) ---
DATA_DIR = Path("data")
LOG_DIR = DATA_DIR / "logs"
for p in (DATA_DIR, LOG_DIR):
    p.mkdir(parents=True, exist_ok=True)

TICK_MS = 500           # tick interval
LOG_FLUSH_EVERY = 20    # flush log buffer frequency
USE_RL = False          # toggle when ready
USE_NLP = False         # reserved; current UI has no text box yet

def main():
    # 1) Pet & persistence
    pet = VirtualPet(name="Otto")
    pet.load_state()  # loads Otto_state.json if present

    # 2) Session logger
    session_path = LOG_DIR / f"session_{int(time.time())}.jsonl"
    logf = session_path.open("a", encoding="utf-8")
    log_count = 0

    def write_log(obj: dict):
        nonlocal log_count
        json.dump(obj, logf, ensure_ascii=False)
        logf.write("\n")
        log_count += 1
        if log_count % LOG_FLUSH_EVERY == 0:
            logf.flush()

    # 3) UI
    app = PetApp(pet, tick_ms=TICK_MS)

    # 4) Optional RL init
    agent = TabularAgent() if (USE_RL and TabularAgent is not None) else None
    last_state_tuple = pet.get_state_vector()
    # Keep a dict snapshot for reward computation
    last_state_dict = pet.get_state()

    # ---- Handlers (close over pet/app/logging/agent) ----
    def refresh_status():
        s = pet.get_state()
        # interaction.PetApp handles status labels internally
        # Here we just ensure state is up to date.
        return s

    # If you later add a text box for NLP, you can route user strings here.
    def handle_user_text(text: str):
        if not (USE_NLP and predict_intent):
            return
        label, conf = predict_intent(text)
        msg, warn = pet.perform_action(label)
        write_log({"t": "user_text", "text": text, "intent": label, "conf": conf,
                   "msg": msg, "err": warn, "state": pet.get_state()})
        pet.save_state()

    def on_tick():
        nonlocal last_state_tuple, last_state_dict

        # environment step
        prev_dict = pet.get_state()
        pet.tick()
        now_dict = pet.get_state()

        # optional RL step: agent chooses an action
        if agent is not None and compute_reward is not None:
            # agent observes transition from last_state -> current (time penalty + mood drift)
            r_env = compute_reward(last_state_dict, None, now_dict, user_event=None)
            agent.observe(pet.get_state_vector(), r_env, done=False)

            # agent acts
            a_idx, a = agent.select_action(pet.get_state_vector())
            # map agent action to environment effect
            if a == "self_sleep":
                msg, warn = pet.perform_action("sleep")
                now_dict = pet.get_state()
                write_log({"t": "agent_action", "a": a, "msg": msg, "err": warn, "state": now_dict})
            elif a.startswith("prompt_user_"):
                # For now, log the prompt; you can connect this to UI text later.
                write_log({"t": "agent_prompt", "a": a, "state": now_dict})
            # "self_idle" does nothing

            # compute reward for the agent’s action outcome
            after_dict = pet.get_state()
            r = compute_reward(now_dict, a, after_dict, user_event=None)
            agent.observe(pet.get_state_vector(), r, done=False)

        # log the tick and schedule next
        write_log({"t": "tick", "state": pet.get_state()})
        app.after(TICK_MS, on_tick)

        # update trackers
        last_state_tuple = pet.get_state_vector()
        last_state_dict = pet.get_state()

    # kick off tick loop
    app.after(TICK_MS, on_tick)
    app.run()

    # teardown
    pet.save_state()
    logf.close()

if __name__ == "__main__":
    main()
