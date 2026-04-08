import random
import math

from learner_storage import blank_question_state, clamp, normalize_question_state


CONFIDENCE_LABELS = [
    "I don't know",
    "I'm unsure",
    "I think so",
    "I know",
]

MASTERY_THRESHOLD = 0.7
READY_THRESHOLD = 0.45
RECENT_WINDOW = 10
RECOMMENDATION_WINDOW_SIZES = (8, 16, 24)
GRIT_DECAY_HALF_LIFE_MS = 7 * 24 * 60 * 60 * 1000
RECENT_REPEAT_WINDOW = 6
STICKY_REPEAT_LIMIT = 3
STICKY_REPEAT_COOLDOWN = 4


def question_state(progress: dict, question_id: int) -> dict:
    questions = progress.setdefault("questions", {})
    key = str(question_id)
    if key not in questions:
        questions[key] = blank_question_state()
    else:
        questions[key] = normalize_question_state(questions[key])
    return questions[key]


def is_mastered(state: dict, threshold: float = MASTERY_THRESHOLD) -> bool:
    return float(state.get("mastery", 0.0) or 0.0) >= threshold


def is_ready(state: dict, threshold: float = READY_THRESHOLD) -> bool:
    return float(state.get("mastery", 0.0) or 0.0) >= threshold


def current_user_grit(progress: dict, now_ms: int) -> float:
    stored_grit = max(0.0, float(progress.get("user_grit", 0.0) or 0.0))
    updated_at = max(0, int(progress.get("user_grit_updated_at", 0) or 0))
    if stored_grit <= 0.0 or updated_at <= 0 or now_ms <= updated_at:
        return stored_grit
    elapsed_ms = now_ms - updated_at
    decay_factor = math.pow(0.5, elapsed_ms / GRIT_DECAY_HALF_LIFE_MS)
    return max(0.0, stored_grit * decay_factor)


def update_user_grit(progress: dict, grit_delta: float, now_ms: int) -> float:
    decayed_grit = current_user_grit(progress, now_ms)
    new_grit = max(0.0, decayed_grit + grit_delta)
    progress["user_grit"] = new_grit
    progress["user_grit_updated_at"] = now_ms
    return new_grit


def select_checkpoint_question_ids(
    progress: dict,
    scope_question_ids: list[int],
    now_ms: int,
    count: int = 15,
) -> list[int]:
    if not scope_question_ids:
        return []
    if len(scope_question_ids) <= count:
        return list(scope_question_ids)

    unseen_question_ids: list[int] = []
    engaged_question_ids: list[int] = []
    for question_id in scope_question_ids:
        state = question_state(progress, question_id)
        attempts = int(state.get("attempts", 0) or 0)
        if attempts == 0:
            unseen_question_ids.append(question_id)
        else:
            engaged_question_ids.append(question_id)

    random.shuffle(unseen_question_ids)
    engaged_sorted = sorted(
        engaged_question_ids,
        key=lambda question_id: question_priority(
            question_state(progress, question_id),
            now_ms,
            question_id,
            [],
        ),
        reverse=True,
    )

    unseen_target = min(
        len(unseen_question_ids),
        max(4, count - max(3, round(count * 0.3))),
    )
    engaged_target = min(len(engaged_sorted), count - unseen_target)

    chosen = engaged_sorted[:engaged_target] + unseen_question_ids[:unseen_target]
    if len(chosen) < count:
        remaining_unseen = [question_id for question_id in unseen_question_ids if question_id not in chosen]
        remaining_engaged = [question_id for question_id in engaged_sorted if question_id not in chosen]
        filler = remaining_engaged + remaining_unseen
        chosen.extend(filler[: count - len(chosen)])

    return chosen[:count]


def question_priority_breakdown(
    state: dict,
    now_ms: int,
    question_id: int,
    recent_question_ids: list[int],
) -> dict:
    attempts = int(state.get("attempts", 0) or 0)
    due_at = int(state.get("due_at", 0) or 0)
    mastery = float(state.get("mastery", 0.0) or 0.0)
    knowledge = float(state.get("knowledge", 0.0) or 0.0)
    meta_learning = float(state.get("meta_learning", 0.0) or 0.0)
    difficulty = float(state.get("difficulty", 0.5) or 0.5)
    last_answer_ms = int(state.get("last_answer_ms", 0) or 0)
    consecutive_wrong = int(state.get("consecutive_wrong", 0) or 0)
    overdue_minutes = max(0.0, (now_ms - due_at) / 60_000) if due_at else 0.5
    base_priority = 0.85 - (0.15 * (question_id % 7) / 7) if attempts == 0 else (
        min(2.5, overdue_minutes * 0.08)
        + ((1.0 - mastery) * 1.4)
        + ((1.0 - knowledge) * 0.9)
        + (max(0.0, 0.55 - meta_learning) * 1.3)
        + (difficulty * 0.45)
        + (consecutive_wrong * 0.25)
        + (0.18 if last_answer_ms > 14_000 else 0.0)
    )
    recent_penalty = 0.0
    if recent_question_ids:
        if question_id == recent_question_ids[-1]:
            recent_penalty = -2.0
        elif question_id in recent_question_ids[-3:]:
            recent_penalty = -0.7
    wrong_confidence_bonus = 0.0
    last_confidence = None
    if bool(state.get("last_result_correct", False)) is False and attempts > 0:
        if state.get("confidence_history"):
            last_confidence = int(state["confidence_history"][-1])
            wrong_confidence_bonus = 0.75 if last_confidence >= 2 else 0.35
    total_priority = base_priority + recent_penalty + wrong_confidence_bonus
    return {
        "question_id": question_id,
        "attempts": attempts,
        "due_at": due_at,
        "due_in_seconds": round((due_at - now_ms) / 1000, 1) if due_at else None,
        "mastery": round(mastery, 4),
        "knowledge": round(knowledge, 4),
        "meta_learning": round(meta_learning, 4),
        "difficulty": round(difficulty, 4),
        "consecutive_wrong": consecutive_wrong,
        "last_result_correct": bool(state.get("last_result_correct", False)),
        "last_confidence": last_confidence,
        "is_in_recent_last_1": bool(recent_question_ids and question_id == recent_question_ids[-1]),
        "is_in_recent_last_3": question_id in recent_question_ids[-3:],
        "overdue_component": round(min(2.5, overdue_minutes * 0.08), 4) if attempts > 0 else 0.0,
        "mastery_component": round(((1.0 - mastery) * 1.4), 4) if attempts > 0 else 0.0,
        "knowledge_component": round(((1.0 - knowledge) * 0.9), 4) if attempts > 0 else 0.0,
        "meta_component": round((max(0.0, 0.55 - meta_learning) * 1.3), 4) if attempts > 0 else 0.0,
        "difficulty_component": round((difficulty * 0.45), 4) if attempts > 0 else 0.0,
        "wrong_streak_component": round((consecutive_wrong * 0.25), 4) if attempts > 0 else 0.0,
        "slow_answer_component": round((0.18 if last_answer_ms > 14_000 else 0.0), 4) if attempts > 0 else 0.0,
        "recent_penalty": round(recent_penalty, 4),
        "wrong_confidence_bonus": round(wrong_confidence_bonus, 4),
        "priority": round(total_priority, 4),
    }


def _choose_next_question_core(
    progress: dict,
    scope_question_ids: list[int],
    now_ms: int,
    recent_question_ids: list[int] | None = None,
    *,
    capture_diagnostics: bool = False,
):
    recent_question_ids = recent_question_ids or []
    diagnostics = {
        "scope_question_ids_input": list(scope_question_ids or []),
        "recent_question_ids": list(recent_question_ids),
        "sticky_ids": [],
        "unseen_question_ids": [],
        "engaged_question_ids": [],
        "candidate_question_ids": [],
        "candidate_count": 0,
        "selection_branch": "",
        "unseen_pick_probability": None,
        "random_roll": None,
        "selected_from_branch": None,
        "selected_next_question_id": None,
        "priority_table": [],
        "selection_failure_reason": "",
        "scope_was_empty": not bool(scope_question_ids),
        "candidate_was_empty": False,
        "all_candidates_filtered": False,
        "best_priority_was_none": False,
        "exception_during_selection": "",
    }
    if not scope_question_ids:
        diagnostics["selection_failure_reason"] = "empty_scope"
        return None, diagnostics

    try:
        unseen_question_ids: list[int] = []
        engaged_question_ids: list[int] = []
        sticky_ids = sticky_question_ids(recent_question_ids)
        diagnostics["sticky_ids"] = sorted(sticky_ids)

        for question_id in scope_question_ids:
            state = question_state(progress, question_id)
            attempts = int(state.get("attempts", 0) or 0)
            if attempts == 0 and question_id not in recent_question_ids[-3:]:
                unseen_question_ids.append(question_id)
            else:
                engaged_question_ids.append(question_id)

        if sticky_ids:
            unseen_question_ids = [question_id for question_id in unseen_question_ids if question_id not in sticky_ids]
            cooled_engaged = [question_id for question_id in engaged_question_ids if question_id not in sticky_ids]
            if cooled_engaged:
                engaged_question_ids = cooled_engaged
            elif len(recent_question_ids) >= STICKY_REPEAT_COOLDOWN:
                engaged_question_ids = [question_id for question_id in scope_question_ids if question_id not in recent_question_ids[-1:]]
            else:
                engaged_question_ids = [question_id for question_id in engaged_question_ids]

        diagnostics["unseen_question_ids"] = list(unseen_question_ids)
        diagnostics["engaged_question_ids"] = list(engaged_question_ids)

        if unseen_question_ids and not engaged_question_ids:
            selected = random.choice(unseen_question_ids)
            diagnostics["selection_branch"] = "unseen_only"
            diagnostics["selected_from_branch"] = "unseen_only"
            diagnostics["selected_next_question_id"] = selected
            return selected, diagnostics

        if unseen_question_ids and engaged_question_ids:
            unseen_ratio = len(unseen_question_ids) / max(1, len(scope_question_ids))
            unseen_pick_probability = clamp(0.35 + (0.40 * unseen_ratio), 0.35, 0.75)
            diagnostics["unseen_pick_probability"] = round(unseen_pick_probability, 4)
            random_roll = random.random()
            diagnostics["random_roll"] = round(random_roll, 4)
            if random_roll < unseen_pick_probability:
                selected = random.choice(unseen_question_ids)
                diagnostics["selection_branch"] = "mixed_random_unseen"
                diagnostics["selected_from_branch"] = "mixed_random_unseen"
                diagnostics["selected_next_question_id"] = selected
                return selected, diagnostics

        best_question_id = None
        best_priority = None
        candidate_question_ids = engaged_question_ids if engaged_question_ids else list(scope_question_ids)
        diagnostics["candidate_question_ids"] = list(candidate_question_ids)
        diagnostics["candidate_count"] = len(candidate_question_ids)
        diagnostics["selection_branch"] = "priority_pick"
        diagnostics["candidate_was_empty"] = not bool(candidate_question_ids)
        diagnostics["all_candidates_filtered"] = not bool(candidate_question_ids) and bool(scope_question_ids)

        for question_id in candidate_question_ids:
            state = question_state(progress, question_id)
            breakdown = question_priority_breakdown(
                state,
                now_ms,
                question_id,
                recent_question_ids,
            )
            diagnostics["priority_table"].append(breakdown)
            priority = breakdown["priority"]
            if best_priority is None or priority > best_priority:
                best_priority = priority
                best_question_id = question_id

        diagnostics["best_priority_was_none"] = best_priority is None
        diagnostics["selected_next_question_id"] = best_question_id
        if best_question_id is None:
            diagnostics["selection_failure_reason"] = "no_best_question_found"
        return best_question_id, diagnostics
    except Exception as exc:
        diagnostics["exception_during_selection"] = f"{type(exc).__name__}: {exc}"
        diagnostics["selection_failure_reason"] = "exception"
        return None, diagnostics


def choose_next_question(
    progress: dict,
    scope_question_ids: list[int],
    now_ms: int,
    recent_question_ids: list[int] | None = None,
) -> int | None:
    selected, _diagnostics = _choose_next_question_core(
        progress,
        scope_question_ids,
        now_ms,
        recent_question_ids,
        capture_diagnostics=False,
    )
    return selected


def choose_next_question_diagnostics(
    progress: dict,
    scope_question_ids: list[int],
    now_ms: int,
    recent_question_ids: list[int] | None = None,
) -> dict:
    selected, diagnostics = _choose_next_question_core(
        progress,
        scope_question_ids,
        now_ms,
        recent_question_ids,
        capture_diagnostics=True,
    )
    diagnostics["selected_next_question_id"] = selected
    return diagnostics


def update_after_response(
    progress: dict,
    question_id: int,
    is_correct: bool,
    confidence_value: int,
    response_ms: int,
    now_ms: int,
) -> dict:
    state = question_state(progress, question_id)
    previous_mastery = state["mastery"]
    previous_last_seen_at = int(state.get("last_seen_at", 0) or 0)
    previous_due_at = int(state.get("due_at", 0) or 0)
    previous_last_result_correct = bool(state.get("last_result_correct", False))
    previous_consecutive_wrong = int(state.get("consecutive_wrong", 0) or 0)
    previous_attempts = int(state.get("attempts", 0) or 0)

    state["attempts"] += 1
    state["last_seen_at"] = now_ms
    state["last_answer_ms"] = max(0, int(response_ms))
    state["updated_at"] = now_ms
    state["confidence_history"].append(int(confidence_value))
    state["confidence_history"] = state["confidence_history"][-50:]

    if is_correct:
        state["correct_attempts"] += 1
        state["consecutive_correct"] += 1
        state["consecutive_wrong"] = 0
    else:
        state["consecutive_wrong"] += 1
        state["consecutive_correct"] = 0

    confidence_scaled = clamp(confidence_value / 3.0)
    speed_factor = speed_score(response_ms)
    mismatch = confidence_scaled if not is_correct else abs(1.0 - confidence_scaled) * 0.3
    recall_bonus = spaced_recall_bonus(
        is_correct=is_correct,
        now_ms=now_ms,
        last_seen_at=previous_last_seen_at,
        due_at=previous_due_at,
    )

    recovered_question = bool(
        is_correct
        and previous_attempts > 0
        and (
            (not previous_last_result_correct)
            or previous_consecutive_wrong > 0
        )
    )

    if is_correct:
        knowledge_delta = (0.12 + (0.26 * confidence_scaled) + (0.05 * speed_factor)) * recall_bonus
        if confidence_value == 1 and previous_attempts > 0:
            knowledge_delta += 0.035 * recall_bonus
        if recovered_question:
            knowledge_delta += 0.06 * recall_bonus

        meta_delta = 0.11 if confidence_value >= 2 else 0.04
        if confidence_value == 0:
            meta_delta = 0.025
        elif confidence_value == 1 and previous_attempts > 0:
            meta_delta += 0.02
        if recovered_question:
            meta_delta += 0.025
        difficulty_delta = -0.04
        grit_delta = 0.04
    else:
        knowledge_delta = -0.07 - (0.07 * confidence_scaled)
        meta_delta = -0.10 if confidence_value >= 2 else 0.035
        difficulty_delta = 0.05
        grit_delta = 0.05 if confidence_value <= 1 else 0.02

    state["knowledge"] = clamp(state["knowledge"] + knowledge_delta)
    state["meta_learning"] = clamp(state["meta_learning"] + meta_delta)
    state["difficulty"] = clamp(state["difficulty"] + difficulty_delta)
    user_grit = update_user_grit(progress, grit_delta, now_ms)
    stability_delta = ((0.17 * recall_bonus) if is_correct else -0.06) + (0.04 * confidence_scaled)
    state["stability"] = clamp(
        state["stability"] + stability_delta,
        0.05,
        5.0,
    )
    knowledge_component = 0.6 * state["knowledge"]
    meta_component = 0.25 * state["meta_learning"]
    difficulty_component = 0.15 * (1.0 - state["difficulty"])
    state["mastery"] = clamp(
        knowledge_component
        + meta_component
        + difficulty_component
    )
    state["last_result_correct"] = bool(is_correct)

    next_due_at = now_ms + next_interval_ms(
        is_correct=is_correct,
        confidence_value=confidence_value,
        mastery=state["mastery"],
        stability=state["stability"],
        mismatch=mismatch,
    )
    if recovered_question:
        next_due_at = max(next_due_at, now_ms + 8 * 60_000)
    state["due_at"] = next_due_at

    return {
        "mastery_delta": round(state["mastery"] - previous_mastery, 4),
        "previous_mastery": round(previous_mastery, 4),
        "knowledge": state["knowledge"],
        "knowledge_delta": round(knowledge_delta, 4),
        "grit": user_grit,
        "grit_delta": round(grit_delta, 4),
        "meta_learning": state["meta_learning"],
        "meta_delta": round(meta_delta, 4),
        "mastery": state["mastery"],
        "difficulty": state["difficulty"],
        "difficulty_delta": round(difficulty_delta, 4),
        "stability": state["stability"],
        "stability_delta": round(stability_delta, 4),
        "confidence_scaled": round(confidence_scaled, 4),
        "speed_factor": round(speed_factor, 4),
        "mismatch": round(mismatch, 4),
        "recall_bonus": round(recall_bonus, 4),
        "knowledge_component": round(knowledge_component, 4),
        "meta_component": round(meta_component, 4),
        "difficulty_component": round(difficulty_component, 4),
        "due_at": state["due_at"],
        "next_interval_ms": max(0, int(state["due_at"] - now_ms)),
        "recovered_question": recovered_question,
        "first_attempt_ever": previous_attempts == 0,
        "previous_attempts": previous_attempts,
    }


def next_interval_ms(
    *,
    is_correct: bool,
    confidence_value: int,
    mastery: float,
    stability: float,
    mismatch: float,
) -> int:
    if not is_correct:
        if confidence_value >= 2:
            return 90_000
        return 180_000

    if confidence_value == 0:
        return 240_000
    if confidence_value == 1:
        return 420_000

    base_minutes = 30 if confidence_value == 2 else 90
    scale = 1.0 + mastery + (stability * 0.3) - (mismatch * 0.4)
    minutes = max(10.0, base_minutes * scale)
    return int(minutes * 60_000)


def question_priority(
    state: dict,
    now_ms: int,
    question_id: int,
    recent_question_ids: list[int],
) -> float:
    attempts = int(state.get("attempts", 0) or 0)
    due_at = int(state.get("due_at", 0) or 0)
    mastery = float(state.get("mastery", 0.0) or 0.0)
    knowledge = float(state.get("knowledge", 0.0) or 0.0)
    meta_learning = float(state.get("meta_learning", 0.0) or 0.0)
    difficulty = float(state.get("difficulty", 0.5) or 0.5)
    last_answer_ms = int(state.get("last_answer_ms", 0) or 0)
    consecutive_wrong = int(state.get("consecutive_wrong", 0) or 0)

    if attempts == 0:
        base_priority = 0.85 - (0.15 * (question_id % 7) / 7)
    else:
        overdue_minutes = max(0.0, (now_ms - due_at) / 60_000) if due_at else 0.5
        base_priority = (
            min(2.5, overdue_minutes * 0.08)
            + ((1.0 - mastery) * 1.4)
            + ((1.0 - knowledge) * 0.9)
            + (max(0.0, 0.55 - meta_learning) * 1.3)
            + (difficulty * 0.45)
            + (consecutive_wrong * 0.25)
            + (0.18 if last_answer_ms > 14_000 else 0.0)
        )

    if recent_question_ids:
        if question_id == recent_question_ids[-1]:
            base_priority -= 2.0
        elif question_id in recent_question_ids[-3:]:
            base_priority -= 0.7

    if bool(state.get("last_result_correct", False)) is False and attempts > 0:
        if state.get("confidence_history"):
            last_confidence = int(state["confidence_history"][-1])
            if last_confidence >= 2:
                base_priority += 0.75
            else:
                base_priority += 0.35

    return base_priority


def sticky_question_ids(
    recent_question_ids: list[int],
    *,
    repeat_window: int = RECENT_REPEAT_WINDOW,
    repeat_limit: int = STICKY_REPEAT_LIMIT,
) -> set[int]:
    if not recent_question_ids:
        return set()
    recent_window = recent_question_ids[-repeat_window:]
    repeats: dict[int, int] = {}
    for question_id in recent_window:
        repeats[question_id] = repeats.get(question_id, 0) + 1
    return {
        question_id
        for question_id, repeat_count in repeats.items()
        if repeat_count >= repeat_limit
    }


def recommendation_for_session(
    interactions: list[dict],
    progress: dict,
    scope_question_ids: list[int],
    now_ms: int,
) -> dict:
    def window_stats(window: list[dict]) -> dict:
        return {
            "size": len(window),
            "avg_mastery_gain": sum(item.get("mastery_delta", 0.0) for item in window) / len(window),
            "accuracy": sum(1 for item in window if item.get("is_correct")) / len(window),
            "avg_meta": sum(item.get("meta_learning", 0.0) for item in window) / len(window),
            "avg_response_ms": sum(item.get("response_ms", 0) for item in window) / len(window),
            "avg_grit": sum(item.get("grit", 0.0) for item in window) / len(window),
        }

    def take_break_signal(stats: dict) -> bool:
        return (
            stats["avg_response_ms"] > 20_000
            and (
                stats["accuracy"] < 0.72
                or stats["avg_grit"] < 0.78
                or stats["avg_mastery_gain"] < 0.02
            )
        )

    def diminishing_returns_signal(stats: dict) -> bool:
        return (
            stats["avg_mastery_gain"] < 0.015
            and (
                stats["accuracy"] < 0.62
                or stats["avg_meta"] < 0.46
            )
        )

    def strong_low_yield_signal(stats: dict) -> bool:
        return (
            stats["avg_mastery_gain"] < 0.01
            and stats["accuracy"] < 0.5
            and stats["avg_meta"] < 0.4
        )

    if not scope_question_ids:
        return {"kind": "empty", "message": "", "end_session": True}

    mastered_count = 0
    due_now_count = 0
    for question_id in scope_question_ids:
        state = question_state(progress, question_id)
        if is_mastered(state):
            mastered_count += 1
        if not is_mastered(state) or int(state.get("due_at", 0) or 0) <= now_ms:
            due_now_count += 1

    if mastered_count == len(scope_question_ids):
        return {
            "kind": "all_learned",
            "message": "You've learned everything currently due in this area.",
            "end_session": True,
        }

    if len(interactions) < RECOMMENDATION_WINDOW_SIZES[0]:
        return {"kind": "", "message": "", "end_session": False}

    recent_windows = [
        window_stats(interactions[-window_size:])
        for window_size in RECOMMENDATION_WINDOW_SIZES
        if len(interactions) >= window_size
    ]
    latest_window = recent_windows[0]
    take_break_hits = sum(1 for stats in recent_windows if take_break_signal(stats))
    diminishing_hits = sum(1 for stats in recent_windows if diminishing_returns_signal(stats))
    strong_low_yield_hits = sum(1 for stats in recent_windows if strong_low_yield_signal(stats))

    if (
        len(interactions) >= RECOMMENDATION_WINDOW_SIZES[-1]
        and len(recent_windows) == len(RECOMMENDATION_WINDOW_SIZES)
        and strong_low_yield_hits == len(RECOMMENDATION_WINDOW_SIZES)
        and latest_window["avg_mastery_gain"] < 0.012
    ):
        return {
            "kind": "come_back_later",
            "message": (
                "You seem to be hitting sustained diminishing returns. "
                "This is a good place to pause and come back later, when the next session "
                "is more likely to pay off."
            ),
            "end_session": True,
        }

    if diminishing_hits >= 2:
        return {
            "kind": "diminishing_returns",
            "message": "You may be hitting diminishing returns. A short reset or small change of pace might help.",
            "end_session": False,
        }

    if take_break_hits >= 2:
        return {
            "kind": "take_break",
            "message": (
                "You may be hitting diminishing returns. You can keep going, "
                "but a short break might help the next stretch feel easier."
            ),
            "end_session": False,
        }

    if due_now_count <= max(1, len(scope_question_ids) // 10):
        return {
            "kind": "mostly_due_later",
            "message": (
                "Most of this area is due later. Consider learning other modules before "
                "coming back to this one for more optimal memory recall."
            ),
            "end_session": False,
        }

    return {"kind": "", "message": "", "end_session": False}


def spaced_recall_bonus(
    *,
    is_correct: bool,
    now_ms: int,
    last_seen_at: int,
    due_at: int,
) -> float:
    if not is_correct:
        return 1.0
    if last_seen_at <= 0:
        return 0.9
    if due_at <= last_seen_at:
        return 1.0

    elapsed_ms = max(0, now_ms - last_seen_at)
    scheduled_ms = max(60_000, due_at - last_seen_at)
    recall_ratio = elapsed_ms / scheduled_ms

    if recall_ratio < 0.5:
        return 0.9
    if recall_ratio < 1.0:
        return 1.05
    if recall_ratio < 1.5:
        return 1.25
    return 1.45


def speed_score(response_ms: int) -> float:
    if response_ms <= 0:
        return 0.5
    if response_ms <= 6_000:
        return 1.0
    if response_ms <= 12_000:
        return 0.7
    if response_ms <= 20_000:
        return 0.45
    return 0.2
