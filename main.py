import asyncio
import hashlib
import html
import importlib
import inspect
import json
import random
import sys
import traceback
from dataclasses import dataclass, field
from urllib.parse import quote

from pyscript import fetch, web
from pyodide.ffi import create_proxy
from js import console, document, window


APP_CONFIG_PATH = "./quiz.json"
QUIZ_INDEX_PATH = ""
QUESTION_PATH_TEMPLATE = ""
QUIZ_CONFIG_PATH = ""
QUIZ_ID = ""
DRAFT_STORAGE_KEY = "quizurself_quiz_draft_v1"
QUESTION_METADATA_COLLAPSED_KEY = "quizurself_question_metadata_collapsed_v1"
QNA_METADATA_VISIBLE_KEY = "quizurself_qna_metadata_visible_v1"
ADVANCED_OPTIONS_ENABLED_KEY = "quizurself_advanced_options_enabled_v1"
ADVANCED_OPTIONS_AREAS_KEY = "quizurself_advanced_options_areas_v1"
ADVANCED_OPTIONS_SHOW_TIMER_KEY = "quizurself_advanced_options_show_timer_v1"
ADVANCED_OPTIONS_LEARNER_MODE_KEY = "quizurself_advanced_options_learner_mode_v1"
PREFETCH_COUNT = 2
QUIZ_CURSOR_HIDE_DELAY_SECONDS = 2.0
TWEMOJI_BASE_URL = "https://cdn.jsdelivr.net/gh/jdecked/twemoji@15.1.0/assets/svg"
PASSPORT_AVATARS = [
    {"id": "cat_smile", "emoji": "😺", "codepoint": "1f63a", "label": "Sunny Cat"},
    {"id": "cat_grin", "emoji": "😸", "codepoint": "1f638", "label": "Grin Cat"},
    {"id": "cat_joy", "emoji": "😹", "codepoint": "1f639", "label": "Giggle Cat"},
    {"id": "cat_heart", "emoji": "😻", "codepoint": "1f63b", "label": "Heart Cat"},
    {"id": "cat_wry", "emoji": "😼", "codepoint": "1f63c", "label": "Wry Cat"},
    {"id": "cat_kiss", "emoji": "😽", "codepoint": "1f63d", "label": "Kiss Cat"},
    {"id": "cat_scream", "emoji": "🙀", "codepoint": "1f640", "label": "Surprised Cat"},
    {"id": "cat_cry", "emoji": "😿", "codepoint": "1f63f", "label": "Misty Cat"},
    {"id": "cat_pout", "emoji": "😾", "codepoint": "1f63e", "label": "Pout Cat"},
]
PASSPORT_AVATAR_BACKGROUNDS = [
    {"id": "peach", "label": "Peach", "color": "#ffd9cc"},
    {"id": "butter", "label": "Butter", "color": "#fff0b8"},
    {"id": "mint", "label": "Mint", "color": "#d8f3dc"},
    {"id": "sky", "label": "Sky", "color": "#d6ecff"},
    {"id": "lavender", "label": "Lavender", "color": "#e7dcff"},
    {"id": "blush", "label": "Blush", "color": "#ffd9e8"},
]

KNOWLEDGE_AREAS: list[str] = []
SYLLABUS_CATALOG: dict[str, dict[str, str]] = {}
APP_CONFIG: dict = {}
FEATURE_FLAGS: dict[str, bool] = {}
QUESTION_PANEL_FIELDS: list[dict[str, str]] = []
RESULTS_METADATA_FIELDS: list[dict[str, str]] = []
DEFAULT_QUESTION_TYPE = "single_select_4orless"


@dataclass
class Question:
    question_id: int
    text: str
    image: str | None
    question_type: str
    options: list[dict[str, str]]
    correct_answers: list[str]
    answer: str | list[str]
    metadata: dict[str, str] = field(default_factory=dict)


hero = web.page["hero-section"]
status_box = web.page["status-box"]
status_text = web.page["status-text"]
app_title = web.page["app-title"]
app_subtitle = web.page["app-subtitle"]
page_loader_text = web.page["page-loader-text"]

home_screen = web.page["home-screen"]
quiz_screen = web.page["quiz-screen"]
learner_confirm_screen = web.page["learner-confirm-screen"]
learner_passport_screen = web.page["learner-passport-screen"]
learner_generator_screen = web.page["learner-generator-screen"]
learner_hub_screen = web.page["learner-hub-screen"]
quit_confirm_screen = web.page["quit-confirm-screen"]
learner_summary_screen = web.page["learner-summary-screen"]
results_screen = web.page["results-screen"]

count_input = web.page["question-count"]
total_question_count = web.page["total-question-count"]
total_question_count_label = web.page["total-question-count-label"]
advanced_options_toggle = web.page["advanced-options-toggle"]
advanced_options = web.page["advanced-options"]
knowledge_area_checkboxes = web.page["knowledge-area-checkboxes"]
show_timer_toggle = web.page["show-timer-toggle"]
learner_mode_toggle = web.page["learner-mode-toggle"]

start_button = web.page["start-quiz-btn"]
previous_button = web.page["previous-btn"]
next_button = web.page["next-btn"]
quit_attempt_button = web.page["quit-attempt-btn"]
copy_question_link = web.page["copy-question-link"]
quiz_help_link = web.page["quiz-help-link"]
learner_end_session_button = web.page["learner-end-session-btn"]
retry_same_button = web.page["retry-same-btn"]
retry_new_button = web.page["retry-new-btn"]
back_home_button = web.page["back-home-btn"]
confirm_quit_button = web.page["confirm-quit-btn"]
cancel_quit_button = web.page["cancel-quit-btn"]
quit_confirm_kicker = web.page["quit-confirm-kicker"]
quit_confirm_title = web.page["quit-confirm-title"]
quit_confirm_copy = web.page["quit-confirm-copy"]
learner_confirm_yes_button = web.page["learner-confirm-yes-btn"]
learner_confirm_no_button = web.page["learner-confirm-no-btn"]
learner_progress_file = web.page["learner-progress-file"]
learner_use_current_passport_button = web.page["learner-use-current-passport-btn"]
learner_start_fresh_button = web.page["learner-start-fresh-btn"]
learner_username_input = web.page["learner-username-input"]
learner_avatar_options = web.page["learner-avatar-options"]
learner_avatar_bg_options = web.page["learner-avatar-bg-options"]
learner_generator_avatar_frame = web.page["learner-generator-avatar-frame"]
learner_generator_avatar_preview = web.page["learner-generator-avatar-preview"]
learner_generator_avatar_name = web.page["learner-generator-avatar-name"]
learner_generate_passport_button = web.page["learner-generate-passport-btn"]
learner_generator_back_button = web.page["learner-generator-back-btn"]
learner_download_progress_button = web.page["learner-download-progress-btn"]
learner_hub_back_home_button = web.page["learner-hub-back-home-btn"]
learner_summary_download_button = web.page["learner-summary-download-btn"]
learner_summary_continue_button = web.page["learner-summary-continue-btn"]
learner_summary_return_hub_button = web.page["learner-summary-return-hub-btn"]
learner_summary_home_button = web.page["learner-summary-home-btn"]
learner_guidance_dismiss_button = web.page["learner-guidance-dismiss-btn"]

progress_text = web.page["quiz-progress-text"]
score_chip = web.page["quiz-score-chip"]
quiz_progress = web.page["quiz-progress"]
progress_bar = web.page["quiz-progress-bar"]
question_id_text = web.page["question-id"]
question_text = web.page["question-text"]
question_type_card = web.page["question-type-card"]
question_metadata_panel = web.page["question-metadata-panel"]
question_metadata_toggle = web.page["question-metadata-toggle"]
question_image_wrap = web.page["question-image-wrap"]
question_image = web.page["question-image"]
options_host = web.page["question-options"]
multi_select_indicator = web.page["multi-select-indicator"]
learner_feedback = web.page["learner-feedback"]
learner_confidence_panel = web.page["learner-confidence-panel"]
learner_confidence_buttons = web.page["learner-confidence-buttons"]

results_title = web.page["results-title"]
results_subtitle = web.page["results-subtitle"]
score_value = web.page["score-value"]
score_detail = web.page["score-detail"]
stats_host = web.page["results-stats-grid"]

stats_tab_button = web.page["stats-tab-btn"]
qna_tab_button = web.page["qna-tab-btn"]
stats_tab = web.page["stats-tab"]
qna_tab = web.page["qna-tab"]
lightbox = web.page["image-lightbox"]
lightbox_image = web.page["lightbox-image"]
lightbox_close_button = web.page["lightbox-close-btn"]
session_timer = web.page["session-timer"]
toast_notification = web.page["toast-notification"]
page_loader = web.page["page-loader"]
advanced_options_bar = document.querySelector(".home-mode-bar")
quiz_footer = web.page["quiz-footer"]
quiz_nav_actions = web.page["quiz-nav-actions"]
learner_hub_progress = web.page["learner-hub-progress"]
learner_hub_overall = web.page["learner-hub-overall"]
learner_hub_avatar_frame = web.page["learner-hub-avatar-frame"]
learner_hub_avatar = web.page["learner-hub-avatar"]
learner_hub_title = web.page["learner-hub-title"]
learner_hub_copy = web.page["learner-hub-copy"]
learner_import_status = web.page["learner-import-status"]
learner_summary_title = web.page["learner-summary-title"]
learner_summary_subtitle = web.page["learner-summary-subtitle"]
learner_summary_positive_section = web.page["learner-summary-positive-section"]
learner_summary_positive_list = web.page["learner-summary-positive-list"]
learner_summary_next_step_section = web.page["learner-summary-next-step-section"]
learner_summary_next_step_title = web.page["learner-summary-next-step-title"]
learner_summary_next_step_message = web.page["learner-summary-next-step-message"]
learner_summary_value = web.page["learner-summary-value"]
learner_summary_detail = web.page["learner-summary-detail"]
learner_summary_stats_grid = web.page["learner-summary-stats-grid"]
learner_guidance_modal = web.page["learner-guidance-modal"]
learner_guidance_title = web.page["learner-guidance-title"]
learner_guidance_message = web.page["learner-guidance-message"]
quiz_help_modal = web.page["quiz-help-modal"]
quiz_help_title = web.page["quiz-help-title"]
quiz_help_message = web.page["quiz-help-message"]
quiz_help_dismiss_button = web.page["quiz-help-dismiss-btn"]
learner_debug_panel = web.page["learner-debug-panel"]
learner_debug_content = web.page["learner-debug-content"]
learner_debug_download_button = web.page["learner-debug-download-btn"]
learner_debug_copy_button = web.page["learner-debug-copy-btn"]
learner_debug_popout_button = web.page["learner-debug-popout-btn"]
learner_debug_hide_button = web.page["learner-debug-hide-btn"]
learner_debug_reopen_button = web.page["learner-debug-reopen-btn"]


quiz_index: dict = {}
question_cache: dict[int, Question] = {}
question_load_tasks: dict[int, asyncio.Task] = {}
question_bank_index: dict[int, dict[str, str]] = {}
question_ids_by_area: dict[str, list[int]] = {}
session_question_ids: list[int] = []
answers: dict[int, str] = {}
current_index = 0
proxies = []
results_rows_data: list[dict] = []
results_filter = "all"
results_show_metadata = False
advanced_options_enabled = False
selected_knowledge_areas: list[str] = list(KNOWLEDGE_AREAS)
show_timer_enabled = False
learner_mode_enabled = False
session_advanced_options_enabled = False
session_selected_knowledge_areas: list[str] = []
session_show_timer = False
session_learner_mode = False
session_timer_started_at_ms: float | None = None
session_elapsed_seconds = 0
question_metadata_collapsed = False
toast_clear_task: asyncio.Task | None = None
timer_task: asyncio.Task | None = None
learner_debug_task: asyncio.Task | None = None
cursor_hide_task: asyncio.Task | None = None
learner_prefetch_task: asyncio.Task | None = None
learner_modules_loaded = False
learner_storage_module = None
learner_scheduler_module = None
learner_mode_module = None
learner_progress: dict = {}
learner_session_active = False
learner_scope_name = ""
learner_scope_question_ids: list[int] = []
learner_checkpoint_question_ids: list[int] = []
learner_checkpoint_baseline_average_mastery = 0.0
learner_checkpoint_attempted_question_ids: set[int] = set()
learner_checkpoint_initial_ready_question_ids: set[int] = set()
learner_checkpoint_initial_baseline_question_ids: set[int] = set()
learner_checkpoint_initial_mastered_question_ids: set[int] = set()
learner_checkpoint_display_mode_for_session = "ready"
learner_interactions: list[dict] = []
learner_answer_locked = False
learner_selected_answer: str | None = None
learner_question_started_at_ms: float | None = None
learner_summary_payload: dict = {}
learner_pending_next_question_id: int | None = None
learner_prefetched_question_id: int | None = None
learner_pending_recommendation: dict | None = None
learner_session_end_context: dict = {}
learner_guidance_visible = False
learner_guidance_kind = ""
learner_guidance_shown_kinds: set[str] = set()
learner_review_mode = False
learner_review_return_state: dict | None = None
quit_confirm_mode = "quiz"
learner_selected_confidence: int | None = None
multi_select_focus_key: str | None = None
learner_debug_popup = None
learner_debug_panel_visible = False
learner_debug_unlocked = False
learner_debug_unlock_buffer = ""
learner_debug_previous_values: dict[str, str] = {}
learner_debug_event_log: list[dict] = []
learner_debug_report_text = ""
learner_debug_checkpoint_completion_captured = False
learner_debug_session_end_details: dict = {}
learner_generator_avatar_id = "cat_smile"
learner_generator_avatar_bg_id = "peach"


def learner_checkpoint_target(scope_question_count: int) -> int:
    return min(15, scope_question_count)


def learner_checkpoint_progress(checkpoint_question_ids: list[int]) -> int:
    if learner_scheduler_module is None:
        return 0
    ready_count = 0
    for question_id in checkpoint_question_ids:
        state = learner_scheduler_module.question_state(learner_progress, question_id)
        if learner_scheduler_module.is_ready(state):
            ready_count += 1
    return ready_count


def learner_checkpoint_average_mastery(checkpoint_question_ids: list[int]) -> float:
    if learner_scheduler_module is None or not checkpoint_question_ids:
        return 0.0
    mastery_sum = 0.0
    for question_id in checkpoint_question_ids:
        state = learner_scheduler_module.question_state(learner_progress, question_id)
        mastery_sum += float(state.get("mastery", 0.0) or 0.0)
    return mastery_sum / len(checkpoint_question_ids)


def learner_checkpoint_initial_state_sets(
    checkpoint_question_ids: list[int],
) -> tuple[set[int], set[int], set[int]]:
    if learner_scheduler_module is None or not checkpoint_question_ids:
        return set(), set(), set()

    initial_ready: set[int] = set()
    initial_baseline: set[int] = set()
    initial_mastered: set[int] = set()
    for question_id in checkpoint_question_ids:
        state = learner_scheduler_module.question_state(learner_progress, question_id)
        mastery = float(state.get("mastery", 0.0) or 0.0)
        if learner_scheduler_module.is_ready(state):
            initial_ready.add(question_id)
        if mastery >= 0.4:
            initial_baseline.add(question_id)
        if learner_scheduler_module.is_mastered(state):
            initial_mastered.add(question_id)
    return initial_ready, initial_baseline, initial_mastered


def learner_checkpoint_counts() -> dict[str, int]:
    if learner_scheduler_module is None or not learner_checkpoint_question_ids:
        return {
            "total": 0,
            "attempted": 0,
            "ready": 0,
            "mastery_04": 0,
            "mastered": 0,
            "ready_needed": 0,
            "baseline_needed": 0,
            "mastered_needed": 0,
            "newly_ready": 0,
            "newly_baseline": 0,
            "newly_mastered": 0,
            "mastery_04_not_ready": 0,
        }

    total = len(learner_checkpoint_question_ids)
    attempted = 0
    ready = 0
    mastery_04 = 0
    mastered = 0

    for question_id in learner_checkpoint_question_ids:
        state = learner_scheduler_module.question_state(learner_progress, question_id)
        mastery = float(state.get("mastery", 0.0) or 0.0)
        if question_id in learner_checkpoint_attempted_question_ids:
            attempted += 1
        if learner_scheduler_module.is_ready(state):
            ready += 1
        if learner_scheduler_module.is_mastered(state):
            mastered += 1
        if mastery >= 0.4:
            mastery_04 += 1

    ready_needed = max(0, total - len(learner_checkpoint_initial_ready_question_ids))
    baseline_needed = max(0, total - len(learner_checkpoint_initial_baseline_question_ids))
    mastered_needed = max(0, total - len(learner_checkpoint_initial_mastered_question_ids))
    newly_ready = sum(
        1
        for question_id in learner_checkpoint_question_ids
        if question_id not in learner_checkpoint_initial_ready_question_ids
        and learner_scheduler_module.is_ready(
            learner_scheduler_module.question_state(learner_progress, question_id)
        )
    )
    newly_baseline = sum(
        1
        for question_id in learner_checkpoint_question_ids
        if question_id not in learner_checkpoint_initial_baseline_question_ids
        and float(
            learner_scheduler_module.question_state(learner_progress, question_id).get("mastery", 0.0) or 0.0
        ) >= 0.4
    )
    newly_mastered = sum(
        1
        for question_id in learner_checkpoint_question_ids
        if question_id not in learner_checkpoint_initial_mastered_question_ids
        and learner_scheduler_module.is_mastered(
            learner_scheduler_module.question_state(learner_progress, question_id)
        )
    )
    mastery_04_not_ready = max(0, mastery_04 - ready)
    return {
        "total": total,
        "attempted": attempted,
        "ready": ready,
        "mastery_04": mastery_04,
        "mastered": mastered,
        "ready_needed": ready_needed,
        "baseline_needed": baseline_needed,
        "mastered_needed": mastered_needed,
        "newly_ready": newly_ready,
        "newly_baseline": newly_baseline,
        "newly_mastered": newly_mastered,
        "mastery_04_not_ready": mastery_04_not_ready,
    }


def learner_checkpoint_display_progress() -> tuple[float, dict[str, int]]:
    counts = learner_checkpoint_counts()
    total = counts["total"]
    if total <= 0:
        return 0.0, counts

    required_units = (
        (0.2 * total)
        + (0.6 * counts["baseline_needed"])
        + (1.0 * counts["ready_needed"])
    )
    if required_units <= 0:
        return 0.0, counts

    display_units = (
        (0.2 * counts["attempted"])
        + (0.6 * counts["newly_baseline"])
        + (1.0 * counts["newly_ready"])
    )
    return min(1.0, display_units / required_units), counts


def learner_checkpoint_status() -> tuple[float, int]:
    target = len(learner_checkpoint_question_ids) or learner_checkpoint_target(len(learner_scope_question_ids))
    progress = learner_checkpoint_progress(learner_checkpoint_question_ids)
    return progress, target


def learner_checkpoint_progress_chip(counts: dict[str, int], target: int) -> str:
    ready_needed = counts.get("ready_needed", 0)
    baseline_needed = counts.get("baseline_needed", 0)
    newly_ready = counts.get("newly_ready", 0)
    newly_baseline = counts.get("newly_baseline", 0)
    attempted = counts.get("attempted", 0)

    if ready_needed > 0:
        ready_text = f"{newly_ready}/{ready_needed} newly ready"
    else:
        ready_text = "ready done at start"

    if baseline_needed > 0:
        baseline_text = f"{newly_baseline}/{baseline_needed} newly at baseline"
    else:
        baseline_text = "baseline done at start"

    return f"{attempted}/{target} attempted • {ready_text} • {baseline_text}"


def learner_checkpoint_display_mode(counts: dict[str, int]) -> str:
    if learner_checkpoint_display_mode_for_session in {"ready", "mastered"}:
        return learner_checkpoint_display_mode_for_session
    return "ready"


def learner_checkpoint_display_progress() -> tuple[float, dict[str, int], str]:
    counts = learner_checkpoint_counts()
    total = counts["total"]
    if total <= 0:
        return 0.0, counts, "ready"

    display_mode = learner_checkpoint_display_mode(counts)
    if display_mode == "mastered":
        required_units = (
            (0.2 * total)
            + (1.0 * counts["mastered_needed"])
        )
        display_units = (
            (0.2 * counts["attempted"])
            + (1.0 * counts["newly_mastered"])
        )
    else:
        required_units = (
            (0.2 * total)
            + (0.6 * counts["baseline_needed"])
            + (1.0 * counts["ready_needed"])
        )
        display_units = (
            (0.2 * counts["attempted"])
            + (0.6 * counts["newly_baseline"])
            + (1.0 * counts["newly_ready"])
        )
    if required_units <= 0:
        return 0.0, counts, display_mode

    return min(1.0, display_units / required_units), counts, display_mode


def learner_checkpoint_progress_chip(counts: dict[str, int], target: int, display_mode: str) -> str:
    ready_needed = counts.get("ready_needed", 0)
    baseline_needed = counts.get("baseline_needed", 0)
    mastered_needed = counts.get("mastered_needed", 0)
    newly_ready = counts.get("newly_ready", 0)
    newly_baseline = counts.get("newly_baseline", 0)
    newly_mastered = counts.get("newly_mastered", 0)
    attempted = counts.get("attempted", 0)
    mastered = counts.get("mastered", 0)

    if display_mode == "mastered":
        if mastered_needed > 0:
            mastery_text = f"{newly_mastered}/{mastered_needed} newly mastered"
        else:
            mastery_text = "mastered done at start"
        return f"{attempted}/{target} attempted • {mastery_text} • {mastered}/{target} mastered"

    if ready_needed > 0:
        ready_text = f"{newly_ready}/{ready_needed} newly ready"
    else:
        ready_text = "ready done at start"

    if baseline_needed > 0:
        baseline_text = f"{newly_baseline}/{baseline_needed} newly at baseline"
    else:
        baseline_text = "baseline done at start"

    return f"{attempted}/{target} attempted • {ready_text} • {baseline_text}"


def learner_checkpoint_completion_details() -> dict[str, object]:
    details = {
        "complete": False,
        "kind": "",
        "message": "",
    }
    if learner_scheduler_module is None or not learner_checkpoint_question_ids:
        return details

    counts = learner_checkpoint_counts()
    total = counts["total"]
    attempted_count = counts["attempted"]
    ready_needed = counts["ready_needed"]
    baseline_needed = counts["baseline_needed"]
    newly_ready_count = counts["newly_ready"]
    newly_baseline_count = counts["newly_baseline"]
    all_last_attempts_correct = all(
        bool(
            learner_scheduler_module.question_state(learner_progress, question_id).get(
                "last_result_correct",
                False,
            )
        )
        for question_id in learner_checkpoint_question_ids
    )

    all_attempted = attempted_count == total
    ready_completion_ratio = (
        1.0 if ready_needed <= 0 else (newly_ready_count / ready_needed)
    )
    baseline_completion_ratio = (
        1.0 if baseline_needed <= 0 else (newly_baseline_count / baseline_needed)
    )
    attempt_count = len(learner_interactions)

    if attempt_count < 5:
        return details

    if all_last_attempts_correct and ready_completion_ratio >= 0.8:
        if not all_attempted:
            return details
        return {
            "complete": True,
            "kind": "ready_completion",
            "message": "You have this session's set of questions ready for now. Your progress has been saved to your Quiz Passport.",
        }

    if all_last_attempts_correct and baseline_completion_ratio >= 1.0:
        if not all_attempted:
            return details
        return {
            "complete": True,
            "kind": "baseline_completion",
            "message": "Every question in this session's set has reached a solid baseline. Your progress has been saved to your Quiz Passport.",
        }

    if attempt_count > 45:
        return {
            "complete": True,
            "kind": "long_session_escape_hatch",
            "message": "You made strong progress across this session's set. Your progress has been saved to your Quiz Passport.",
        }

    return details


def learner_checkpoint_completion() -> tuple[bool, str]:
    details = learner_checkpoint_completion_details()
    return bool(details.get("complete", False)), str(details.get("message", "") or "")


def formatted_exception_text(exc_type, exc_value, exc_traceback) -> str:
    return "".join(traceback.format_exception(exc_type, exc_value, exc_traceback)).strip()


def report_runtime_error(message: str) -> None:
    console.error(message)
    show_status(message)
    hide_page_loader()


def handle_uncaught_exception(exc_type, exc_value, exc_traceback) -> None:
    report_runtime_error(formatted_exception_text(exc_type, exc_value, exc_traceback))


def handle_asyncio_exception(loop, context) -> None:
    exception = context.get("exception")
    if exception is not None:
        message = formatted_exception_text(type(exception), exception, exception.__traceback__)
    else:
        message = str(context.get("message", "Unhandled async error"))
    report_runtime_error(message)


def save_draft_attempt() -> None:
    if not session_question_ids:
        clear_draft_attempt()
        return

    payload = {
        "question_ids": session_question_ids,
        "answers": answers,
        "current_index": current_index,
        "session_advanced_options_enabled": session_advanced_options_enabled,
        "session_selected_knowledge_areas": session_selected_knowledge_areas,
        "session_show_timer": session_show_timer,
        "session_learner_mode": session_learner_mode,
        "session_timer_started_at_ms": session_timer_started_at_ms,
    }
    window.localStorage.setItem(DRAFT_STORAGE_KEY, json.dumps(payload))


def load_draft_attempt() -> dict | None:
    raw_payload = window.localStorage.getItem(DRAFT_STORAGE_KEY)
    if not raw_payload:
        return None

    try:
        payload = json.loads(raw_payload)
    except Exception:
        clear_draft_attempt()
        return None

    if not isinstance(payload, dict):
        clear_draft_attempt()
        return None

    question_ids = payload.get("question_ids")
    draft_answers = payload.get("answers")
    draft_index = payload.get("current_index")

    if not isinstance(question_ids, list) or not question_ids:
        clear_draft_attempt()
        return None

    if not isinstance(draft_answers, dict):
        clear_draft_attempt()
        return None

    if not isinstance(draft_index, int):
        clear_draft_attempt()
        return None

    return payload


def normalized_saved_response(value):
    if isinstance(value, list):
        return [str(item) for item in value if str(item)]
    if value in (None, ""):
        return None
    return str(value)


def clear_draft_attempt() -> None:
    window.localStorage.removeItem(DRAFT_STORAGE_KEY)


def clear_active_attempt_state() -> None:
    global session_question_ids, answers, current_index
    global session_advanced_options_enabled, session_selected_knowledge_areas
    global session_show_timer, session_learner_mode
    global session_timer_started_at_ms, session_elapsed_seconds
    global learner_review_mode, learner_review_return_state

    session_question_ids = []
    answers = {}
    current_index = 0
    session_advanced_options_enabled = False
    session_selected_knowledge_areas = []
    session_show_timer = False
    session_learner_mode = False
    session_timer_started_at_ms = None
    session_elapsed_seconds = 0
    learner_review_mode = False
    learner_review_return_state = None
    stop_timer_updates()
    stop_learner_debug_updates()
    hide_session_timer()
    clear_draft_attempt()


def show_status(message: str) -> None:
    status_text.textContent = message
    status_box.classes.discard("hidden")


def hide_status() -> None:
    status_box.classes.add("hidden")


def hide_page_loader() -> None:
    page_loader.classes.add("hidden")


def format_elapsed_time(total_seconds: int) -> str:
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"


def update_session_elapsed_time() -> None:
    global session_elapsed_seconds

    if not session_show_timer or session_timer_started_at_ms is None:
        session_elapsed_seconds = 0
        return

    now_ms = float(window.Date.now())
    session_elapsed_seconds = max(0, int((now_ms - session_timer_started_at_ms) // 1000))


def hide_session_timer() -> None:
    session_timer.classes.add("hidden")


def render_session_timer() -> None:
    if not session_show_timer or session_timer_started_at_ms is None:
        hide_session_timer()
        return

    update_session_elapsed_time()
    session_timer.textContent = format_elapsed_time(session_elapsed_seconds)
    session_timer.classes.discard("hidden")


def stop_timer_updates() -> None:
    global timer_task

    if timer_task is not None and not timer_task.done():
        timer_task.cancel()
    timer_task = None


def stop_learner_debug_updates() -> None:
    global learner_debug_task

    if learner_debug_task is not None and not learner_debug_task.done():
        learner_debug_task.cancel()
    learner_debug_task = None


def show_quiz_cursor() -> None:
    document.body.classList.remove("quiz-cursor-hidden")


def hide_quiz_cursor() -> None:
    if quiz_is_visible():
        document.body.classList.add("quiz-cursor-hidden")


def stop_cursor_hide_timer() -> None:
    global cursor_hide_task

    if cursor_hide_task is not None and not cursor_hide_task.done():
        cursor_hide_task.cancel()
    cursor_hide_task = None
    show_quiz_cursor()


async def run_cursor_hide_timer() -> None:
    try:
        await asyncio.sleep(QUIZ_CURSOR_HIDE_DELAY_SECONDS)
        hide_quiz_cursor()
    except asyncio.CancelledError:
        pass


def note_quiz_pointer_activity() -> None:
    global cursor_hide_task

    if not quiz_is_visible():
        stop_cursor_hide_timer()
        return
    show_quiz_cursor()
    stop_cursor_hide_timer()
    cursor_hide_task = asyncio.create_task(run_cursor_hide_timer())


async def run_timer_updates() -> None:
    try:
        while session_show_timer and session_timer_started_at_ms is not None:
            render_session_timer()
            await asyncio.sleep(1)
    except asyncio.CancelledError:
        pass


async def run_learner_debug_updates() -> None:
    try:
        while learner_session_active:
            current_question_id = session_question_ids[0] if session_question_ids else None
            render_learner_debug_panel(current_question_id)
            await asyncio.sleep(1)
    except asyncio.CancelledError:
        pass


def start_timer_updates() -> None:
    global timer_task

    stop_timer_updates()
    if not session_show_timer or session_timer_started_at_ms is None:
        hide_session_timer()
        return

    render_session_timer()
    timer_task = asyncio.create_task(run_timer_updates())


def start_learner_debug_updates() -> None:
    global learner_debug_task

    stop_learner_debug_updates()
    if not learner_session_active or not learner_debug_unlocked:
        learner_debug_download_button.classes.add("hidden")
        learner_debug_copy_button.classes.add("hidden")
        hide_learner_debug_panel()
        return

    current_question_id = session_question_ids[0] if session_question_ids else None
    render_learner_debug_panel(current_question_id)
    learner_debug_task = asyncio.create_task(run_learner_debug_updates())


def show_screen(name: str) -> None:
    for screen_name, screen in {
        "home": home_screen,
        "quiz": quiz_screen,
        "learner-confirm": learner_confirm_screen,
        "learner-passport": learner_passport_screen,
        "learner-generator": learner_generator_screen,
        "learner-hub": learner_hub_screen,
        "quit-confirm": quit_confirm_screen,
        "learner-summary": learner_summary_screen,
        "results": results_screen,
    }.items():
        if screen_name == name:
            screen.classes.discard("hidden")
        else:
            screen.classes.add("hidden")

    if name == "home":
        hero.classes.discard("hidden")
    else:
        hero.classes.add("hidden")

    if name == "quiz":
        note_quiz_pointer_activity()
    else:
        stop_cursor_hide_timer()


def show_results_tab(tab_name: str) -> None:
    if tab_name == "stats":
        stats_tab_button.classes.add("active")
        qna_tab_button.classes.discard("active")
        stats_tab.classes.add("active")
        qna_tab.classes.discard("active")
        stats_tab.classes.discard("hidden")
        qna_tab.classes.add("hidden")
    else:
        qna_tab_button.classes.add("active")
        stats_tab_button.classes.discard("active")
        qna_tab.classes.add("active")
        stats_tab.classes.discard("active")
        qna_tab.classes.discard("hidden")
        stats_tab.classes.add("hidden")


def show_lightbox(image_src: str) -> None:
    lightbox_image.src = image_src
    lightbox.classes.discard("hidden")


def hide_lightbox() -> None:
    lightbox.classes.add("hidden")
    lightbox_image.src = ""


async def clear_toast_after_delay(delay_seconds: float = 4.0) -> None:
    await asyncio.sleep(delay_seconds)
    toast_notification.classes.add("hidden")
    toast_notification.textContent = ""


def show_toast(message: str) -> None:
    global toast_clear_task

    toast_notification.textContent = message
    toast_notification.classes.discard("hidden")

    if toast_clear_task is not None and not toast_clear_task.done():
        toast_clear_task.cancel()

    toast_clear_task = asyncio.create_task(clear_toast_after_delay())


def update_quiz_image_size() -> None:
    if "hidden" in question_image_wrap.classes:
        question_image.style["max-height"] = ""
        return

    quiz_segment = quiz_screen._dom_element.querySelector(".ui.segment .ui.segment")
    if quiz_segment is None:
        return

    viewport_height = window.innerHeight
    segment_top = quiz_segment.getBoundingClientRect().top
    options_height = options_host._dom_element.getBoundingClientRect().height
    question_height = question_text._dom_element.getBoundingClientRect().height
    question_id_height = question_id_text._dom_element.getBoundingClientRect().height
    metadata_height = 0
    if "hidden" not in question_metadata_panel.classes:
        metadata_height = question_metadata_panel._dom_element.getBoundingClientRect().height

    reserved_height = options_height + question_height + question_id_height + metadata_height + 220
    available_height = max(120, viewport_height - segment_top - reserved_height)

    question_image.style["width"] = "auto"
    question_image.style["max-width"] = "75%"
    question_image.style["max-height"] = f"{int(available_height)}px"


def quiz_is_visible() -> bool:
    return "hidden" not in quiz_screen.classes


def move_option_selection(step: int) -> None:
    global learner_selected_answer, multi_select_focus_key

    if not quiz_is_visible() or not session_question_ids:
        return

    question_id = session_question_ids[current_index]
    question = question_cache.get(question_id)
    if question is None or not question.options:
        return
    option_keys = [option["key"] for option in question.options]
    if question_is_multi_select(question):
        current_key = multi_select_focus_key if multi_select_focus_key in option_keys else None
        if current_key in option_keys:
            current_position = option_keys.index(current_key)
        else:
            current_position = -1 if step > 0 else len(option_keys)
        new_position = (current_position + step) % len(option_keys)
        multi_select_focus_key = option_keys[new_position]
        if learner_session_active:
            save_learner_session_draft()
        asyncio.create_task(render_current_question())
        return

    if learner_session_active:
        if learner_answer_locked:
            return
        current_answer = learner_selected_answer
    else:
        current_answer = answers.get(question_id)

    if current_answer in option_keys:
        current_position = option_keys.index(current_answer)
    else:
        current_position = -1 if step > 0 else len(option_keys)

    new_position = (current_position + step) % len(option_keys)
    if learner_session_active:
        learner_selected_answer = option_keys[new_position]
        save_learner_session_draft()
    else:
        answers[question_id] = option_keys[new_position]
        save_draft_attempt()
    asyncio.create_task(render_current_question())


def move_learner_confidence_selection(step: int) -> None:
    global learner_selected_confidence

    if not learner_session_active or learner_answer_locked or learner_selected_answer is None:
        return

    confidence_order = [3, 2, 1, 0]

    if learner_selected_confidence in confidence_order:
        current_position = confidence_order.index(learner_selected_confidence)
    else:
        current_position = -1 if step > 0 else len(confidence_order)

    new_position = (current_position + step) % len(confidence_order)
    learner_selected_confidence = confidence_order[new_position]
    save_learner_session_draft()
    asyncio.create_task(render_current_question())


def multi_select_focus_for_question(question: Question, selected_answer) -> str | None:
    option_keys = [option["key"] for option in question.options]
    if not option_keys:
        return None
    if multi_select_focus_key in option_keys:
        return multi_select_focus_key
    selected_keys = response_keys(question, selected_answer)
    for option_key in option_keys:
        if option_key in selected_keys:
            return option_key
    return option_keys[0]


def rendered_multi_select_focus_key(question: Question) -> str | None:
    option_keys = [option["key"] for option in question.options]
    if not option_keys:
        return None
    if multi_select_focus_key in option_keys:
        return multi_select_focus_key
    return None


def multi_select_focus_active(question: Question) -> bool:
    return rendered_multi_select_focus_key(question) is not None


def toggle_focused_multi_select_option(question: Question) -> None:
    global learner_selected_answer, learner_selected_confidence, multi_select_focus_key

    if not question_is_multi_select(question):
        return

    focus_key = multi_select_focus_for_question(
        question,
        learner_selected_answer if learner_session_active else answers.get(question.question_id),
    )
    if not focus_key:
        return

    multi_select_focus_key = focus_key
    if learner_session_active:
        if learner_answer_locked:
            return
        learner_selected_answer = toggled_response(
            question,
            learner_selected_answer,
            focus_key,
        )
        learner_selected_confidence = None
        save_learner_session_draft()
    else:
        updated_response = toggled_response(
            question,
            answers.get(question.question_id),
            focus_key,
        )
        if updated_response is None:
            answers.pop(question.question_id, None)
        else:
            answers[question.question_id] = updated_response
        save_draft_attempt()
    asyncio.create_task(render_current_question())


async def fetch_json(path: str) -> dict:
    response = await fetch(path)
    if not response.ok:
        raise RuntimeError(f"{path} returned HTTP {response.status}")
    return await response.json()


async def fetch_text(path: str) -> str:
    response = await fetch(path)
    if not response.ok:
        raise RuntimeError(f"{path} returned HTTP {response.status}")
    return await response.text()


def config_metadata_fields(key: str) -> list[dict[str, str]]:
    metadata = APP_CONFIG.get("metadata", {})
    fields = metadata.get(key, [])
    return [field for field in fields if isinstance(field, dict) and isinstance(field.get("key"), str)]


def question_metadata_value(question: Question, key: str, empty_value: str = "") -> str:
    value = question.metadata.get(key, "")
    return value or empty_value


def normalize_text_value(value) -> str:
    if value is None:
        return ""
    return str(value).strip()


def question_metadata_from_payload(payload: dict, indexed_metadata: dict[str, str] | None = None) -> dict[str, str]:
    metadata: dict[str, str] = {}
    indexed_metadata = indexed_metadata or {}

    source_metadata = payload.get("metadata")
    if isinstance(source_metadata, dict):
        for key, value in source_metadata.items():
            if isinstance(key, str):
                metadata[key] = normalize_text_value(value)

    for fallback_key in ("knowledge_area", "syllabus_reference"):
        fallback_value = payload.get(fallback_key) or indexed_metadata.get(fallback_key, "")
        if fallback_value:
            metadata[fallback_key] = normalize_text_value(fallback_value)

    if "learning_outcome" not in metadata:
        metadata["learning_outcome"] = learning_outcome_for(
            metadata.get("knowledge_area", ""),
            metadata.get("syllabus_reference", ""),
        )

    for key, value in indexed_metadata.items():
        if key not in metadata and value:
            metadata[key] = value

    return metadata


def apply_branding() -> None:
    branding = APP_CONFIG.get("branding", {})
    page_title = branding.get("page_title")
    meta_description = branding.get("meta_description")
    hero_title = branding.get("hero_title")
    hero_subtitle = branding.get("hero_subtitle")
    loader_text = branding.get("loader_text")

    if isinstance(page_title, str) and page_title:
        document.title = page_title

    if isinstance(meta_description, str):
        meta_element = document.getElementById("page-meta-description")
        if meta_element is not None:
            meta_element.setAttribute("content", meta_description)

    if isinstance(hero_title, str):
        app_title.textContent = hero_title

    if isinstance(hero_subtitle, str):
        app_subtitle.textContent = hero_subtitle

    if isinstance(loader_text, str):
        page_loader_text.textContent = loader_text


async def load_app_config() -> None:
    global APP_CONFIG, FEATURE_FLAGS, QUESTION_PANEL_FIELDS, RESULTS_METADATA_FIELDS
    global QUIZ_INDEX_PATH, QUESTION_PATH_TEMPLATE, QUIZ_CONFIG_PATH, QUIZ_ID

    payload = await fetch_json(APP_CONFIG_PATH)
    if not isinstance(payload, dict):
        raise RuntimeError("App config must be a JSON object.")

    paths = payload.get("paths", {})
    if not isinstance(paths, dict):
        raise RuntimeError("App config paths must be a JSON object.")

    quiz_index_path = paths.get("quiz_index")
    question_path_template = paths.get("question_path_template")
    quiz_config_path = paths.get("quiz_config")

    if not all(isinstance(value, str) and value for value in (
        quiz_index_path,
        question_path_template,
        quiz_config_path,
    )):
        raise RuntimeError("App config paths are incomplete.")

    APP_CONFIG = payload
    QUIZ_ID = str(payload.get("quiz_id", "") or "")
    FEATURE_FLAGS = {
        key: bool(value)
        for key, value in payload.get("features", {}).items()
    }
    QUESTION_PANEL_FIELDS = config_metadata_fields("question_panel_fields")
    RESULTS_METADATA_FIELDS = config_metadata_fields("results_fields")
    QUIZ_INDEX_PATH = quiz_index_path
    QUESTION_PATH_TEMPLATE = question_path_template
    QUIZ_CONFIG_PATH = quiz_config_path
    apply_branding()


async def load_quiz_config() -> None:
    global KNOWLEDGE_AREAS, SYLLABUS_CATALOG

    payload = await fetch_json(QUIZ_CONFIG_PATH)
    knowledge_areas = payload.get("knowledge_areas")
    syllabus_catalog = payload.get("syllabus_catalog")

    if not isinstance(knowledge_areas, list) or not all(
        isinstance(area, str) and area for area in knowledge_areas
    ):
        raise RuntimeError("Quiz config is missing a valid knowledge_areas list.")

    if not isinstance(syllabus_catalog, dict):
        raise RuntimeError("Quiz config is missing a valid syllabus_catalog map.")

    normalized_catalog: dict[str, dict[str, str]] = {}
    for area in knowledge_areas:
        entries = syllabus_catalog.get(area, {})
        if not isinstance(entries, dict):
            raise RuntimeError(f"Quiz config syllabus entries for '{area}' must be a map.")

        normalized_entries: dict[str, str] = {}
        for reference, description in entries.items():
            if not isinstance(reference, str) or not isinstance(description, str):
                raise RuntimeError(f"Quiz config syllabus entry for '{area}' is invalid.")
            normalized_entries[reference] = description

        normalized_catalog[area] = normalized_entries

    KNOWLEDGE_AREAS = list(knowledge_areas)
    SYLLABUS_CATALOG = normalized_catalog


def area_to_dom_id(area: str) -> str:
    return "".join(character.lower() if character.isalnum() else "-" for character in area)


def selected_knowledge_areas_from_ui() -> list[str]:
    selected: list[str] = []
    for area in KNOWLEDGE_AREAS:
        checkbox = document.getElementById(f"knowledge-area-{area_to_dom_id(area)}")
        if checkbox is not None and checkbox.checked:
            selected.append(area)
    return selected


def available_question_count() -> int:
    if not quiz_index:
        return 0

    if not advanced_options_enabled:
        return int(quiz_index["question_count"])

    selected = selected_knowledge_areas_from_ui()
    if not selected:
        return 0

    return sum(len(question_ids_by_area.get(area, [])) for area in selected)


def update_available_question_display() -> None:
    available_count = available_question_count()
    total_question_count.textContent = str(available_count)
    total_question_count_label.textContent = (
        "questions available" if available_count != 1 else "question available"
    )


def on_knowledge_area_checkbox_change(event) -> None:
    global selected_knowledge_areas

    selected_knowledge_areas = selected_knowledge_areas_from_ui()
    update_available_question_display()
    save_advanced_options_preferences()


def on_show_timer_toggle_change(event) -> None:
    global show_timer_enabled

    show_timer_enabled = bool(show_timer_toggle._dom_element.checked)
    save_advanced_options_preferences()


def on_learner_mode_toggle_change(event) -> None:
    global learner_mode_enabled

    learner_mode_enabled = bool(learner_mode_toggle._dom_element.checked)
    save_advanced_options_preferences()


def set_question_metadata_collapsed(value: bool) -> None:
    global question_metadata_collapsed

    question_metadata_collapsed = value
    window.sessionStorage.setItem(
        QUESTION_METADATA_COLLAPSED_KEY,
        "true" if value else "false",
    )


def learning_outcome_for(knowledge_area: str, syllabus_reference: str) -> str:
    if not knowledge_area or not syllabus_reference:
        return ""
    return SYLLABUS_CATALOG.get(knowledge_area, {}).get(syllabus_reference, "")


def set_results_show_metadata(value: bool) -> None:
    global results_show_metadata

    results_show_metadata = value
    window.sessionStorage.setItem(
        QNA_METADATA_VISIBLE_KEY,
        "true" if value else "false",
    )


def save_advanced_options_preferences() -> None:
    window.localStorage.setItem(
        ADVANCED_OPTIONS_ENABLED_KEY,
        "true" if advanced_options_enabled else "false",
    )
    window.localStorage.setItem(
        ADVANCED_OPTIONS_AREAS_KEY,
        json.dumps(selected_knowledge_areas),
    )
    window.localStorage.setItem(
        ADVANCED_OPTIONS_SHOW_TIMER_KEY,
        "true" if show_timer_enabled else "false",
    )
    window.localStorage.setItem(
        ADVANCED_OPTIONS_LEARNER_MODE_KEY,
        "true" if learner_mode_enabled else "false",
    )


def load_advanced_options_preferences() -> tuple[bool, list[str], bool, bool]:
    stored_enabled = window.localStorage.getItem(ADVANCED_OPTIONS_ENABLED_KEY) == "true"
    stored_areas_raw = window.localStorage.getItem(ADVANCED_OPTIONS_AREAS_KEY)
    stored_show_timer = window.localStorage.getItem(ADVANCED_OPTIONS_SHOW_TIMER_KEY) == "true"
    stored_learner_mode = (
        window.localStorage.getItem(ADVANCED_OPTIONS_LEARNER_MODE_KEY) == "true"
    )

    if not stored_areas_raw:
        return stored_enabled, list(KNOWLEDGE_AREAS), stored_show_timer, stored_learner_mode

    try:
        parsed_areas = json.loads(stored_areas_raw)
    except Exception:
        return stored_enabled, list(KNOWLEDGE_AREAS), stored_show_timer, stored_learner_mode

    if not isinstance(parsed_areas, list):
        return stored_enabled, list(KNOWLEDGE_AREAS), stored_show_timer, stored_learner_mode

    valid_areas = [str(area) for area in parsed_areas if str(area) in KNOWLEDGE_AREAS]
    return stored_enabled, valid_areas, stored_show_timer, stored_learner_mode


async def load_question_bank_index() -> None:
    global quiz_index, question_bank_index, question_ids_by_area

    payload = await fetch_json(QUIZ_INDEX_PATH)
    if not isinstance(payload, dict):
        raise RuntimeError("Quiz index must be a JSON object.")

    metadata_rows = payload.get("question_metadata_index")
    if not isinstance(metadata_rows, list):
        raise RuntimeError("Quiz index is missing question_metadata_index.")

    index: dict[int, dict[str, str]] = {}
    ids_by_area = {area: [] for area in KNOWLEDGE_AREAS}

    for row in metadata_rows:
        if not isinstance(row, dict):
            continue
        try:
            question_id = int(row.get("id") or "0")
        except ValueError:
            continue

        metadata = {
            key: normalize_text_value(value)
            for key, value in row.items()
            if key
        }
        knowledge_area = metadata.get("knowledge_area", "")
        syllabus_reference = metadata.get("syllabus_reference", "")
        metadata["learning_outcome"] = learning_outcome_for(knowledge_area, syllabus_reference)
        index[question_id] = metadata

        if knowledge_area in ids_by_area:
            ids_by_area[knowledge_area].append(question_id)

    quiz_index = payload
    question_bank_index = index
    question_ids_by_area = ids_by_area


def learner_enabled_for_start() -> bool:
    return advanced_options_enabled and bool(learner_mode_toggle._dom_element.checked)


def all_question_ids() -> list[int]:
    return [int(question_id) for question_id in quiz_index.get("question_ids", [])]


async def ensure_learner_modules_loaded() -> None:
    global learner_modules_loaded
    global learner_storage_module, learner_scheduler_module, learner_mode_module

    if learner_modules_loaded:
        return

    learner_storage_module = importlib.import_module("learner_storage")
    learner_scheduler_module = importlib.import_module("learner_scheduler")
    learner_mode_module = importlib.import_module("learner_mode")
    learner_modules_loaded = True


def ensure_learner_progress_loaded() -> None:
    global learner_progress

    if learner_storage_module is None:
        return

    learner_progress = learner_storage_module.load_progress(
        window,
        QUIZ_ID,
        set(all_question_ids()),
    )


def save_learner_progress() -> None:
    if learner_storage_module is None:
        return
    learner_storage_module.save_progress(window, learner_progress)


def clear_learner_session_draft() -> None:
    if learner_storage_module is None or not QUIZ_ID:
        return
    learner_storage_module.clear_session(window, QUIZ_ID)


def save_learner_session_draft() -> None:
    if (
        learner_storage_module is None
        or not QUIZ_ID
        or not learner_session_active
        or not learner_scope_question_ids
        or not session_question_ids
    ):
        return

    learner_storage_module.save_session(
        window,
        QUIZ_ID,
        {
            "scope_name": learner_scope_name,
            "scope_question_ids": learner_scope_question_ids,
            "checkpoint_question_ids": learner_checkpoint_question_ids,
            "checkpoint_baseline_average_mastery": learner_checkpoint_baseline_average_mastery,
            "checkpoint_attempted_question_ids": sorted(learner_checkpoint_attempted_question_ids),
            "checkpoint_initial_ready_question_ids": sorted(learner_checkpoint_initial_ready_question_ids),
            "checkpoint_initial_baseline_question_ids": sorted(learner_checkpoint_initial_baseline_question_ids),
            "checkpoint_initial_mastered_question_ids": sorted(learner_checkpoint_initial_mastered_question_ids),
            "checkpoint_display_mode_for_session": learner_checkpoint_display_mode_for_session,
            "current_question_id": session_question_ids[0],
            "selected_answer": learner_selected_answer,
            "answer_locked": learner_answer_locked,
            "pending_next_question_id": learner_pending_next_question_id,
            "pending_recommendation": learner_pending_recommendation,
            "selected_confidence": learner_selected_confidence,
            "multi_select_focus_key": multi_select_focus_key,
            "review_mode": learner_review_mode,
            "review_return_state": learner_review_return_state,
            "interactions": learner_interactions,
            "session_timer_started_at_ms": session_timer_started_at_ms,
            "session_show_timer": session_show_timer,
        },
    )


def learner_scope_ids(scope_name: str) -> list[int]:
    if scope_name == "__all__":
        return all_question_ids()
    return list(question_ids_by_area.get(scope_name, []))


def learner_scope_display_name(scope_name: str) -> str:
    if learner_mode_module is None:
        return "all Knowledge Areas" if scope_name == "__all__" else scope_name
    return learner_mode_module.scope_label(scope_name)


def show_learner_import_status(message: str, tone: str = "info") -> None:
    learner_import_status.textContent = message
    learner_import_status.classes.discard("hidden")
    learner_import_status.classes.discard("positive")
    learner_import_status.classes.discard("negative")
    if tone == "positive":
        learner_import_status.classes.add("positive")
    elif tone == "negative":
        learner_import_status.classes.add("negative")


def hide_learner_import_status() -> None:
    learner_import_status.textContent = ""
    learner_import_status.classes.add("hidden")
    learner_import_status.classes.discard("positive")
    learner_import_status.classes.discard("negative")


def show_learner_guidance(kind: str, title: str, message: str) -> None:
    global learner_guidance_visible, learner_guidance_kind, learner_guidance_shown_kinds

    learner_guidance_kind = kind
    learner_guidance_shown_kinds.add(kind)
    learner_guidance_visible = True
    learner_guidance_title.textContent = title
    learner_guidance_message.textContent = message
    learner_guidance_modal.classes.discard("hidden")


def hide_learner_guidance() -> None:
    global learner_guidance_visible

    learner_guidance_visible = False
    learner_guidance_modal.classes.add("hidden")


def show_quiz_help(title: str, message_html: str) -> None:
    quiz_help_title.textContent = title
    quiz_help_message.innerHTML = message_html
    quiz_help_modal.classes.discard("hidden")


def hide_quiz_help() -> None:
    quiz_help_modal.classes.add("hidden")
    quiz_help_message.innerHTML = ""


def current_question_for_copy() -> Question | None:
    if not session_question_ids:
        return None
    question_id = session_question_ids[current_index]
    return question_cache.get(question_id)


def current_question_copy_text() -> str:
    question = current_question_for_copy()
    if question is None:
        return ""

    lines = [question.text, ""]
    for option in question.options:
        lines.append(f'{option["key"]}. {option["text"]}')

    answer_value = None
    if learner_session_active:
        if learner_answer_locked:
            answer_value = question.answer
    elif question.question_id in answers:
        answer_value = question.answer

    if answer_value is not None:
        lines.extend(["", f"Answer: {answer_text(question, answer_value)}"])

    return "\n".join(lines).strip()


def normal_mode_help_html() -> str:
    return (
        "<p>Keyboard shortcuts:</p>"
        "<ul>"
        "<li><strong>1-4</strong>: choose an answer</li>"
        "<li><strong>Up / Down</strong>: move answer selection</li>"
        "<li><strong>Left</strong>: previous question</li>"
        "<li><strong>Right</strong>, <strong>Space</strong>, or <strong>Enter</strong>: next question</li>"
        "</ul>"
        "<p>You can also use <strong>Copy question</strong> to copy the current question for pasting elsewhere.</p>"
    )


def learner_mode_help_html() -> str:
    return (
        "<p>Keyboard shortcuts:</p>"
        "<ul>"
        "<li><strong>1-4</strong>: choose an answer</li>"
        "<li><strong>Up / Down</strong>: move answer selection</li>"
        "<li><strong>Left / Right</strong>: move confidence after choosing an answer</li>"
        "<li><strong>Enter</strong>: if no confidence is chosen yet, default to <strong>I'm unsure</strong>; otherwise submit</li>"
        "<li><strong>Space</strong>: submit once confidence is selected</li>"
        "<li><strong>Left</strong> when <strong>Previous</strong> is visible: reopen the most recently answered question for review</li>"
        "</ul>"
        "<p>Tips to move faster:</p>"
        "<ul>"
        "<li>The algorithm rewards faster correct responses, so steady accurate answers help you move through learner mode more quickly.</li>"
        "<li>Use higher confidence only when you really know the answer.</li>"
        "<li>Use lower confidence when you are unsure so the system can adapt more accurately.</li>"
        "<li>Review the previous question if you moved past feedback too quickly.</li>"
        "</ul>"
        "<p>You can also use <strong>Copy question</strong> to copy the current question and options for pasting elsewhere.</p>"
    )


def hide_learner_debug_panel() -> None:
    global learner_debug_previous_values

    learner_debug_panel.classes.add("hidden")
    learner_debug_content.innerHTML = ""
    learner_debug_reopen_button.classes.add("hidden")
    learner_debug_download_button.classes.add("hidden")
    learner_debug_download_button.classes.add("hidden")
    learner_debug_copy_button.classes.add("hidden")
    learner_debug_previous_values = {}


def close_learner_debug_popup() -> None:
    global learner_debug_popup

    if learner_debug_popup is not None and not learner_debug_popup.closed:
        learner_debug_popup.close()
    learner_debug_popup = None


def hide_learner_debug_panel_in_page() -> None:
    global learner_debug_panel_visible

    learner_debug_panel_visible = False
    learner_debug_panel.classes.add("hidden")
    if learner_debug_unlocked:
        learner_debug_reopen_button.classes.discard("hidden")
    else:
        learner_debug_reopen_button.classes.add("hidden")


def show_learner_debug_panel_in_page() -> None:
    global learner_debug_panel_visible

    learner_debug_panel_visible = True
    learner_debug_panel.classes.discard("hidden")
    if learner_debug_unlocked:
        learner_debug_reopen_button.classes.discard("hidden")
    else:
        learner_debug_reopen_button.classes.add("hidden")


def reset_learner_debug_capture_state() -> None:
    global learner_debug_event_log, learner_debug_report_text, learner_debug_checkpoint_completion_captured
    global learner_debug_previous_values, learner_debug_session_end_details, learner_session_end_context

    learner_debug_event_log = []
    learner_debug_report_text = ""
    learner_debug_checkpoint_completion_captured = False
    learner_debug_previous_values = {}
    learner_debug_session_end_details = {}
    learner_session_end_context = {}
    learner_debug_download_button.classes.add("hidden")
    learner_debug_copy_button.classes.add("hidden")


def learner_debug_is_open() -> bool:
    popup_open = learner_debug_popup is not None and not learner_debug_popup.closed
    return learner_debug_unlocked and (learner_debug_panel_visible or popup_open)


def reset_learner_debug_unlock() -> None:
    global learner_debug_unlocked, learner_debug_unlock_buffer, learner_debug_panel_visible

    learner_debug_unlocked = False
    learner_debug_unlock_buffer = ""
    learner_debug_panel_visible = False
    learner_debug_panel.classes.add("hidden")
    learner_debug_reopen_button.classes.add("hidden")
    learner_debug_download_button.classes.add("hidden")
    learner_debug_copy_button.classes.add("hidden")


def unlock_learner_debug_controls() -> None:
    global learner_debug_unlocked, learner_debug_unlock_buffer

    learner_debug_unlocked = True
    learner_debug_unlock_buffer = ""
    learner_debug_reopen_button.classes.discard("hidden")


def learner_debug_popup_html(content: str) -> str:
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Learner Debug</title>
  <style>
    body {{
      margin: 0;
      padding: 12px;
      background: #f6f6f6;
      color: #333;
      font: 12px/1.5 Consolas, "Courier New", monospace;
    }}
    .wrap {{
      background: #fff;
      border: 1px solid #d7d7d7;
      padding: 12px;
      box-shadow: 0 6px 18px rgba(0,0,0,0.08);
      max-width: 1100px;
    }}
    .title {{
      margin: 0 0 8px;
      font: 700 11px/1.4 system-ui, sans-serif;
      letter-spacing: 0.08em;
      text-transform: uppercase;
      color: #666;
    }}
    .learner-debug-content {{
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 10px;
      align-items: start;
    }}
    .learner-debug-section-title {{
      margin: 0 0 4px;
      font: 700 10px/1.4 system-ui, sans-serif;
      letter-spacing: .06em;
      text-transform: uppercase;
      color: #777;
    }}
    .learner-debug-section {{
      min-width: 0;
      border: 1px solid rgba(0,0,0,.08);
      border-radius: 7px;
      background: rgba(255,255,255,.92);
      padding: 7px 8px;
      box-shadow: inset 0 1px 0 rgba(255,255,255,.7);
    }}
    .learner-debug-table {{
      width: 100%;
      border-collapse: collapse;
      table-layout: fixed;
    }}
    .learner-debug-line {{
      border-top: 1px solid rgba(0,0,0,.05);
      transition: background-color .25s ease;
    }}
    .learner-debug-table tr:first-child {{
      border-top: 0;
    }}
    .learner-debug-line-highlight {{
      animation: learner-debug-flash 1.35s ease;
    }}
    .learner-debug-key {{
      width: 38%;
      padding: 2px 4px;
      color: #666;
      vertical-align: top;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }}
    .learner-debug-value {{
      width: 62%;
      padding: 2px 4px;
      color: #333;
      word-break: break-word;
      vertical-align: top;
      border-left: 1px solid rgba(0,0,0,.05);
    }}
    .learner-debug-good .learner-debug-value {{
      color: #1e6b38;
      font-weight: 700;
    }}
    .learner-debug-bad .learner-debug-value {{
      color: #a3332c;
      font-weight: 700;
    }}
    @keyframes learner-debug-flash {{
      0% {{
        background: rgba(255, 241, 118, 0);
      }}
      18% {{
        background: rgba(255, 241, 118, 0.85);
      }}
      100% {{
        background: rgba(255, 241, 118, 0);
      }}
    }}
    @media (max-width: 720px) {{
      .learner-debug-content {{
        grid-template-columns: minmax(0, 1fr);
      }}
    }}
  </style>
</head>
<body>
  <div class="wrap">
    <div class="title">Learner Debug</div>
    <div class="learner-debug-content">{content}</div>
  </div>
</body>
</html>"""


def update_learner_debug_popup(content: str) -> None:
    if learner_debug_popup is None or learner_debug_popup.closed:
        return
    learner_debug_popup.document.open()
    learner_debug_popup.document.write(learner_debug_popup_html(content))
    learner_debug_popup.document.close()


def open_learner_debug_popup() -> None:
    global learner_debug_popup

    popup = window.open("", "quizurselfLearnerDebug", "width=920,height=720")
    if popup is None:
        show_toast("The debug window was blocked by the browser.")
        return
    learner_debug_popup = popup
    update_learner_debug_popup(
        learner_debug_content.innerHTML
        or (
            "<section class='learner-debug-section'>"
            "<div class='learner-debug-section-title'>Overview</div>"
            "<table class='learner-debug-table'>"
            "<tr class='learner-debug-line'>"
            "<td class='learner-debug-key'>status</td>"
            "<td class='learner-debug-value'>No learner debug data yet.</td>"
            "</tr>"
            "</table>"
            "</section>"
        )
    )


def learner_debug_tone(key: str, value) -> str:
    if key in {"knowledge", "user_grit", "meta_learning", "mastery", "stability", "recent_accuracy_8", "recent_mastery_gain_8", "recent_meta_8", "recent_grit_8", "latest_grit"}:
        try:
            numeric = float(value)
        except Exception:
            return ""
        if numeric >= 0.7:
            return "good"
        if numeric <= 0.35:
            return "bad"
        return ""
    if key in {"difficulty", "consecutive_wrong"}:
        try:
            numeric = float(value)
        except Exception:
            return ""
        if numeric >= 0.7 or numeric >= 2:
            return "bad"
        if numeric <= 0.25 or numeric == 0:
            return "good"
        return ""
    if key in {"due_in_minutes"}:
        try:
            numeric = float(value)
        except Exception:
            return ""
        if numeric < 0:
            return "bad"
    return ""


def learner_debug_line_html(key: str, value: str, highlight: bool, tone: str) -> str:
    classes = ["learner-debug-line"]
    if highlight:
        classes.append("learner-debug-line-highlight")
    if tone == "good":
        classes.append("learner-debug-good")
    elif tone == "bad":
        classes.append("learner-debug-bad")
    class_name = " ".join(classes)
    return (
        f'<tr class="{class_name}">'
        f'<td class="learner-debug-key">{escape(key)}</td>'
        f'<td class="learner-debug-value">{escape(value)}</td>'
        "</tr>"
    )


def learner_debug_section_html(title: str, rows: list[str]) -> str:
    return (
        '<section class="learner-debug-section">'
        f'<div class="learner-debug-section-title">{escape(title)}</div>'
        '<table class="learner-debug-table">'
        f'{"".join(rows)}'
        "</table>"
        "</section>"
    )


def render_learner_debug_panel(current_question_id: int | None = None) -> None:
    global learner_debug_previous_values

    if not learner_session_active or learner_scheduler_module is None or learner_storage_module is None:
        if learner_debug_report_text and learner_debug_unlocked:
            learner_debug_download_button.classes.discard("hidden")
            learner_debug_copy_button.classes.discard("hidden")
            return
        hide_learner_debug_panel()
        return

    state = None
    if current_question_id is not None:
        state = learner_scheduler_module.question_state(learner_progress, current_question_id)

    window_items = learner_interactions[-8:]
    avg_mastery_gain = (
        sum(item.get("mastery_delta", 0.0) for item in window_items) / len(window_items)
        if window_items else 0.0
    )
    avg_accuracy = (
        sum(1 for item in window_items if item.get("is_correct")) / len(window_items)
        if window_items else 0.0
    )
    avg_meta = (
        sum(item.get("meta_learning", 0.0) for item in window_items) / len(window_items)
        if window_items else 0.0
    )
    avg_grit = (
        sum(item.get("grit", 0.0) for item in window_items) / len(window_items)
        if window_items else 0.0
    )
    recommendation_kind = (learner_pending_recommendation or {}).get("kind", "")
    recommendation_message = (learner_pending_recommendation or {}).get("message", "")
    now_ms = int(window.Date.now())
    due_in_minutes = None
    due_in_seconds = None
    attempts = 0
    correct_attempts = 0
    confidence_history_tail = "-"
    confidence_history_count = 0
    attempt_accuracy = None
    last_seen_delta_seconds = None
    updated_delta_seconds = None
    computed_priority = None
    computed_is_mastered = None
    current_user_grit = (
        learner_scheduler_module.current_user_grit(learner_progress, now_ms)
        if learner_scheduler_module is not None
        else 0.0
    )
    user_grit_updated_at = max(0, int(learner_progress.get("user_grit_updated_at", 0) or 0))
    user_grit_updated_delta_seconds = (
        round((now_ms - user_grit_updated_at) / 1000, 1)
        if user_grit_updated_at > 0
        else None
    )
    recent_question_ids = [item.get("question_id") for item in learner_interactions[-3:]]
    if state is not None and int(state.get("due_at", 0) or 0) > 0:
        due_in_minutes = round((int(state["due_at"]) - now_ms) / 60000, 2)
        due_in_seconds = round((int(state["due_at"]) - now_ms) / 1000, 1)
    if state is not None:
        attempts = int(state.get("attempts", 0) or 0)
        correct_attempts = int(state.get("correct_attempts", 0) or 0)
        attempt_accuracy = (correct_attempts / attempts) if attempts else None
        confidence_history = state.get("confidence_history", [])
        if isinstance(confidence_history, list):
            confidence_history_count = len(confidence_history)
            if confidence_history_count:
                confidence_history_tail = ", ".join(str(value) for value in confidence_history[-8:])
        last_seen_at = int(state.get("last_seen_at", 0) or 0)
        updated_at = int(state.get("updated_at", 0) or 0)
        if last_seen_at > 0:
            last_seen_delta_seconds = round((now_ms - last_seen_at) / 1000, 1)
        if updated_at > 0:
            updated_delta_seconds = round((now_ms - updated_at) / 1000, 1)
        computed_priority = learner_scheduler_module.question_priority(
            state,
            now_ms,
            int(current_question_id or 0),
            recent_question_ids,
        )
        computed_is_mastered = learner_scheduler_module.is_mastered(state)

    interaction_count = len(learner_interactions)
    window_size = len(window_items)
    checkpoint_progress, checkpoint_target = learner_checkpoint_status()
    checkpoint_display_progress, checkpoint_counts, checkpoint_display_mode = learner_checkpoint_display_progress()
    checkpoint_average_mastery = learner_checkpoint_average_mastery(learner_checkpoint_question_ids)
    checkpoint_average_mastery_gain = (
        checkpoint_average_mastery - learner_checkpoint_baseline_average_mastery
    )
    checkpoint_attempted_count = checkpoint_counts["attempted"]
    checkpoint_ready_count = checkpoint_counts["ready"]
    checkpoint_mastery_04_count = checkpoint_counts["mastery_04"]
    checkpoint_newly_ready_count = checkpoint_counts["newly_ready"]
    checkpoint_newly_baseline_count = checkpoint_counts["newly_baseline"]
    checkpoint_mastered_count = checkpoint_counts["mastered"]
    checkpoint_newly_mastered_count = checkpoint_counts["newly_mastered"]
    checkpoint_mastered_needed = checkpoint_counts["mastered_needed"]
    checkpoint_ready_needed = checkpoint_counts["ready_needed"]
    checkpoint_baseline_needed = checkpoint_counts["baseline_needed"]
    checkpoint_ready_completion_ratio = (
        1.0 if checkpoint_ready_needed <= 0 else (checkpoint_newly_ready_count / checkpoint_ready_needed)
    )
    checkpoint_baseline_completion_ratio = (
        1.0 if checkpoint_baseline_needed <= 0 else (checkpoint_newly_baseline_count / checkpoint_baseline_needed)
    )
    checkpoint_all_last_attempts_correct = all(
        bool(
            learner_scheduler_module.question_state(learner_progress, question_id).get(
                "last_result_correct",
                False,
            )
        )
        for question_id in learner_checkpoint_question_ids
    ) if learner_scheduler_module is not None and learner_checkpoint_question_ids else False
    checkpoint_complete, checkpoint_completion_message = learner_checkpoint_completion()
    avg_response_ms = (
        sum(item.get("response_ms", 0) for item in window_items) / len(window_items)
        if window_items else 0.0
    )
    avg_confidence = (
        sum(item.get("confidence", 0) for item in window_items) / len(window_items)
        if window_items else 0.0
    )
    latest_interaction = window_items[-1] if window_items else {}

    overview_items: list[tuple[str, str]] = [
        ("scope", learner_scope_display_name(learner_scope_name)),
        ("question_id", str(current_question_id or "-")),
        ("user_grit", f"{current_user_grit:.3f}"),
        ("user_grit_updated_delta_s", f"{user_grit_updated_delta_seconds if user_grit_updated_delta_seconds is not None else '-'}"),
        ("selected_answer", str(learner_selected_answer or "-")),
        ("selected_confidence", str(learner_selected_confidence if learner_selected_confidence is not None else "-")),
        ("answer_locked", str(learner_answer_locked)),
        ("interaction_count", str(interaction_count)),
        ("attempt_count", str(interaction_count)),
        ("recent_window_size", str(window_size)),
        ("checkpoint_ready", f"{checkpoint_progress}/{checkpoint_target}"),
        ("checkpoint_set_size", str(checkpoint_target)),
        ("checkpoint_display_progress", f"{checkpoint_display_progress:.3f}"),
        ("checkpoint_display_mode", checkpoint_display_mode),
    ]

    checkpoint_completion_items: list[tuple[str, str]] = [
        ("checkpoint_questions_attempted", f"{checkpoint_attempted_count}/{checkpoint_target}"),
        ("checkpoint_questions_ready", f"{checkpoint_ready_count}/{checkpoint_target}"),
        ("checkpoint_questions_mastered", f"{checkpoint_mastered_count}/{checkpoint_target}"),
        ("checkpoint_questions_mastery_ge_0_4", f"{checkpoint_mastery_04_count}/{checkpoint_target}"),
        ("checkpoint_initial_ready", f'{len(learner_checkpoint_initial_ready_question_ids)}/{checkpoint_target}'),
        ("checkpoint_initial_baseline", f'{len(learner_checkpoint_initial_baseline_question_ids)}/{checkpoint_target}'),
        ("checkpoint_initial_mastered", f'{len(learner_checkpoint_initial_mastered_question_ids)}/{checkpoint_target}'),
        ("checkpoint_ready_needed_at_start", f"{checkpoint_ready_needed}/{checkpoint_target}"),
        ("checkpoint_baseline_needed_at_start", f"{checkpoint_baseline_needed}/{checkpoint_target}"),
        ("checkpoint_mastered_needed_at_start", f"{checkpoint_mastered_needed}/{checkpoint_target}"),
        ("checkpoint_newly_ready", f"{checkpoint_newly_ready_count}/{max(1, checkpoint_ready_needed)}" if checkpoint_ready_needed > 0 else "done at start"),
        ("checkpoint_newly_baseline", f"{checkpoint_newly_baseline_count}/{max(1, checkpoint_baseline_needed)}" if checkpoint_baseline_needed > 0 else "done at start"),
        ("checkpoint_newly_mastered", f"{checkpoint_newly_mastered_count}/{max(1, checkpoint_mastered_needed)}" if checkpoint_mastered_needed > 0 else "done at start"),
        ("checkpoint_average_mastery", f"{checkpoint_average_mastery:.3f}"),
        ("checkpoint_baseline_average_mastery", f"{learner_checkpoint_baseline_average_mastery:.3f}"),
        ("checkpoint_average_mastery_gain", f"{checkpoint_average_mastery_gain:.3f}"),
        ("checkpoint_interactions", str(interaction_count)),
        ("checkpoint_min_attempts_5", str(interaction_count >= 5)),
        ("checkpoint_all_attempted", str(checkpoint_attempted_count == checkpoint_target if checkpoint_target else False)),
        ("checkpoint_all_last_attempts_correct", str(checkpoint_all_last_attempts_correct)),
        ("checkpoint_ready_completion_ratio", f"{checkpoint_ready_completion_ratio:.3f}"),
        ("checkpoint_ready_ratio_ge_0_8", str(checkpoint_ready_completion_ratio >= 0.8)),
        ("checkpoint_baseline_completion_ratio", f"{checkpoint_baseline_completion_ratio:.3f}"),
        ("checkpoint_all_remaining_baseline_done", str(checkpoint_baseline_completion_ratio >= 1.0)),
        ("checkpoint_attempts_gt_45", str(interaction_count > 45)),
        ("checkpoint_complete", str(checkpoint_complete)),
    ]
    if checkpoint_completion_message:
        checkpoint_completion_items.append(("checkpoint_completion_message", checkpoint_completion_message))

    question_state_items: list[tuple[str, str]] = []
    if state is not None:
        question_state_items.extend([
            ("knowledge", f"{float(state.get('knowledge', 0.0)):.3f}"),
            ("meta_learning", f"{float(state.get('meta_learning', 0.0)):.3f}"),
            ("mastery", f"{float(state.get('mastery', 0.0)):.3f}"),
            ("stability", f"{float(state.get('stability', 0.0)):.3f}"),
            ("difficulty", f"{float(state.get('difficulty', 0.0)):.3f}"),
            ("attempts", f"{attempts}"),
            ("correct_attempts", f"{correct_attempts}"),
            ("attempt_accuracy", f"{attempt_accuracy:.3f}" if attempt_accuracy is not None else "-"),
            ("consecutive_correct", f"{int(state.get('consecutive_correct', 0) or 0)}"),
            ("consecutive_wrong", f"{int(state.get('consecutive_wrong', 0) or 0)}"),
            ("last_result_correct", str(bool(state.get("last_result_correct", False)))),
            ("last_answer_ms", f"{int(state.get('last_answer_ms', 0) or 0)}"),
            ("last_seen_delta_s", f"{last_seen_delta_seconds if last_seen_delta_seconds is not None else '-'}"),
            ("updated_delta_s", f"{updated_delta_seconds if updated_delta_seconds is not None else '-'}"),
            ("due_in_minutes", f"{due_in_minutes if due_in_minutes is not None else '-'}"),
            ("due_in_seconds", f"{due_in_seconds if due_in_seconds is not None else '-'}"),
            ("is_mastered", str(computed_is_mastered)),
            ("computed_priority", f"{computed_priority:.3f}" if computed_priority is not None else "-"),
            ("confidence_history_count", str(confidence_history_count)),
            ("confidence_history_tail", confidence_history_tail),
        ])

    recent_window_items: list[tuple[str, str]] = [
        ("recent_accuracy_8", f"{avg_accuracy:.3f}"),
        ("recent_mastery_gain_8", f"{avg_mastery_gain:.4f}"),
        ("recent_meta_8", f"{avg_meta:.3f}"),
        ("recent_grit_8", f"{avg_grit:.3f}"),
        ("recent_avg_response_ms_8", f"{avg_response_ms:.1f}"),
        ("recent_avg_confidence_8", f"{avg_confidence:.3f}"),
        ("recent_question_ids_3", ", ".join(str(question_id) for question_id in recent_question_ids) or "-"),
        ("latest_question_id", str(latest_interaction.get("question_id", "-"))),
        ("latest_is_correct", str(latest_interaction.get("is_correct", "-"))),
        ("latest_confidence", str(latest_interaction.get("confidence", "-"))),
        ("latest_response_ms", str(latest_interaction.get("response_ms", "-"))),
        ("latest_mastery_delta", f"{float(latest_interaction.get('mastery_delta', 0.0)):.4f}" if latest_interaction else "-"),
        ("latest_meta_learning", f"{float(latest_interaction.get('meta_learning', 0.0)):.3f}" if latest_interaction else "-"),
        ("latest_grit", f"{float(latest_interaction.get('grit', 0.0)):.3f}" if latest_interaction else "-"),
    ]

    scheduler_items: list[tuple[str, str]] = [
        ("pending_recommendation", recommendation_kind or "-"),
        ("pending_end_session", str(bool((learner_pending_recommendation or {}).get("end_session", False)))),
        ("pending_next_question_id", str(learner_pending_next_question_id if learner_pending_next_question_id is not None else "-")),
        ("guidance_visible", str(learner_guidance_visible)),
        ("guidance_kind", learner_guidance_kind or "-"),
        ("timer_enabled", str(session_show_timer)),
        ("elapsed_seconds", str(session_elapsed_seconds)),
        ("question_started_at_ms", str(int(learner_question_started_at_ms) if learner_question_started_at_ms else "-")),
        ("scope_question_count", str(len(learner_scope_question_ids))),
        ("checkpoint_question_count", str(len(learner_checkpoint_question_ids))),
        ("all_question_count", str(len(all_question_ids()))),
    ]
    if recommendation_message:
        scheduler_items.append(("recommendation_message", recommendation_message))

    sections = [
        ("Overview", overview_items),
        ("Checkpoint Completion", checkpoint_completion_items),
        ("Question State", question_state_items),
        ("Recent Window", recent_window_items),
        ("Scheduler", scheduler_items),
    ]

    html_sections: list[str] = []
    current_values: dict[str, str] = {}
    for title, section_items in sections:
        if not section_items:
            continue
        rows: list[str] = []
        for key, value in section_items:
            current_values[key] = value
            highlight = learner_debug_previous_values.get(key) not in {None, value}
            tone = learner_debug_tone(key, value)
            rows.append(learner_debug_line_html(key, value, highlight, tone))
        html_sections.append(learner_debug_section_html(title, rows))

    content = "".join(html_sections)
    learner_debug_content.innerHTML = content
    learner_debug_download_button.classes.add("hidden")
    learner_debug_copy_button.classes.add("hidden")
    learner_debug_previous_values = current_values
    if learner_debug_unlocked and learner_debug_panel_visible:
        learner_debug_panel.classes.discard("hidden")
        learner_debug_reopen_button.classes.discard("hidden")
    else:
        learner_debug_panel.classes.add("hidden")
        if learner_debug_unlocked:
            learner_debug_reopen_button.classes.discard("hidden")
        else:
            learner_debug_reopen_button.classes.add("hidden")
    update_learner_debug_popup(content)


def configure_quit_confirm_screen(mode: str) -> None:
    global quit_confirm_mode

    quit_confirm_mode = mode
    if mode == "learner":
        quit_confirm_kicker.textContent = "End Session"
        quit_confirm_title.textContent = "Are you sure?"
        quit_confirm_copy.textContent = (
            "Your progress will be saved to your Quiz Passport."
        )
        confirm_quit_button.textContent = "Yes"
        cancel_quit_button.textContent = "No"
    else:
        quit_confirm_kicker.textContent = "Quit Attempt"
        quit_confirm_title.textContent = "Are you sure?"
        quit_confirm_copy.textContent = (
            "If you quit this attempt, your saved draft and current progress will be cleared "
            "and you will return to the home page."
        )
        confirm_quit_button.textContent = "Yes, Quit Attempt"
        cancel_quit_button.textContent = "Cancel"


def download_json_payload(payload: dict, filename: str) -> None:
    anchor = document.createElement("a")
    json_text = json.dumps(payload, indent=2)
    anchor.setAttribute(
        "href",
        "data:application/json;charset=utf-8," + quote(json_text),
    )
    anchor.setAttribute("download", filename)
    document.body.appendChild(anchor)
    anchor.click()
    document.body.removeChild(anchor)


def learner_username() -> str:
    if learner_storage_module is None:
        return "User"
    return learner_storage_module.normalize_username(
        learner_progress.get("username", "User") if isinstance(learner_progress, dict) else "User"
    )


def learner_avatar_id() -> str:
    if learner_storage_module is None:
        return "cat_smile"
    return learner_storage_module.normalize_avatar_id(
        learner_progress.get("avatar_id", "cat_smile") if isinstance(learner_progress, dict) else "cat_smile"
    )


def learner_avatar_bg_id() -> str:
    if learner_storage_module is None:
        return "peach"
    return learner_storage_module.normalize_avatar_bg_id(
        learner_progress.get("avatar_bg_id", "peach") if isinstance(learner_progress, dict) else "peach"
    )


def passport_avatar(avatar_id: str | None = None) -> dict:
    normalized_id = (
        learner_storage_module.normalize_avatar_id(avatar_id or learner_avatar_id())
        if learner_storage_module is not None
        else (avatar_id or "cat_smile")
    )
    for avatar in PASSPORT_AVATARS:
        if avatar["id"] == normalized_id:
            return avatar
    return PASSPORT_AVATARS[0]


def passport_avatar_src(avatar_id: str | None = None) -> str:
    avatar = passport_avatar(avatar_id)
    return f'{TWEMOJI_BASE_URL}/{avatar["codepoint"]}.svg'


def passport_avatar_background(background_id: str | None = None) -> dict:
    normalized_id = (
        learner_storage_module.normalize_avatar_bg_id(background_id or learner_avatar_bg_id())
        if learner_storage_module is not None
        else (background_id or "peach")
    )
    for background in PASSPORT_AVATAR_BACKGROUNDS:
        if background["id"] == normalized_id:
            return background
    return PASSPORT_AVATAR_BACKGROUNDS[0]


def set_avatar_background(element, background_id: str | None = None) -> None:
    background = passport_avatar_background(background_id)
    element._dom_element.style.setProperty("--avatar-bg", background["color"])


def learner_username_filename_slug() -> str:
    raw_name = learner_username()
    safe_chars = []
    for char in raw_name:
        if char.isalnum():
            safe_chars.append(char)
        elif char in (" ", "-", "_"):
            safe_chars.append("_")
    slug = "".join(safe_chars).strip("_")
    return slug or "User"


def passport_timestamp_prefix() -> str:
    now = window.Date.new()
    year = int(now.getFullYear())
    month = str(int(now.getMonth()) + 1).zfill(2)
    day = str(int(now.getDate())).zfill(2)
    hours = str(int(now.getHours())).zfill(2)
    minutes = str(int(now.getMinutes())).zfill(2)
    seconds = str(int(now.getSeconds())).zfill(2)
    return f"{year}-{month}-{day}_{hours}-{minutes}-{seconds}"


def exported_progress_filename() -> str:
    return (
        f"{passport_timestamp_prefix()}_"
        f"{learner_username_filename_slug()}_{QUIZ_ID}_quiz_passport.json"
    )


def exported_progress_payload() -> dict:
    exported_at = window.Date.new().toISOString()
    return learner_storage_module.export_payload(learner_progress, exported_at)


async def import_learner_progress_from_file() -> None:
    if learner_storage_module is None:
        return

    file_list = learner_progress_file._dom_element.files
    if file_list is None or file_list.length == 0:
        show_learner_import_status("Choose a learner progress JSON file first.", "negative")
        return

    js_file = file_list.item(0)
    try:
        raw_text = await js_file.text()
        payload = json.loads(raw_text)
        progress = learner_storage_module.normalize_progress(
            payload,
            QUIZ_ID,
            set(all_question_ids()),
        )
    except Exception as exc:
        show_learner_import_status(f"Could not import learner progress: {exc}", "negative")
        return

    global learner_progress
    learner_progress = progress
    save_learner_progress()
    clear_learner_session_draft()
    show_learner_import_status("Quiz Passport imported successfully.", "positive")
    render_learner_hub()
    show_screen("learner-hub")


def create_fresh_learner_progress(
    username: str | None = None,
    avatar_id: str | None = None,
    avatar_bg_id: str | None = None,
) -> None:
    global learner_progress
    learner_progress = learner_storage_module.create_empty_progress(QUIZ_ID)
    learner_progress["username"] = learner_storage_module.normalize_username(username)
    learner_progress["avatar_id"] = learner_storage_module.normalize_avatar_id(avatar_id)
    learner_progress["avatar_bg_id"] = learner_storage_module.normalize_avatar_bg_id(avatar_bg_id)
    save_learner_progress()
    clear_learner_session_draft()
    show_learner_import_status(
        f"Started a fresh Quiz Passport for {learner_username()}.",
        "positive",
    )
    render_learner_hub()
    show_screen("learner-hub")


def enter_learner_generator_screen() -> None:
    global learner_generator_avatar_id, learner_generator_avatar_bg_id

    default_name = learner_username() if learner_username() != "User" else ""
    learner_username_input._dom_element.value = default_name
    learner_generator_avatar_id = learner_avatar_id()
    learner_generator_avatar_bg_id = learner_avatar_bg_id()
    render_learner_generator_avatar_picker()
    show_screen("learner-generator")
    try:
        learner_username_input._dom_element.focus()
        learner_username_input._dom_element.select()
    except Exception:
        pass


def render_learner_generator_avatar_picker() -> None:
    avatar = passport_avatar(learner_generator_avatar_id)
    background = passport_avatar_background(learner_generator_avatar_bg_id)
    learner_generator_avatar_preview.setAttribute("src", passport_avatar_src(avatar["id"]))
    learner_generator_avatar_preview.setAttribute("alt", avatar["label"])
    set_avatar_background(learner_generator_avatar_frame, background["id"])
    learner_generator_avatar_name.textContent = avatar["label"]
    learner_avatar_options.innerHTML = ""
    for option in PASSPORT_AVATARS:
        selected_class = " selected" if option["id"] == avatar["id"] else ""
        learner_avatar_options.innerHTML += (
            f'<button class="learner-avatar-option{selected_class}" type="button" '
            f'style="--avatar-bg: {escape(background["color"])}" '
            f'data-learner-avatar-id="{escape(option["id"])}" '
            f'title="{escape(option["label"])}">'
            f'<img src="{escape(passport_avatar_src(option["id"]))}" alt="{escape(option["label"])}">'
            "</button>"
        )
    learner_avatar_bg_options.innerHTML = ""
    for option in PASSPORT_AVATAR_BACKGROUNDS:
        selected_class = " selected" if option["id"] == background["id"] else ""
        learner_avatar_bg_options.innerHTML += (
            f'<button class="learner-avatar-bg-option{selected_class}" type="button" '
            f'style="--avatar-bg: {escape(option["color"])}" '
            f'data-learner-avatar-bg-id="{escape(option["id"])}" '
            f'title="{escape(option["label"])}"></button>'
        )


def reset_quiz_screen_for_mode() -> None:
    global learner_selected_confidence

    learner_feedback.classes.add("hidden")
    learner_feedback.classes.discard("is-correct")
    learner_feedback.classes.discard("is-wrong")
    learner_feedback.textContent = ""
    learner_confidence_panel.classes.add("hidden")
    learner_confidence_buttons.innerHTML = ""
    question_metadata_toggle.classes.discard("hidden")
    learner_selected_confidence = None


def render_learner_hub() -> None:
    hide_learner_import_status()
    learner_hub_progress.innerHTML = ""
    username = learner_username()
    avatar = passport_avatar()
    background = passport_avatar_background()
    learner_hub_avatar.setAttribute("src", passport_avatar_src(avatar["id"]))
    learner_hub_avatar.setAttribute("alt", avatar["label"])
    set_avatar_background(learner_hub_avatar_frame, background["id"])
    learner_hub_title.textContent = f"Welcome {username}! Choose what to learn next"
    learner_hub_copy.textContent = (
        f"{username}'s Quiz Passport is active. Choose a Knowledge Area to keep "
        "learning, or take on all Knowledge Areas together."
    )

    overall = learner_mode_module.summary_for_scope("__all__", all_question_ids(), learner_progress)
    learner_hub_overall.innerHTML = (
        f'<div class="value">{overall["percent_learned"]}%</div>'
        '<div class="label">overall progress</div>'
    )

    rows = learner_mode_module.area_progress_rows(KNOWLEDGE_AREAS, question_ids_by_area, learner_progress)
    rows.append(learner_mode_module.progress_for_scope("__all__", all_question_ids(), learner_progress))

    for row in rows:
        scope_name = row["name"]
        display_name = learner_scope_display_name(scope_name)
        learner_hub_progress.innerHTML += (
            '<div class="learner-progress-card">'
            '<div class="learner-progress-head">'
            f'<p class="learner-progress-title">{escape(display_name)}</p>'
            f'<div class="learner-progress-percent">Learning progress: {row["percent_learned"]}%</div>'
            "</div>"
            f'<p class="learner-progress-subtitle">{row["question_count"]} questions</p>'
            '<div class="learner-progress-bar">'
            f'<div class="learner-progress-bar-fill" style="width:{row["percent_learned"]}%"></div>'
            "</div>"
            f'<button class="ui primary button" type="button" data-learner-scope="{escape(scope_name)}">Learn {escape(display_name)}</button>'
            "</div>"
        )


def render_learner_confidence_buttons() -> None:
    learner_confidence_buttons.innerHTML = ""
    confidence_labels = list(reversed(learner_scheduler_module.CONFIDENCE_LABELS))
    confidence_values = list(reversed(range(len(learner_scheduler_module.CONFIDENCE_LABELS))))
    confidence_class_names = {
        3: "confidence-high",
        2: "confidence-mid-high",
        1: "confidence-mid-low",
        0: "confidence-low",
    }

    for label, confidence_value in zip(confidence_labels, confidence_values):
        button = document.createElement("button")
        button.className = (
            "ui button learner-confidence-button "
            + confidence_class_names.get(confidence_value, "")
        ).strip()
        if learner_selected_confidence == confidence_value:
            button.className += " selected"
        button.type = "button"
        button.textContent = label
        button.setAttribute("data-learner-confidence", str(confidence_value))
        learner_confidence_buttons._dom_element.appendChild(button)


def render_learner_feedback(
    question: Question,
    selected_answer: str,
    is_correct: bool,
    recommendation_message: str = "",
) -> None:
    learner_feedback.classes.discard("hidden")
    learner_feedback.classes.discard("is-correct")
    learner_feedback.classes.discard("is-wrong")
    learner_feedback.classes.add("is-correct" if is_correct else "is-wrong")
    feedback_text = (
        "Correct. "
        if is_correct
        else f"Not quite. The correct answer is {answer_text(question, question.answer)}. "
    )
    if recommendation_message:
        feedback_text += " " + recommendation_message
    learner_feedback.textContent = feedback_text


def latest_learner_review_interaction() -> dict | None:
    if not learner_interactions:
        return None
    return learner_interactions[-1]


def learner_stats_items(summary: dict) -> list[tuple[str, str]]:
    items = [
        ("Learning Progress", f'{summary["percent_learned"]}%'),
        ("Ready", str(summary["ready_count"])),
        ("Remaining", str(summary["remaining_count"])),
        ("Due Later", str(summary["due_later_count"])),
    ]
    if session_show_timer:
        items.append(("Time Taken", format_elapsed_time(session_elapsed_seconds)))
    return items


def learner_window_stats(window: list[dict]) -> dict:
    if not window:
        return {
            "size": 0,
            "avg_mastery_gain": 0.0,
            "accuracy": 0.0,
            "avg_meta": 0.0,
            "avg_response_ms": 0.0,
            "avg_grit": 0.0,
        }
    return {
        "size": len(window),
        "avg_mastery_gain": sum(float(item.get("mastery_delta", 0.0) or 0.0) for item in window) / len(window),
        "accuracy": sum(1 for item in window if item.get("is_correct")) / len(window),
        "avg_meta": sum(float(item.get("meta_learning", 0.0) or 0.0) for item in window) / len(window),
        "avg_response_ms": sum(int(item.get("response_ms", 0) or 0) for item in window) / len(window),
        "avg_grit": sum(float(item.get("grit", 0.0) or 0.0) for item in window) / len(window),
    }


def learner_debug_recent_windows(interactions: list[dict]) -> list[dict]:
    if learner_scheduler_module is None:
        return []
    windows: list[dict] = []
    for window_size in learner_scheduler_module.RECOMMENDATION_WINDOW_SIZES:
        if len(interactions) < window_size:
            continue
        stats = dict(learner_window_stats(interactions[-window_size:]))
        stats["window_size"] = window_size
        stats["take_break_signal"] = learner_take_break_signal(stats)
        stats["diminishing_returns_signal"] = learner_diminishing_returns_signal(stats)
        stats["strong_low_yield_signal"] = learner_strong_low_yield_signal(stats)
        windows.append(stats)
    return windows


def learner_debug_question_state_snapshot(question_id: int, now_ms: int, recent_question_ids: list[int] | None = None) -> dict:
    if learner_scheduler_module is None:
        return {}
    state = learner_scheduler_module.question_state(learner_progress, question_id)
    attempts = int(state.get("attempts", 0) or 0)
    correct_attempts = int(state.get("correct_attempts", 0) or 0)
    due_at = int(state.get("due_at", 0) or 0)
    last_seen_at = int(state.get("last_seen_at", 0) or 0)
    updated_at = int(state.get("updated_at", 0) or 0)
    recent_question_ids = recent_question_ids or [item.get("question_id") for item in learner_interactions[-3:]]
    confidence_history = state.get("confidence_history", [])
    if not isinstance(confidence_history, list):
        confidence_history = []
    return {
        "knowledge": round(float(state.get("knowledge", 0.0) or 0.0), 4),
        "meta_learning": round(float(state.get("meta_learning", 0.0) or 0.0), 4),
        "mastery": round(float(state.get("mastery", 0.0) or 0.0), 4),
        "stability": round(float(state.get("stability", 0.0) or 0.0), 4),
        "difficulty": round(float(state.get("difficulty", 0.0) or 0.0), 4),
        "attempts": attempts,
        "correct_attempts": correct_attempts,
        "attempt_accuracy": round((correct_attempts / attempts), 4) if attempts else 0.0,
        "consecutive_correct": int(state.get("consecutive_correct", 0) or 0),
        "consecutive_wrong": int(state.get("consecutive_wrong", 0) or 0),
        "last_result_correct": bool(state.get("last_result_correct", False)),
        "last_answer_ms": int(state.get("last_answer_ms", 0) or 0),
        "last_seen_at": last_seen_at,
        "updated_at": updated_at,
        "last_seen_delta_s": round((now_ms - last_seen_at) / 1000, 1) if last_seen_at > 0 else None,
        "updated_delta_s": round((now_ms - updated_at) / 1000, 1) if updated_at > 0 else None,
        "due_at": due_at,
        "due_in_seconds": round((due_at - now_ms) / 1000, 1) if due_at > 0 else None,
        "due_in_minutes": round((due_at - now_ms) / 60000, 2) if due_at > 0 else None,
        "is_ready": bool(learner_scheduler_module.is_ready(state)),
        "is_mastered": bool(learner_scheduler_module.is_mastered(state)),
        "computed_priority": round(
            learner_scheduler_module.question_priority(state, now_ms, question_id, recent_question_ids),
            4,
        ),
        "confidence_history_tail": confidence_history[-8:],
    }


def learner_debug_checkpoint_snapshot(interaction_count_override: int | None = None) -> dict:
    if learner_scheduler_module is None or not learner_checkpoint_question_ids:
        return {
            "total": 0,
            "complete": False,
            "message": "",
        }

    counts = learner_checkpoint_counts()
    total = counts["total"]
    attempted_count = counts["attempted"]
    ready_needed = counts["ready_needed"]
    baseline_needed = counts["baseline_needed"]
    mastered_needed = counts["mastered_needed"]
    newly_ready_count = counts["newly_ready"]
    newly_baseline_count = counts["newly_baseline"]
    newly_mastered_count = counts["newly_mastered"]
    checkpoint_average_mastery = learner_checkpoint_average_mastery(learner_checkpoint_question_ids)
    checkpoint_average_mastery_gain = checkpoint_average_mastery - learner_checkpoint_baseline_average_mastery
    all_last_attempts_correct = all(
        bool(
            learner_scheduler_module.question_state(learner_progress, question_id).get("last_result_correct", False)
        )
        for question_id in learner_checkpoint_question_ids
    ) if learner_checkpoint_question_ids else False
    checkpoint_display_progress, checkpoint_counts, checkpoint_display_mode = learner_checkpoint_display_progress()
    attempt_count = interaction_count_override if interaction_count_override is not None else len(learner_interactions)
    ready_completion_ratio = 1.0 if ready_needed <= 0 else (newly_ready_count / ready_needed)
    baseline_completion_ratio = 1.0 if baseline_needed <= 0 else (newly_baseline_count / baseline_needed)
    completion_details = learner_checkpoint_completion_details()
    complete = bool(completion_details.get("complete", False))
    message = str(completion_details.get("message", "") or "")
    return {
        "question_ids": list(learner_checkpoint_question_ids),
        "display_mode": checkpoint_display_mode,
        "display_progress": round(checkpoint_display_progress, 4),
        "total": total,
        "attempted": attempted_count,
        "ready": counts["ready"],
        "mastery_ge_0_4": counts["mastery_04"],
        "mastered": counts["mastered"],
        "initial_ready": len(learner_checkpoint_initial_ready_question_ids),
        "initial_baseline": len(learner_checkpoint_initial_baseline_question_ids),
        "initial_mastered": len(learner_checkpoint_initial_mastered_question_ids),
        "ready_needed": ready_needed,
        "baseline_needed": baseline_needed,
        "mastered_needed": mastered_needed,
        "newly_ready": newly_ready_count,
        "newly_baseline": newly_baseline_count,
        "newly_mastered": newly_mastered_count,
        "average_mastery": round(checkpoint_average_mastery, 4),
        "baseline_average_mastery": round(learner_checkpoint_baseline_average_mastery, 4),
        "average_mastery_gain": round(checkpoint_average_mastery_gain, 4),
        "interaction_count": attempt_count,
        "min_attempts_5": attempt_count >= 5,
        "all_attempted": attempted_count == total if total else False,
        "all_last_attempts_correct": all_last_attempts_correct,
        "ready_completion_ratio": round(ready_completion_ratio, 4),
        "ready_ratio_ge_0_8": ready_completion_ratio >= 0.8,
        "baseline_completion_ratio": round(baseline_completion_ratio, 4),
        "baseline_ratio_ge_1_0": baseline_completion_ratio >= 1.0,
        "attempts_gt_45": attempt_count > 45,
        "completion_kind": str(completion_details.get("kind", "") or ""),
        "complete": complete,
        "message": message,
    }


def learner_debug_record_event(
    question: Question,
    selected_answer: str,
    is_correct: bool,
    confidence_value: int,
    response_ms: int,
    interaction: dict,
    update_result: dict,
    recommendation: dict | None,
    checkpoint_before: dict,
    checkpoint_after: dict,
    windows_before: list[dict],
    windows_after: list[dict],
    state_before: dict,
    now_ms: int,
    initial_scheduler_recommendation: dict | None = None,
    post_gate_recommendation: dict | None = None,
    next_question_selection: dict | None = None,
    final_end_reason: str = "",
) -> None:
    global learner_debug_checkpoint_completion_captured, learner_debug_session_end_details

    event = {
        "sequence": len(learner_debug_event_log) + 1,
        "timestamp_ms": now_ms,
        "question_id": question.question_id,
        "question_type": question.question_type,
        "question_text": question.text,
        "selected_answer": selected_answer,
        "selected_answer_text": answer_text(question, selected_answer),
        "correct_answers": list(question.correct_answers),
        "correct_answer_text": answer_text(question, question.answer),
        "is_correct": bool(is_correct),
        "confidence": int(confidence_value),
        "response_ms": int(response_ms),
        "interaction": dict(interaction),
        "update_breakdown": dict(update_result),
        "question_state_before": state_before,
        "question_state_after": learner_debug_question_state_snapshot(
            question.question_id,
            now_ms,
            [item.get("question_id") for item in learner_interactions[-3:]],
        ),
        "windows_before": windows_before,
        "windows_after": windows_after,
        "checkpoint_before": checkpoint_before,
        "checkpoint_after": checkpoint_after,
        "checkpoint_completion_transition": (not checkpoint_before.get("complete", False)) and checkpoint_after.get("complete", False),
        "initial_scheduler_recommendation": dict(initial_scheduler_recommendation or {}),
        "post_gate_recommendation": dict(post_gate_recommendation or {}),
        "recommendation": dict(recommendation or {}),
        "next_question_selection": dict(next_question_selection or {}),
        "final_end_reason": final_end_reason,
    }
    learner_debug_event_log.append(event)
    learner_debug_session_end_details = {
        "initial_scheduler_recommendation": dict(initial_scheduler_recommendation or {}),
        "post_gate_recommendation": dict(post_gate_recommendation or {}),
        "final_recommendation": dict(recommendation or {}),
        "next_question_selection": dict(next_question_selection or {}),
        "final_end_reason": final_end_reason,
    }
    if event["checkpoint_completion_transition"]:
        learner_debug_checkpoint_completion_captured = True


def learner_debug_summary_report_payload(summary: dict, recommendation: dict | None, session_metrics: dict) -> dict:
    end_details = dict(learner_debug_session_end_details or {})
    last_event = learner_debug_event_log[-1] if learner_debug_event_log else {}
    return {
        "summary": summary,
        "recommendation": recommendation or {},
        "initial_scheduler_recommendation": end_details.get("initial_scheduler_recommendation", last_event.get("initial_scheduler_recommendation", {})),
        "post_gate_recommendation": end_details.get("post_gate_recommendation", last_event.get("post_gate_recommendation", {})),
        "final_recommendation": end_details.get("final_recommendation", recommendation or {}),
        "next_question_selection": end_details.get("next_question_selection", last_event.get("next_question_selection", {})),
        "final_end_reason": end_details.get("final_end_reason", last_event.get("final_end_reason", "")),
        "scheduler_runtime_diagnostics": learner_scheduler_runtime_diagnostics(),
        "summary_next_step_diagnostics": learner_summary_next_step_diagnostics(summary, recommendation, session_metrics),
        "session_metrics": session_metrics,
        "final_checkpoint_snapshot": learner_debug_checkpoint_snapshot(),
        "captured_checkpoint_completion": learner_debug_checkpoint_completion_captured,
        "event_log": learner_debug_event_log,
    }


def render_learner_debug_summary_report(summary: dict, recommendation: dict | None, session_metrics: dict) -> None:
    global learner_debug_report_text, learner_debug_previous_values, learner_debug_panel_visible

    payload = learner_debug_summary_report_payload(summary, recommendation, session_metrics)
    learner_debug_report_text = json.dumps(payload, indent=2)
    content = (
        '<section class="learner-debug-section learner-debug-report">'
        '<div class="learner-debug-section-title">Checkpoint Completion Investigation Report</div>'
        f'<pre class="learner-debug-report-pre">{escape(learner_debug_report_text)}</pre>'
        '</section>'
    )
    learner_debug_content.innerHTML = content
    learner_debug_previous_values = {}
    learner_debug_panel_visible = True
    learner_debug_download_button.classes.discard("hidden")
    learner_debug_copy_button.classes.discard("hidden")
    learner_debug_panel.classes.discard("hidden")
    learner_debug_reopen_button.classes.discard("hidden")
    update_learner_debug_popup(content)


def learner_take_break_signal(stats: dict) -> bool:
    return (
        stats["avg_response_ms"] > 20_000
        and (
            stats["accuracy"] < 0.72
            or stats["avg_grit"] < 0.78
            or stats["avg_mastery_gain"] < 0.02
        )
    )


def learner_diminishing_returns_signal(stats: dict) -> bool:
    return (
        stats["avg_mastery_gain"] < 0.015
        and (
            stats["accuracy"] < 0.62
            or stats["avg_meta"] < 0.46
        )
    )


def learner_strong_low_yield_signal(stats: dict) -> bool:
    return (
        stats["avg_mastery_gain"] < 0.01
        and stats["accuracy"] < 0.5
        and stats["avg_meta"] < 0.4
    )


def format_seconds_from_ms(value_ms: float) -> str:
    return f"{round(value_ms / 1000, 1):g}"


def pluralize(count: int, singular: str, plural: str | None = None) -> str:
    return singular if count == 1 else (plural or f"{singular}s")


def learner_due_now_count(scope_question_ids: list[int], now_ms: int) -> int:
    if learner_scheduler_module is None:
        return 0
    due_now_count = 0
    for question_id in scope_question_ids:
        state = learner_scheduler_module.question_state(learner_progress, question_id)
        if (
            not learner_scheduler_module.is_mastered(state)
            or int(state.get("due_at", 0) or 0) <= now_ms
        ):
            due_now_count += 1
    return due_now_count


def learner_scheduler_runtime_diagnostics() -> dict:
    if learner_scheduler_module is None:
        return {}
    diagnostics = {
        "module_file": getattr(learner_scheduler_module, "__file__", ""),
        "choose_next_question_function_id": id(getattr(learner_scheduler_module, "choose_next_question", None)),
    }
    try:
        source = inspect.getsource(learner_scheduler_module.choose_next_question)
        diagnostics["choose_next_question_source_hash"] = hashlib.sha1(source.encode("utf-8")).hexdigest()
        diagnostics["choose_next_question_source_lines"] = len(source.splitlines())
    except Exception as exc:
        diagnostics["choose_next_question_source_error"] = f"{type(exc).__name__}: {exc}"
    return diagnostics


def learner_summary_next_step_diagnostics(summary: dict, recommendation: dict | None, session_metrics: dict) -> dict:
    recommendation = recommendation or {}
    feedback = summary.get("session_feedback", {}) if isinstance(summary, dict) else {}
    next_step = feedback.get("next_step", {}) if isinstance(feedback, dict) else {}
    latest_window = session_metrics.get("latest_window", {})
    strong_low_yield_all = False
    if learner_scheduler_module is not None:
        strong_low_yield_all = (
            session_metrics.get("interaction_count", 0) >= learner_scheduler_module.RECOMMENDATION_WINDOW_SIZES[-1]
            and session_metrics.get("strong_low_yield_window_count", 0) == len(session_metrics.get("recent_windows", []))
            and len(session_metrics.get("recent_windows", [])) == len(learner_scheduler_module.RECOMMENDATION_WINDOW_SIZES)
            and latest_window.get("avg_mastery_gain", 0.0) < 0.012
        )
    mostly_due_later = False
    scope_question_count = session_metrics.get("scope_question_count", 0)
    if scope_question_count:
        mostly_due_later = session_metrics.get("due_now_count", 0) <= max(1, scope_question_count // 10)
    why_not_come_back_later = ""
    if recommendation.get("kind") != "come_back_later":
        why_not_come_back_later = f"final recommendation kind was {recommendation.get('kind', '<none>')}"
    elif not recommendation.get("end_session"):
        why_not_come_back_later = "come_back_later did not survive as an end-session recommendation"
    return {
        "chosen_next_step": dict(next_step or {}),
        "summary_recommendation_kind": recommendation.get("kind", ""),
        "summary_recommendation_end_session": bool(recommendation.get("end_session", False)),
        "strong_low_yield_all": strong_low_yield_all,
        "weak_window_count": session_metrics.get("weak_window_count", 0),
        "strong_low_yield_window_count": session_metrics.get("strong_low_yield_window_count", 0),
        "mostly_due_later": mostly_due_later,
        "accuracy": session_metrics.get("accuracy", 0.0),
        "session_mastery_gain": session_metrics.get("session_mastery_gain", 0.0),
        "recent_grit": session_metrics.get("recent_grit", 0.0),
        "why_next_step_was_take_break": (
            "summary selected Take a Break because strong low-yield or weak-window conditions still held"
            if next_step.get("kind") == "take_break" else ""
        ),
        "why_not_come_back_later": why_not_come_back_later,
    }


def learner_summary_feedback(summary: dict, recommendation: dict | None, session_metrics: dict) -> dict:
    recommendation = recommendation or {}
    if summary.get("percent_learned", 0) >= 100:
        return {
            "base_message": "Checkpoint complete. Your progress has been saved to your Quiz Passport.",
            "positive_messages": ["You've mastered everything for this module!"],
            "next_step": {
                "title": "Test Your Knowledge",
                "message": "Test your knowledge in Quiz Mode.",
                "kind": "quiz_mode",
            },
        }

    positive_messages: list[str] = []
    interaction_count = session_metrics["interaction_count"]
    correct_count = session_metrics["correct_count"]
    wrong_count = session_metrics["wrong_count"]
    accuracy = session_metrics["accuracy"]
    avg_correct_response_ms = session_metrics["avg_correct_response_ms"]
    recovered_questions_count = session_metrics["recovered_questions_count"]
    wrong_high_confidence_rate = session_metrics["wrong_high_confidence_rate"]
    correct_low_confidence_rate = session_metrics["correct_low_confidence_rate"]
    newly_ready = session_metrics["newly_ready"]
    newly_mastered = session_metrics["newly_mastered"]
    first_attempt_ever_count = session_metrics["first_attempt_ever_count"]
    session_mastery_gain = session_metrics["session_mastery_gain"]
    current_grit = session_metrics["current_user_grit"]
    recent_grit = session_metrics["recent_grit"]
    weak_window_count = session_metrics["weak_window_count"]
    due_now_count = session_metrics["due_now_count"]
    scope_question_count = session_metrics["scope_question_count"]
    latest_window = session_metrics["latest_window"]
    end_context = dict(learner_session_end_context or {})
    checkpoint_completion_reason = end_context.get("checkpoint_completion_reason", "")
    initial_kind = ((end_context.get("initial_scheduler_recommendation") or {}).get("kind") or recommendation.get("kind") or "")
    final_kind = ((end_context.get("final_recommendation") or {}).get("kind") or recommendation.get("kind") or "")
    prefer_come_back_later = (
        initial_kind == "come_back_later"
        and final_kind == "checkpoint_reached"
        and checkpoint_completion_reason == "long_session_escape_hatch"
    )

    if recommendation.get("kind") == "checkpoint_reached":
        if checkpoint_completion_reason == "long_session_escape_hatch":
            base_message = "This session reached the long-session checkpoint limit. Your progress has been saved to your Quiz Passport."
        elif newly_ready >= 1:
            base_message = "Checkpoint complete. Your progress has been saved to your Quiz Passport."
        elif session_metrics["newly_baseline"] >= 1:
            base_message = "Checkpoint complete. You built a solid foundation on this session's questions."
        else:
            base_message = "Checkpoint complete. You made meaningful progress across this session's set."
    elif recommendation.get("kind") == "all_learned":
        base_message = "Everything currently due in this area has been learned and saved to your Quiz Passport."
    else:
        base_message = "Your learner progress has been saved and can be downloaded below."

    if newly_mastered >= 3:
        positive_messages.append(
            f"Excellent consolidation: {newly_mastered} {pluralize(newly_mastered, 'question')} reached mastery."
        )
    elif newly_mastered >= 1:
        positive_messages.append(
            f"You mastered {newly_mastered} {pluralize(newly_mastered, 'question')} this session."
        )

    if newly_ready >= 4:
        positive_messages.append(
            f"Strong progress: {newly_ready} {pluralize(newly_ready, 'question')} reached ready this session."
        )
    elif newly_ready >= 1:
        positive_messages.append(
            f"You moved {newly_ready} {pluralize(newly_ready, 'question')} to ready this session."
        )

    if recovered_questions_count >= 3:
        positive_messages.append(
            f"Great recovery: you corrected {recovered_questions_count} questions after getting them wrong earlier."
        )
    elif recovered_questions_count >= 1:
        pronoun = "it" if recovered_questions_count == 1 else "them"
        positive_messages.append(
            f"Nice recovery: you corrected {recovered_questions_count} {pluralize(recovered_questions_count, 'question')} after missing {pronoun} earlier."
        )

    if (
        interaction_count >= 8
        and wrong_high_confidence_rate <= 0.1
        and correct_low_confidence_rate <= 0.2
    ):
        positive_messages.append("Your confidence matched your answers well this session.")

    if interaction_count >= 6 and accuracy >= 0.9 and correct_count >= 8:
        positive_messages.append(f"Excellent accuracy: {round(accuracy * 100)}% correct this session.")
    elif interaction_count >= 6 and accuracy >= 0.8:
        positive_messages.append(
            f"Strong accuracy this session: {correct_count} of {interaction_count} were correct."
        )

    if correct_count >= 5 and avg_correct_response_ms > 0:
        if accuracy >= 0.75 and avg_correct_response_ms <= 6500:
            positive_messages.append(
                f"Fast and accurate recall: your correct answers averaged {format_seconds_from_ms(avg_correct_response_ms)}s."
            )
        elif avg_correct_response_ms <= 8000:
            positive_messages.append(
                f"Fast recall: your average correct response time was {format_seconds_from_ms(avg_correct_response_ms)}s."
            )

    if first_attempt_ever_count >= 3:
        positive_messages.append(
            f"You made progress on new material: {first_attempt_ever_count} new {pluralize(first_attempt_ever_count, 'question')} appeared in this session."
        )

    if (
        wrong_count >= 3
        and (newly_ready >= 1 or newly_mastered >= 1 or recovered_questions_count >= 2)
    ):
        positive_messages.append("Good persistence: you kept improving even after difficult questions.")

    if (
        interaction_count >= 8
        and accuracy >= 0.65
        and weak_window_count == 0
        and latest_window.get("avg_response_ms", 0) <= 16_000
    ):
        positive_messages.append("Steady session: your pace and accuracy stayed consistent.")

    if not positive_messages:
        if prefer_come_back_later or (recommendation.get("kind") == "come_back_later" and recommendation.get("end_session")):
            positive_messages.append("You showed a lot of persistence by sticking with this session even as it got tougher.")
        else:
            positive_messages.append("You made steady progress on this session's questions.")

    deduped_messages: list[str] = []
    for message in positive_messages:
        if message not in deduped_messages:
            deduped_messages.append(message)
    positive_messages = deduped_messages[:3]

    strong_low_yield_all = (
        interaction_count >= learner_scheduler_module.RECOMMENDATION_WINDOW_SIZES[-1]
        and session_metrics["strong_low_yield_window_count"] == len(session_metrics["recent_windows"])
        and len(session_metrics["recent_windows"]) == len(learner_scheduler_module.RECOMMENDATION_WINDOW_SIZES)
        and latest_window.get("avg_mastery_gain", 0.0) < 0.012
    ) if learner_scheduler_module is not None else False
    mostly_due_later = due_now_count <= max(1, scope_question_count // 10) if scope_question_count else False

    next_step = {
        "title": "Keep This Pace",
        "message": "Your pace looks steady. If you continue, sticking with this same rhythm is likely to work well.",
        "kind": "keep_this_pace",
    }

    if prefer_come_back_later or (recommendation.get("kind") == "come_back_later" and recommendation.get("end_session")):
        next_step = {
            "title": "Come Back Later",
            "message": ((end_context.get("initial_scheduler_recommendation") or {}).get("message") or recommendation.get("message") or "You seem to be hitting sustained diminishing returns. This is a good place to pause and come back later, when the next session is more likely to pay off."),
            "kind": "come_back_later",
        }
    elif (
        strong_low_yield_all
        or (
            weak_window_count >= 2
            and recent_grit < 0.9
            and accuracy < 0.6
            and session_mastery_gain < 0.04
        )
    ):
        next_step = {
            "title": "Take a Break",
            "message": "You may be hitting diminishing returns. A short break could help the next stretch feel easier and more productive.",
            "kind": "take_break",
        }
    elif mostly_due_later and summary.get("percent_learned", 0) < 100:
        next_step = {
            "title": "Try Another Module",
            "message": "You've likely taken most of the value available here for now. Consider learning another module before coming back to this one for better recall.",
            "kind": "try_another_module",
        }
    elif (
        interaction_count >= 8
        and current_grit >= 1.05
        and accuracy >= 0.75
        and (session_mastery_gain >= 0.08 or newly_ready >= 2)
        and weak_window_count <= 1
    ):
        next_step = {
            "title": "Push On",
            "message": "You're still gaining strong value from this session. If you want to keep going, now is a good time to push on.",
            "kind": "push_on",
        }

    return {
        "base_message": base_message,
        "positive_messages": positive_messages,
        "next_step": next_step,
    }


def learner_guidance_prompt(interactions: list[dict]) -> dict | None:
    window = interactions[-8:]
    if len(window) < 5:
        return None
    latest = window[-1]

    correct_low_confidence = [
        item for item in window
        if item.get("is_correct") and int(item.get("confidence", -1)) <= 1
    ]
    wrong_high_confidence = [
        item for item in window
        if (not item.get("is_correct")) and int(item.get("confidence", -1)) >= 2
    ]

    if (
        latest.get("is_correct")
        and int(latest.get("confidence", -1)) <= 1
        and
        len(correct_low_confidence) >= 4
        and "correct_low_confidence" not in learner_guidance_shown_kinds
    ):
        return {
            "kind": "correct_low_confidence",
            "title": "You may know more than you think",
            "message": (
                "You’ve been getting several questions right with low confidence. "
                "If you really know the answer, using a higher confidence level will help "
                "the system move you through the module faster."
            ),
        }

    if (
        (not latest.get("is_correct"))
        and int(latest.get("confidence", -1)) >= 2
        and
        len(wrong_high_confidence) >= 3
        and "wrong_high_confidence" not in learner_guidance_shown_kinds
    ):
        return {
            "kind": "wrong_high_confidence",
            "title": "Try leaving more room for uncertainty",
            "message": (
                "You’ve had several wrong answers at high confidence. If you're unsure, "
                "using a lower confidence level will help the system guide you more accurately "
                "and get you through the module faster."
            ),
        }

    return None


def render_learner_summary(summary: dict, recommendation: dict | None = None) -> None:
    recommendation = recommendation or {}
    feedback = summary.get("session_feedback", {})
    learner_summary_title.textContent = summary["headline"]
    learner_summary_subtitle.textContent = feedback.get("base_message") or recommendation.get("message", "") or (
        "Your learner progress has been saved and can be downloaded below."
    )
    learner_summary_value.textContent = f'{summary["percent_learned"]}%'
    learner_summary_detail.textContent = f'{summary["ready_count"]} ready, {summary["remaining_count"]} remaining'
    learner_summary_stats_grid.innerHTML = ""
    for label, value in learner_stats_items(summary):
        learner_summary_stats_grid.append(
            web.div(
                web.div(value, classes=["value"]),
                web.div(label, classes=["label"]),
                classes=["statistic"],
            )
        )
    learner_summary_positive_list.innerHTML = ""
    positive_messages = feedback.get("positive_messages", [])
    if positive_messages:
        learner_summary_positive_section.classes.discard("hidden")
        for message in positive_messages:
            learner_summary_positive_list.append(
                web.div(message, classes=["learner-summary-message-item"])
            )
    else:
        learner_summary_positive_section.classes.add("hidden")

    next_step = feedback.get("next_step", {})
    if next_step.get("title") and next_step.get("message"):
        learner_summary_next_step_section.classes.discard("hidden")
        learner_summary_next_step_title.textContent = next_step["title"]
        learner_summary_next_step_message.textContent = next_step["message"]
    else:
        learner_summary_next_step_section.classes.add("hidden")
        learner_summary_next_step_title.textContent = ""
        learner_summary_next_step_message.textContent = ""
    if summary.get("percent_learned", 0) >= 100:
        learner_summary_continue_button.classes.add("hidden")
    else:
        learner_summary_continue_button.classes.discard("hidden")


def on_learner_guidance_dismiss_click(event) -> None:
    hide_learner_guidance()


async def copy_text_to_clipboard(text: str, success_message: str, empty_message: str) -> None:
    if not text:
        show_toast(empty_message)
        return

    try:
        clipboard = getattr(window.navigator, "clipboard", None)
        if clipboard is not None and hasattr(clipboard, "writeText"):
            await clipboard.writeText(text)
        else:
            raise RuntimeError("Clipboard API unavailable")
    except Exception:
        try:
            textarea = document.createElement("textarea")
            textarea.value = text
            textarea.setAttribute("readonly", "true")
            textarea.style.position = "fixed"
            textarea.style.opacity = "0"
            textarea.style.left = "-9999px"
            document.body.appendChild(textarea)
            textarea.select()
            document.execCommand("copy")
            document.body.removeChild(textarea)
        except Exception:
            show_toast("Copy failed on this device.")
            return

    show_toast(success_message)


def learner_debug_report_filename() -> str:
    now = window.Date.new()
    timestamp = (
        f"{now.getFullYear():04d}-"
        f"{int(now.getMonth()) + 1:02d}-"
        f"{int(now.getDate()):02d}_"
        f"{int(now.getHours()):02d}-"
        f"{int(now.getMinutes()):02d}-"
        f"{int(now.getSeconds()):02d}"
    )
    scope = learner_scope_name or "all"
    safe_scope = "".join(ch.lower() if ch.isalnum() else "_" for ch in scope).strip("_") or "all"
    return f"{timestamp}_{safe_scope}_learner_debug_report.json"


def download_text_payload(text: str, filename: str, empty_message: str) -> None:
    if not text:
        show_toast(empty_message)
        return
    anchor = document.createElement("a")
    anchor.setAttribute(
        "href",
        "data:application/json;charset=utf-8," + quote(text),
    )
    anchor.setAttribute("download", filename)
    anchor.style.display = "none"
    document.body.appendChild(anchor)
    anchor.click()
    document.body.removeChild(anchor)


def on_learner_debug_popout_click(event) -> None:
    open_learner_debug_popup()


def on_learner_debug_download_click(event) -> None:
    download_text_payload(
        learner_debug_report_text,
        learner_debug_report_filename(),
        "There is no learner debug report to download right now.",
    )


def on_learner_debug_copy_click(event) -> None:
    asyncio.create_task(
        copy_text_to_clipboard(
            learner_debug_report_text,
            "Learner debug report copied to clipboard.",
            "There is no learner debug report to copy right now.",
        )
    )


def on_learner_debug_hide_click(event) -> None:
    hide_learner_debug_panel_in_page()


def on_learner_debug_reopen_click(event) -> None:
    show_learner_debug_panel_in_page()


async def enter_learner_hub() -> None:
    await ensure_learner_modules_loaded()
    ensure_learner_progress_loaded()
    render_learner_hub()
    learner_progress_file._dom_element.value = ""
    show_screen("learner-hub")


async def enter_learner_passport_screen() -> None:
    await ensure_learner_modules_loaded()
    ensure_learner_progress_loaded()
    learner_progress_file._dom_element.value = ""
    local_passport_exists = bool(
        window.localStorage.getItem(learner_storage_module.progress_storage_key(QUIZ_ID))
    )
    if local_passport_exists:
        username = learner_username()
        show_learner_import_status(
            f"{username}'s Quiz Passport already exists on this device. Use it, upload a different one, or start fresh.",
            "positive",
        )
        learner_use_current_passport_button.textContent = f"Use {username}'s Passport"
        learner_use_current_passport_button.classes.discard("hidden")
    else:
        hide_learner_import_status()
        learner_use_current_passport_button.textContent = "Use User's Passport"
        learner_use_current_passport_button.classes.add("hidden")
    show_screen("learner-passport")


async def start_learner_session(scope_name: str, restore_payload: dict | None = None) -> None:
    global learner_session_active, learner_scope_name, learner_scope_question_ids
    global learner_checkpoint_question_ids, learner_checkpoint_baseline_average_mastery
    global learner_checkpoint_attempted_question_ids, learner_checkpoint_initial_ready_question_ids
    global learner_checkpoint_initial_baseline_question_ids, learner_checkpoint_initial_mastered_question_ids
    global learner_checkpoint_display_mode_for_session
    global learner_checkpoint_display_mode_for_session
    global learner_interactions, learner_selected_answer, learner_answer_locked
    global learner_question_started_at_ms, session_question_ids, answers, current_index
    global session_advanced_options_enabled, session_selected_knowledge_areas
    global session_show_timer, session_learner_mode, session_timer_started_at_ms
    global learner_pending_next_question_id, learner_pending_recommendation
    global learner_guidance_kind, learner_guidance_shown_kinds
    global learner_review_mode, learner_review_return_state
    global learner_selected_confidence, multi_select_focus_key

    await ensure_learner_modules_loaded()
    ensure_learner_progress_loaded()
    clear_draft_attempt()

    learner_scope_name = scope_name
    learner_scope_question_ids = learner_scope_ids(scope_name)
    learner_checkpoint_question_ids = []
    learner_checkpoint_baseline_average_mastery = 0.0
    learner_checkpoint_attempted_question_ids = set()
    learner_checkpoint_initial_ready_question_ids = set()
    learner_checkpoint_initial_baseline_question_ids = set()
    learner_checkpoint_initial_mastered_question_ids = set()
    learner_checkpoint_display_mode_for_session = "ready"
    learner_checkpoint_display_mode_for_session = "ready"
    learner_session_active = True
    reset_learner_debug_unlock()
    reset_learner_debug_capture_state()
    hide_learner_guidance()
    if not restore_payload:
        learner_guidance_kind = ""
        learner_guidance_shown_kinds = set()
    learner_interactions = list(restore_payload.get("interactions", [])) if restore_payload else []
    learner_selected_answer = (
        normalized_saved_response(restore_payload.get("selected_answer"))
        if restore_payload
        else None
    )
    learner_answer_locked = bool(restore_payload.get("answer_locked", False)) if restore_payload else False
    learner_pending_next_question_id = (
        int(restore_payload.get("pending_next_question_id"))
        if restore_payload and restore_payload.get("pending_next_question_id") is not None
        else None
    )
    learner_pending_recommendation = (
        dict(restore_payload.get("pending_recommendation", {}))
        if restore_payload and isinstance(restore_payload.get("pending_recommendation"), dict)
        else None
    )
    learner_review_mode = bool(restore_payload.get("review_mode", False)) if restore_payload else False
    learner_review_return_state = (
        dict(restore_payload.get("review_return_state", {}))
        if restore_payload and isinstance(restore_payload.get("review_return_state"), dict)
        else None
    )
    learner_selected_confidence = (
        int(restore_payload.get("selected_confidence"))
        if restore_payload and restore_payload.get("selected_confidence") is not None
        else None
    )
    multi_select_focus_key = (
        str(restore_payload.get("multi_select_focus_key"))
        if restore_payload and restore_payload.get("multi_select_focus_key")
        else None
    )

    session_advanced_options_enabled = True
    session_selected_knowledge_areas = []
    session_show_timer = (
        bool(restore_payload.get("session_show_timer", False))
        if restore_payload
        else (advanced_options_enabled and bool(show_timer_toggle._dom_element.checked))
    )
    session_learner_mode = True
    session_timer_started_at_ms = (
        float(restore_payload.get("session_timer_started_at_ms"))
        if restore_payload and restore_payload.get("session_timer_started_at_ms") is not None
        else (float(window.Date.now()) if session_show_timer else None)
    )
    start_timer_updates()
    reset_quiz_screen_for_mode()
    start_learner_debug_updates()

    next_question_id = None
    now_ms = int(window.Date.now())
    if restore_payload is not None:
        try:
            learner_checkpoint_question_ids = [
                int(question_id) for question_id in restore_payload.get("checkpoint_question_ids", [])
            ]
        except Exception:
            learner_checkpoint_question_ids = []
        learner_checkpoint_baseline_average_mastery = float(
            restore_payload.get("checkpoint_baseline_average_mastery", 0.0) or 0.0
        )
        learner_checkpoint_attempted_question_ids = {
            int(question_id)
            for question_id in restore_payload.get("checkpoint_attempted_question_ids", [])
        }
        learner_checkpoint_initial_ready_question_ids = {
            int(question_id)
            for question_id in restore_payload.get("checkpoint_initial_ready_question_ids", [])
        }
        learner_checkpoint_initial_baseline_question_ids = {
            int(question_id)
            for question_id in restore_payload.get("checkpoint_initial_baseline_question_ids", [])
        }
        learner_checkpoint_initial_mastered_question_ids = {
            int(question_id)
            for question_id in restore_payload.get("checkpoint_initial_mastered_question_ids", [])
        }
        learner_checkpoint_display_mode_for_session = str(
            restore_payload.get("checkpoint_display_mode_for_session", "ready") or "ready"
        )
    if not learner_checkpoint_question_ids:
        learner_checkpoint_question_ids = learner_scheduler_module.select_checkpoint_question_ids(
            learner_progress,
            learner_scope_question_ids,
            now_ms,
            count=learner_checkpoint_target(len(learner_scope_question_ids)),
        )
        learner_checkpoint_baseline_average_mastery = learner_checkpoint_average_mastery(
            learner_checkpoint_question_ids
        )
        (
            learner_checkpoint_initial_ready_question_ids,
            learner_checkpoint_initial_baseline_question_ids,
            learner_checkpoint_initial_mastered_question_ids,
        ) = learner_checkpoint_initial_state_sets(learner_checkpoint_question_ids)
        initial_ready_ratio = (
            len(learner_checkpoint_initial_ready_question_ids) / len(learner_checkpoint_question_ids)
            if learner_checkpoint_question_ids else 0.0
        )
        learner_checkpoint_display_mode_for_session = (
            "mastered" if initial_ready_ratio > 0.75 else "ready"
        )
    elif (
        not learner_checkpoint_initial_ready_question_ids
        and not learner_checkpoint_initial_baseline_question_ids
        and not learner_checkpoint_initial_mastered_question_ids
    ):
        (
            learner_checkpoint_initial_ready_question_ids,
            learner_checkpoint_initial_baseline_question_ids,
            learner_checkpoint_initial_mastered_question_ids,
        ) = learner_checkpoint_initial_state_sets(learner_checkpoint_question_ids)
        initial_ready_ratio = (
            len(learner_checkpoint_initial_ready_question_ids) / len(learner_checkpoint_question_ids)
            if learner_checkpoint_question_ids else 0.0
        )
        learner_checkpoint_display_mode_for_session = (
            "mastered" if initial_ready_ratio > 0.75 else "ready"
        )
    if restore_payload is not None:
        try:
            next_question_id = int(restore_payload.get("current_question_id") or 0)
        except Exception:
            next_question_id = None

    if next_question_id not in learner_checkpoint_question_ids:
        next_question_id = learner_scheduler_module.choose_next_question(
            learner_progress,
            learner_checkpoint_question_ids,
            now_ms,
            [item.get("question_id") for item in learner_interactions[-3:]],
        )

    if next_question_id is None:
        await end_learner_session({"message": "There are no questions available for this learner scope.", "end_session": True})
        return

    session_question_ids = [next_question_id]
    answers = {}
    current_index = 0
    learner_question_started_at_ms = float(window.Date.now())
    save_learner_session_draft()
    await render_current_question()
    show_screen("quiz")
    hide_status()


async def maybe_restore_learner_session() -> bool:
    if not QUIZ_ID:
        return False
    if not window.localStorage.getItem(f"quizurself_learner_session_{QUIZ_ID}_v1"):
        return False

    await ensure_learner_modules_loaded()
    ensure_learner_progress_loaded()
    draft = learner_storage_module.load_session(window, QUIZ_ID)
    if not draft:
        return False

    scope_name = str(draft.get("scope_name", "") or "")
    if not scope_name:
        clear_learner_session_draft()
        return False

    try:
        restored_scope_ids = [int(question_id) for question_id in draft.get("scope_question_ids", [])]
    except Exception:
        clear_learner_session_draft()
        return False

    if restored_scope_ids != learner_scope_ids(scope_name):
        restored_scope_ids = learner_scope_ids(scope_name)
    draft["scope_question_ids"] = restored_scope_ids
    try:
        restored_checkpoint_ids = [int(question_id) for question_id in draft.get("checkpoint_question_ids", [])]
    except Exception:
        restored_checkpoint_ids = []
    draft["checkpoint_question_ids"] = [
        question_id for question_id in restored_checkpoint_ids if question_id in restored_scope_ids
    ]
    draft["checkpoint_baseline_average_mastery"] = float(
        draft.get("checkpoint_baseline_average_mastery", 0.0) or 0.0
    )
    try:
        restored_attempted_question_ids = [
            int(question_id) for question_id in draft.get("checkpoint_attempted_question_ids", [])
        ]
    except Exception:
        restored_attempted_question_ids = []
    draft["checkpoint_attempted_question_ids"] = [
        question_id for question_id in restored_attempted_question_ids if question_id in draft["checkpoint_question_ids"]
    ]
    try:
        restored_initial_ready_question_ids = [
            int(question_id) for question_id in draft.get("checkpoint_initial_ready_question_ids", [])
        ]
    except Exception:
        restored_initial_ready_question_ids = []
    draft["checkpoint_initial_ready_question_ids"] = [
        question_id for question_id in restored_initial_ready_question_ids if question_id in draft["checkpoint_question_ids"]
    ]
    try:
        restored_initial_baseline_question_ids = [
            int(question_id) for question_id in draft.get("checkpoint_initial_baseline_question_ids", [])
        ]
    except Exception:
        restored_initial_baseline_question_ids = []
    draft["checkpoint_initial_baseline_question_ids"] = [
        question_id for question_id in restored_initial_baseline_question_ids if question_id in draft["checkpoint_question_ids"]
    ]
    try:
        restored_initial_mastered_question_ids = [
            int(question_id) for question_id in draft.get("checkpoint_initial_mastered_question_ids", [])
        ]
    except Exception:
        restored_initial_mastered_question_ids = []
    draft["checkpoint_initial_mastered_question_ids"] = [
        question_id for question_id in restored_initial_mastered_question_ids if question_id in draft["checkpoint_question_ids"]
    ]
    checkpoint_display_mode_for_session = str(
        draft.get("checkpoint_display_mode_for_session", "ready") or "ready"
    )
    draft["checkpoint_display_mode_for_session"] = (
        checkpoint_display_mode_for_session
        if checkpoint_display_mode_for_session in {"ready", "mastered"}
        else "ready"
    )

    show_status("Restoring learner session...")
    try:
        await start_learner_session(scope_name, restore_payload=draft)
    except Exception:
        clear_learner_session_draft()
        raise
    hide_status()
    return True


async def handle_learner_confidence(confidence_value: int) -> None:
    global learner_answer_locked, learner_pending_next_question_id, learner_pending_recommendation
    global learner_selected_confidence, learner_session_end_context

    if (
        not learner_session_active
        or not session_question_ids
        or learner_selected_answer is None
        or learner_answer_locked
    ):
        return

    question_id = session_question_ids[0]
    question = await load_question(question_id)
    now_ms = int(window.Date.now())
    started_at_ms = int(learner_question_started_at_ms or now_ms)
    response_ms = max(0, now_ms - started_at_ms)
    is_correct = response_is_correct(question, learner_selected_answer)
    debug_was_open = learner_debug_is_open()
    state_before = learner_debug_question_state_snapshot(question_id, now_ms) if debug_was_open else {}

    update_result = learner_scheduler_module.update_after_response(
        learner_progress,
        question_id,
        is_correct,
        confidence_value,
        response_ms,
        now_ms,
    )
    checkpoint_before = learner_debug_checkpoint_snapshot(len(learner_interactions)) if debug_was_open else {}
    windows_before = learner_debug_recent_windows(learner_interactions) if debug_was_open else []
    interaction = {
        "question_id": question_id,
        "selected_answer": learner_selected_answer,
        "is_correct": is_correct,
        "confidence": confidence_value,
        "response_ms": response_ms,
        "mastery_delta": update_result["mastery_delta"],
        "meta_learning": update_result["meta_learning"],
        "grit": update_result["grit"],
        "recovered_question": bool(update_result.get("recovered_question")),
        "first_attempt_ever": bool(update_result.get("first_attempt_ever")),
    }
    learner_interactions.append(interaction)
    learner_checkpoint_attempted_question_ids.add(question_id)
    save_learner_progress()

    guidance_prompt = learner_guidance_prompt(learner_interactions)
    if guidance_prompt is not None:
        show_learner_guidance(
            guidance_prompt["kind"],
            guidance_prompt["title"],
            guidance_prompt["message"],
        )

    recommendation = learner_scheduler_module.recommendation_for_session(
        learner_interactions,
        learner_progress,
        learner_checkpoint_question_ids,
        now_ms,
    )
    initial_scheduler_recommendation = dict(recommendation or {})
    checkpoint_progress, checkpoint_target = learner_checkpoint_status()
    checkpoint_completion = learner_checkpoint_completion_details()
    checkpoint_reached = bool(checkpoint_completion.get("complete", False))
    checkpoint_message = str(checkpoint_completion.get("message", "") or "")
    checkpoint_counts = learner_checkpoint_counts()
    checkpoint_attempted_count = checkpoint_counts.get("attempted", 0)
    checkpoint_attempt_ratio = (
        checkpoint_attempted_count / checkpoint_target
        if checkpoint_target
        else 0.0
    )
    recent_question_ids = [item.get("question_id") for item in learner_interactions[-3:]]
    checkpoint_completion_reason = str(checkpoint_completion.get("kind", "") or "")
    next_question_id = None
    final_end_reason = "continue_session"
    if checkpoint_reached:
        recommendation = {
            "kind": "checkpoint_reached",
            "message": checkpoint_message,
            "end_session": True,
        }
        final_end_reason = f"checkpoint_reached:{checkpoint_completion_reason or 'unknown'}"
    elif recommendation.get("kind") == "come_back_later" and (
        len(learner_interactions) < 30
        or checkpoint_attempt_ratio < 0.8
    ):
        recommendation = {
            "kind": "take_break",
            "message": "You may be hitting diminishing returns. You can keep going, but a short break might help the next stretch feel easier.",
            "end_session": False,
        }
    elif not recommendation.get("end_session"):
        next_question_id = None

    post_gate_recommendation = dict(recommendation or {})
    if not recommendation.get("end_session") and hasattr(learner_scheduler_module, "choose_next_question_diagnostics"):
        next_question_selection = learner_scheduler_module.choose_next_question_diagnostics(
            learner_progress,
            learner_checkpoint_question_ids,
            now_ms,
            recent_question_ids,
        )
        next_question_id = next_question_selection.get("selected_next_question_id")
        next_question_selection["selection_attempted"] = True
    else:
        next_question_selection = {
            "checkpoint_question_ids_at_selection_time": list(learner_checkpoint_question_ids),
            "checkpoint_question_count_at_selection_time": len(learner_checkpoint_question_ids),
            "recent_question_ids": list(recent_question_ids),
            "selected_next_question_id": next_question_id,
            "selection_attempted": not bool(recommendation.get("end_session")),
        }

    if next_question_id is None and not recommendation.get("end_session"):
        recommendation = {
            "message": "You've learned everything currently due in this area.",
            "end_session": True,
        }
        final_end_reason = "no_next_question_available"
    elif recommendation.get("end_session"):
        final_end_reason = str(recommendation.get("kind") or "recommendation_end_session")

    learner_session_end_context = {
        "initial_scheduler_recommendation": dict(initial_scheduler_recommendation or {}),
        "post_gate_recommendation": dict(post_gate_recommendation or {}),
        "final_recommendation": dict(recommendation or {}),
        "final_end_reason": final_end_reason,
        "checkpoint_completion_reason": checkpoint_completion_reason,
        "checkpoint_attempt_ratio": checkpoint_attempt_ratio,
        "interaction_count": len(learner_interactions),
    }

    if debug_was_open:
        learner_debug_record_event(
            question,
            learner_selected_answer,
            is_correct,
            confidence_value,
            response_ms,
            interaction,
            update_result,
            recommendation,
            checkpoint_before,
            learner_debug_checkpoint_snapshot(len(learner_interactions)),
            windows_before,
            learner_debug_recent_windows(learner_interactions),
            state_before,
            now_ms,
            initial_scheduler_recommendation=initial_scheduler_recommendation,
            post_gate_recommendation=post_gate_recommendation,
            next_question_selection=next_question_selection,
            final_end_reason=final_end_reason,
        )

    learner_answer_locked = True
    learner_selected_confidence = confidence_value
    learner_pending_next_question_id = next_question_id
    learner_pending_recommendation = recommendation
    queue_learner_question_prefetch(
        None if recommendation.get("end_session") else learner_pending_next_question_id
    )
    save_learner_session_draft()
    await render_current_question()


async def end_learner_session(recommendation: dict | None = None) -> None:
    global learner_session_active, learner_selected_answer, learner_answer_locked
    global learner_summary_payload, learner_session_end_context
    global learner_checkpoint_question_ids, learner_checkpoint_baseline_average_mastery
    global learner_checkpoint_attempted_question_ids, learner_checkpoint_initial_ready_question_ids
    global learner_checkpoint_initial_baseline_question_ids, learner_checkpoint_initial_mastered_question_ids
    global learner_checkpoint_display_mode_for_session
    global learner_prefetch_task, learner_prefetched_question_id
    global learner_pending_next_question_id, learner_pending_recommendation
    global learner_selected_confidence
    global multi_select_focus_key

    if learner_mode_module is None:
        return

    preserve_debug_for_summary = learner_debug_is_open()

    update_session_elapsed_time()
    stop_timer_updates()
    stop_learner_debug_updates()
    hide_session_timer()
    now_ms = int(window.Date.now())
    checkpoint_counts = learner_checkpoint_counts()
    recent_windows = [
        learner_window_stats(learner_interactions[-window_size:])
        for window_size in learner_scheduler_module.RECOMMENDATION_WINDOW_SIZES
        if len(learner_interactions) >= window_size
    ] if learner_scheduler_module is not None else []
    latest_window = recent_windows[0] if recent_windows else learner_window_stats(learner_interactions)
    correct_items = [item for item in learner_interactions if item.get("is_correct")]
    correct_count = len(correct_items)
    interaction_count = len(learner_interactions)
    wrong_count = max(0, interaction_count - correct_count)
    accuracy = (correct_count / interaction_count) if interaction_count else 0.0
    avg_correct_response_ms = (
        sum(int(item.get("response_ms", 0) or 0) for item in correct_items) / correct_count
        if correct_count else 0.0
    )
    recovered_questions_count = sum(1 for item in learner_interactions if item.get("recovered_question"))
    first_attempt_ever_count = sum(1 for item in learner_interactions if item.get("first_attempt_ever"))
    wrong_high_confidence_count = sum(
        1 for item in learner_interactions
        if (not item.get("is_correct")) and int(item.get("confidence", -1)) >= 2
    )
    correct_low_confidence_count = sum(
        1 for item in learner_interactions
        if item.get("is_correct") and int(item.get("confidence", -1)) <= 1
    )
    session_mastery_gain = sum(float(item.get("mastery_delta", 0.0) or 0.0) for item in learner_interactions)
    current_user_grit = (
        learner_scheduler_module.current_user_grit(learner_progress, now_ms)
        if learner_scheduler_module is not None
        else 0.0
    )
    weak_window_count = sum(
        1
        for stats in recent_windows
        if learner_take_break_signal(stats) or learner_diminishing_returns_signal(stats)
    )
    strong_low_yield_window_count = sum(
        1 for stats in recent_windows if learner_strong_low_yield_signal(stats)
    )
    session_metrics = {
        "interaction_count": interaction_count,
        "correct_count": correct_count,
        "wrong_count": wrong_count,
        "accuracy": accuracy,
        "avg_correct_response_ms": avg_correct_response_ms,
        "recovered_questions_count": recovered_questions_count,
        "first_attempt_ever_count": first_attempt_ever_count,
        "wrong_high_confidence_rate": (wrong_high_confidence_count / interaction_count) if interaction_count else 0.0,
        "correct_low_confidence_rate": (correct_low_confidence_count / correct_count) if correct_count else 0.0,
        "newly_ready": checkpoint_counts.get("newly_ready", 0),
        "newly_mastered": checkpoint_counts.get("newly_mastered", 0),
        "newly_baseline": checkpoint_counts.get("newly_baseline", 0),
        "session_mastery_gain": session_mastery_gain,
        "current_user_grit": current_user_grit,
        "recent_grit": latest_window.get("avg_grit", current_user_grit),
        "weak_window_count": weak_window_count,
        "strong_low_yield_window_count": strong_low_yield_window_count,
        "recent_windows": recent_windows,
        "latest_window": latest_window,
        "due_now_count": learner_due_now_count(learner_scope_question_ids or all_question_ids(), now_ms),
        "scope_question_count": len(learner_scope_question_ids or all_question_ids()),
    }
    learner_session_active = False
    if learner_prefetch_task is not None and not learner_prefetch_task.done():
        learner_prefetch_task.cancel()
    learner_prefetch_task = None
    learner_prefetched_question_id = None
    hide_learner_guidance()
    learner_selected_answer = None
    learner_answer_locked = False
    learner_pending_next_question_id = None
    learner_pending_recommendation = None
    learner_selected_confidence = None
    multi_select_focus_key = None
    learner_checkpoint_question_ids = []
    learner_checkpoint_baseline_average_mastery = 0.0
    learner_checkpoint_attempted_question_ids = set()
    learner_checkpoint_initial_ready_question_ids = set()
    learner_checkpoint_initial_baseline_question_ids = set()
    learner_checkpoint_initial_mastered_question_ids = set()
    learner_checkpoint_display_mode_for_session = "ready"
    if not preserve_debug_for_summary:
        hide_learner_debug_panel()
        close_learner_debug_popup()
        reset_learner_debug_unlock()
        reset_learner_debug_capture_state()
    clear_learner_session_draft()
    save_learner_progress()

    summary = learner_mode_module.summary_for_scope(
        learner_scope_name or "__all__",
        learner_scope_question_ids or all_question_ids(),
        learner_progress,
    )
    summary["session_feedback"] = learner_summary_feedback(summary, recommendation, session_metrics)
    learner_summary_payload = {"summary": summary, "recommendation": recommendation or {}}
    render_learner_summary(summary, recommendation)
    show_screen("learner-summary")
    if preserve_debug_for_summary and learner_debug_event_log:
        render_learner_debug_summary_report(summary, recommendation, session_metrics)


async def leave_learner_session_to_hub() -> None:
    global learner_session_active, learner_selected_answer, learner_answer_locked
    global learner_checkpoint_question_ids, learner_checkpoint_baseline_average_mastery
    global learner_checkpoint_attempted_question_ids, learner_checkpoint_initial_ready_question_ids
    global learner_checkpoint_initial_baseline_question_ids, learner_checkpoint_initial_mastered_question_ids
    global learner_pending_next_question_id, learner_pending_recommendation
    global learner_selected_confidence

    update_session_elapsed_time()
    stop_timer_updates()
    stop_learner_debug_updates()
    hide_session_timer()
    learner_session_active = False
    hide_learner_guidance()
    learner_selected_answer = None
    learner_answer_locked = False
    learner_pending_next_question_id = None
    learner_pending_recommendation = None
    learner_selected_confidence = None
    learner_checkpoint_question_ids = []
    learner_checkpoint_baseline_average_mastery = 0.0
    learner_checkpoint_attempted_question_ids = set()
    learner_checkpoint_initial_ready_question_ids = set()
    learner_checkpoint_initial_baseline_question_ids = set()
    learner_checkpoint_initial_mastered_question_ids = set()
    hide_learner_debug_panel()
    close_learner_debug_popup()
    reset_learner_debug_unlock()
    reset_learner_debug_capture_state()
    clear_learner_session_draft()
    save_learner_progress()
    await enter_learner_hub()


async def _fetch_question(question_id: int) -> Question:
    payload = await fetch_json(QUESTION_PATH_TEMPLATE.format(question_id=question_id))
    indexed_metadata = question_bank_index.get(question_id, {})
    metadata = question_metadata_from_payload(payload, indexed_metadata)
    question_type = normalized_question_type(payload.get("question_type"))
    correct_answers_raw = payload.get("correct_answers")
    if isinstance(correct_answers_raw, list):
        correct_answers = [str(answer_key) for answer_key in correct_answers_raw if str(answer_key)]
    else:
        legacy_answer = payload.get("answer")
        if isinstance(legacy_answer, list):
            correct_answers = [str(answer_key) for answer_key in legacy_answer if str(answer_key)]
        elif legacy_answer:
            correct_answers = [str(legacy_answer)]
        else:
            correct_answers = []
    question = Question(
        question_id=int(payload["id"]),
        text=payload["question"],
        image=payload["image"],
        question_type=question_type,
        options=list(payload["options"]),
        correct_answers=correct_answers,
        answer=correct_answers[0] if len(correct_answers) == 1 else list(correct_answers),
        metadata=metadata,
    )
    question_cache[question_id] = question
    return question


async def load_question(question_id: int) -> Question:
    if question_id in question_cache:
        return question_cache[question_id]

    existing_task = question_load_tasks.get(question_id)
    if existing_task is not None:
        return await asyncio.shield(existing_task)

    task = asyncio.create_task(_fetch_question(question_id))
    question_load_tasks[question_id] = task
    try:
        return await asyncio.shield(task)
    finally:
        if question_load_tasks.get(question_id) is task:
            question_load_tasks.pop(question_id, None)


async def _run_learner_question_prefetch(question_id: int) -> None:
    global learner_prefetched_question_id

    try:
        await load_question(question_id)
        learner_prefetched_question_id = question_id
    except asyncio.CancelledError:
        raise
    except Exception:
        # Prefetch should never interrupt learner flow.
        learner_prefetched_question_id = None


def queue_learner_question_prefetch(question_id: int | None) -> None:
    global learner_prefetch_task, learner_prefetched_question_id

    if learner_prefetch_task is not None and not learner_prefetch_task.done():
        learner_prefetch_task.cancel()
    learner_prefetch_task = None

    if question_id is None:
        learner_prefetched_question_id = None
        return

    if learner_prefetched_question_id == question_id or question_id in question_cache:
        learner_prefetched_question_id = question_id
        return

    learner_prefetched_question_id = None
    learner_prefetch_task = asyncio.create_task(_run_learner_question_prefetch(question_id))


async def prefetch_upcoming_questions() -> None:
    end_index = min(len(session_question_ids), current_index + 1 + PREFETCH_COUNT)
    for index in range(current_index + 1, end_index):
        question_id = session_question_ids[index]
        if question_id not in question_cache:
            await load_question(question_id)


def question_count_value(maximum: int | None = None) -> int:
    total = int(quiz_index["question_count"])
    upper_bound = total if maximum is None else max(1, min(total, maximum))

    try:
        value = int(count_input.value or "20")
    except ValueError:
        value = 20

    value = max(1, min(upper_bound, value))
    count_input.value = str(value)
    return value


def normalized_question_type(value: str | None) -> str:
    question_type = (value or "").strip()
    return question_type or DEFAULT_QUESTION_TYPE


def question_is_multi_select(question: Question) -> bool:
    return question.question_type.startswith("multi_select")


def question_type_display_label(question: Question) -> str:
    question_type = normalized_question_type(question.question_type)
    if question_type == DEFAULT_QUESTION_TYPE:
        return ""
    if question_type.startswith("multi_select"):
        return "Multi Select"
    if question_type.startswith("single_select"):
        return "Extended Single Select"
    return " ".join(part.capitalize() for part in question_type.split("_"))


def question_answer_keys(question: Question) -> list[str]:
    if getattr(question, "correct_answers", None):
        return [str(answer_key) for answer_key in question.correct_answers if str(answer_key)]
    answer_value = getattr(question, "answer", None)
    if isinstance(answer_value, list):
        return [str(answer_key) for answer_key in answer_value if str(answer_key)]
    if answer_value:
        return [str(answer_value)]
    return []


def normalized_response_value(question: Question, response):
    if response is None:
        return None
    if question_is_multi_select(question):
        keys = []
        for option in question.options:
            option_key = option["key"]
            if isinstance(response, list):
                if option_key in response and option_key not in keys:
                    keys.append(option_key)
            elif response == option_key:
                keys.append(option_key)
        return keys or None
    if isinstance(response, list):
        for option in question.options:
            if option["key"] in response:
                return option["key"]
        return None
    response_text = str(response or "")
    valid_keys = {option["key"] for option in question.options}
    return response_text if response_text in valid_keys else None


def response_keys(question: Question, response) -> list[str]:
    normalized = normalized_response_value(question, response)
    if normalized is None:
        return []
    if isinstance(normalized, list):
        return normalized
    return [normalized]


def response_complete(question: Question, response) -> bool:
    return bool(response_keys(question, response))


def response_is_correct(question: Question, response) -> bool:
    return response_keys(question, response) == question_answer_keys(question)


def toggled_response(question: Question, response, option_key: str):
    if question_is_multi_select(question):
        current_keys = response_keys(question, response)
        if option_key in current_keys:
            updated = [key for key in current_keys if key != option_key]
        else:
            updated = [
                option["key"]
                for option in question.options
                if option["key"] in current_keys or option["key"] == option_key
            ]
        return updated or None
    return option_key


def answer_text(question: Question, answer_value) -> str:
    answer_keys = response_keys(question, answer_value)
    if not answer_keys:
        return ""

    option_map = {option["key"]: option["text"] for option in question.options}
    formatted = [
        f"{answer_key}. {option_map.get(answer_key, answer_key)}"
        for answer_key in answer_keys
    ]
    return ", ".join(formatted)


def learner_dev_answer_key(question: Question, correct: bool) -> str | None:
    if correct:
        answer_keys = question_answer_keys(question)
        return answer_keys[0] if answer_keys else None

    for option in question.options:
        if option["key"] not in question_answer_keys(question):
            return option["key"]
    return None


def escape(text: str) -> str:
    return html.escape(text or "")


def render_options(question: Question, selected_answer) -> None:
    options_host.innerHTML = ""
    multi_select_indicator.innerHTML = ""
    multi_select_indicator.classes.add("hidden")
    selected_keys = response_keys(question, selected_answer)
    focused_multi_select_key = rendered_multi_select_focus_key(question)
    is_multi_select = question_is_multi_select(question)

    for option in question.options:
        option_key = option["key"]

        def choose_option(event, answer_key=option_key) -> None:
            global learner_selected_answer, learner_answer_locked
            global learner_selected_confidence, multi_select_focus_key

            if learner_session_active and learner_answer_locked:
                return

            if learner_session_active:
                multi_select_focus_key = answer_key if question_is_multi_select(question) else None
                learner_selected_answer = toggled_response(
                    question,
                    learner_selected_answer,
                    answer_key,
                )
                learner_selected_confidence = None
                save_learner_session_draft()
                asyncio.create_task(render_current_question())
                return

            updated_response = toggled_response(
                question,
                answers.get(question.question_id),
                answer_key,
            )
            multi_select_focus_key = answer_key if question_is_multi_select(question) else None
            if updated_response is None:
                answers.pop(question.question_id, None)
            else:
                answers[question.question_id] = updated_response
            save_draft_attempt()
            asyncio.create_task(render_current_question())

        option_children = [
            web.span(option_key, classes=["option-key"]),
            web.span(option["text"], classes=["option-text"]),
        ]
        if is_multi_select:
            checkbox_classes = ["multi-select-option-box"]
            checkbox_symbol = "☐"
            if option_key in selected_keys:
                checkbox_classes.append("checked")
                checkbox_symbol = "☑"
            if (
                learner_session_active
                and learner_answer_locked
                and option_key in selected_keys
                and option_key not in question_answer_keys(question)
            ):
                checkbox_classes.append("crossed")
                checkbox_symbol = "☒"
            option_children.append(
                web.span(
                    checkbox_symbol,
                    classes=checkbox_classes,
                )
            )

        option_item = web.a(
            *option_children,
            classes=["item", "question-option"],
            on_click=choose_option,
        )

        if option_key in selected_keys:
            option_item.classes.add("selected")
        if is_multi_select and option_key == focused_multi_select_key:
            option_item.classes.add("keyboard-focus")

        if learner_session_active and learner_answer_locked:
            if option_key in question_answer_keys(question):
                option_item.classes.add("positive")
            elif option_key in selected_keys:
                option_item.classes.add("negative")

        options_host.append(option_item)

    if is_multi_select:
        multi_select_indicator.append(
            web.span("!", classes=["multi-select-indicator-box"]),
            web.span("Select all that apply", classes=["multi-select-indicator-text"]),
        )
        multi_select_indicator.classes.discard("hidden")


def render_question_metadata(question: Question) -> None:
    if (
        not session_advanced_options_enabled
        or not FEATURE_FLAGS.get("metadata_panel", True)
        or not QUESTION_PANEL_FIELDS
    ):
        question_metadata_panel.innerHTML = ""
        question_metadata_panel.classes.add("hidden")
        question_metadata_toggle.classes.add("hidden")
        return

    question_metadata_toggle.classes.discard("hidden")
    question_metadata_toggle.textContent = ">" if question_metadata_collapsed else "v"
    question_metadata_toggle._dom_element.setAttribute(
        "aria-expanded",
        "false" if question_metadata_collapsed else "true",
    )

    if question_metadata_collapsed:
        question_metadata_panel.innerHTML = ""
        question_metadata_panel.classes.add("hidden")
        return

    question_metadata_panel.innerHTML = "".join(
        (
            '<div class="question-metadata-item">'
            f"<strong>{escape(field.get('label', field['key']))}:</strong> "
            f"{escape(question_metadata_value(question, field['key'], field.get('empty_value', '')))}"
            "</div>"
        )
        for field in QUESTION_PANEL_FIELDS
    )
    question_metadata_panel.classes.discard("hidden")


async def render_current_question() -> None:
    global learner_question_started_at_ms

    question_id = session_question_ids[current_index]
    question = await load_question(question_id)
    render_learner_debug_panel(question_id)

    total = len(session_question_ids)
    position = current_index + 1
    selected_answer = learner_selected_answer if learner_session_active else answers.get(question.question_id)
    progress_percent = round((position / total) * 100) if total else 0

    if learner_session_active:
        _checkpoint_progress, checkpoint_target = learner_checkpoint_status()
        checkpoint_display_progress, checkpoint_counts, checkpoint_display_mode = learner_checkpoint_display_progress()
        progress_percent = min(100, round(checkpoint_display_progress * 100)) if checkpoint_target else 0
        progress_text.textContent = f"Learner Mode: {learner_scope_display_name(learner_scope_name)}"
        quiz_progress._dom_element.classList.add("learner-mode-progress")
        score_chip.textContent = learner_checkpoint_progress_chip(
            checkpoint_counts,
            checkpoint_target,
            checkpoint_display_mode,
        )
    else:
        progress_text.textContent = f"Question {position} of {total}"
        score_chip.textContent = f"{len(answers)} answered"
        quiz_progress._dom_element.classList.remove("learner-mode-progress")

    question_id_text.textContent = f"Question {question.question_id}"
    render_question_metadata(question)
    question_text.textContent = question.text
    question_type_card.textContent = ""
    question_type_card.classes.add("hidden")
    progress_bar.style["width"] = f"{progress_percent}%"

    if question.image:
        question_image.src = question.image
        question_image.setAttribute("data-image-src", question.image)
        question_image_wrap.classes.discard("hidden")
    else:
        question_image.src = ""
        question_image.removeAttribute("data-image-src")
        question_image_wrap.classes.add("hidden")

    render_options(question, selected_answer)

    if learner_session_active:
        review_interaction = latest_learner_review_interaction()
        quit_attempt_button.classes.add("hidden")
        learner_end_session_button.classes.discard("hidden")
        quit_attempt_button.textContent = "End Session"
        if learner_review_mode:
            previous_button.classes.discard("hidden")
            previous_button.disabled = True
            render_learner_feedback(
                question,
                selected_answer,
                response_is_correct(question, selected_answer),
            )
            learner_confidence_panel.classes.add("hidden")
            next_button.classes.discard("hidden")
            next_button.disabled = False
            quiz_footer.classes.add("quiz-footer-center")
            quiz_nav_actions.classes.discard("hidden")
            next_button.textContent = "Back to Current Question"
        elif learner_answer_locked and selected_answer is not None:
            previous_button.classes.add("hidden")
            previous_button.disabled = True
            render_learner_feedback(
                question,
                selected_answer,
                response_is_correct(question, selected_answer),
                (
                    (learner_pending_recommendation or {}).get("message", "")
                    if (learner_pending_recommendation or {}).get("end_session")
                    else ""
                ),
            )
            learner_confidence_panel.classes.add("hidden")
            next_button.classes.discard("hidden")
            next_button.disabled = False
            quiz_footer.classes.add("quiz-footer-center")
            quiz_nav_actions.classes.discard("hidden")
            next_button.textContent = (
                "Finish Session"
                if (learner_pending_recommendation or {}).get("end_session")
                or learner_pending_next_question_id is None
                else "Continue"
            )
        elif selected_answer is not None:
            previous_button.classes.add("hidden")
            previous_button.disabled = True
            learner_feedback.classes.add("hidden")
            learner_feedback.classes.discard("is-correct")
            learner_feedback.classes.discard("is-wrong")
            learner_feedback.textContent = ""
            render_learner_confidence_buttons()
            learner_confidence_panel.classes.discard("hidden")
            quiz_footer.classes.discard("quiz-footer-center")
            quiz_nav_actions.classes.add("hidden")
            next_button.classes.add("hidden")
            next_button.disabled = True
        else:
            if review_interaction is None:
                previous_button.classes.add("hidden")
                previous_button.disabled = True
                quiz_nav_actions.classes.add("hidden")
            else:
                previous_button.classes.discard("hidden")
                previous_button.disabled = False
                quiz_nav_actions.classes.discard("hidden")
            learner_feedback.classes.add("hidden")
            learner_feedback.classes.discard("is-correct")
            learner_feedback.classes.discard("is-wrong")
            learner_feedback.textContent = ""
            learner_confidence_buttons.innerHTML = ""
            learner_confidence_panel.classes.add("hidden")
            quiz_footer.classes.discard("quiz-footer-center")
            next_button.classes.add("hidden")
            next_button.disabled = True
        learner_question_started_at_ms = learner_question_started_at_ms or float(window.Date.now())
    else:
        learner_end_session_button.classes.add("hidden")
        quit_attempt_button.classes.discard("hidden")
        quiz_footer.classes.discard("quiz-footer-center")
        quiz_nav_actions.classes.discard("hidden")
        previous_button.classes.discard("hidden")
        next_button.classes.discard("hidden")
        previous_button.disabled = current_index == 0
        next_button.disabled = not response_complete(question, selected_answer)
        next_button.textContent = "Finish Quiz" if position == total else "Next"
        quit_attempt_button.textContent = "Quit Attempt"
        learner_feedback.classes.add("hidden")
        learner_feedback.classes.discard("is-correct")
        learner_feedback.classes.discard("is-wrong")
        learner_feedback.textContent = ""
        learner_confidence_panel.classes.add("hidden")

    update_quiz_image_size()
    if not learner_session_active:
        asyncio.create_task(prefetch_upcoming_questions())


def render_results_stats(percent: int, correct_count: int, wrong_count: int, total: int) -> None:
    stats_host.innerHTML = ""

    stats_items = [
        ("Score", f"{percent}%"),
        ("Correct", str(correct_count)),
        ("Wrong", str(wrong_count)),
        ("Questions", str(total)),
    ]
    if session_show_timer:
        stats_items.append(("Time Taken", format_elapsed_time(session_elapsed_seconds)))

    for label, value in stats_items:
        stats_host.append(
            web.div(
                web.div(value, classes=["value"]),
                web.div(label, classes=["label"]),
                classes=["statistic"],
            )
        )


def render_results_row(row: dict) -> str:
    metadata_columns = ""
    if results_show_metadata and RESULTS_METADATA_FIELDS and FEATURE_FLAGS.get("results_metadata_toggle", True):
        metadata_columns = "".join(
            f'<td class="{"question-cell" if field["key"] == "learning_outcome" else "answer-cell"}">'
            f'{escape(row["metadata"].get(field["key"], field.get("empty_value", "")))}'
            "</td>"
            for field in RESULTS_METADATA_FIELDS
        )

    return (
        f"""
        <tr class="{'results-row-correct' if row['is_correct'] else 'results-row-wrong'}">
            <td>{row['row_number']}</td>
            <td class="question-cell">{row['question_html']}</td>
            <td class="answer-cell">{escape(row['user_answer'])}</td>
            <td class="answer-cell">{escape(row['correct_answer'])}</td>
            <td>{row['points']}</td>
            {metadata_columns}
        </tr>
        """
    )


def render_results_table(rows: list[dict]) -> None:
    metadata_button_label = "Hide Metadata" if results_show_metadata else "Show Metadata"
    metadata_headers = ""
    table_class_name = "ui celled striped table"
    wrap_class_name = "results-table-wrap"
    metadata_toggle_enabled = FEATURE_FLAGS.get("results_metadata_toggle", True) and bool(RESULTS_METADATA_FIELDS)
    metadata_columns_visible = results_show_metadata and metadata_toggle_enabled
    if metadata_columns_visible:
        metadata_headers = "".join(
            f"<th>{escape(field.get('label', field['key']))}</th>"
            for field in RESULTS_METADATA_FIELDS
        )
        table_class_name += " results-table-compact"
        wrap_class_name += " results-table-wrap-compact"

    metadata_toggle_button = ""
    if metadata_toggle_enabled:
        metadata_toggle_button = (
            f'<button class="ui button qna-metadata-toggle" '
            f'data-toggle-qna-metadata="true" type="button">{metadata_button_label}</button>'
        )

    qna_tab.innerHTML = (
        '<div class="qna-toolbar">'
        + '<button class="ui button'
        + (" primary" if results_filter == "all" else "")
        + '" data-filter="all" type="button">All Questions</button>'
        + '<button class="ui button'
        + (" green" if results_filter == "correct" else "")
        + '" data-filter="correct" type="button">Only Correct</button>'
        + '<button class="ui button'
        + (" red" if results_filter == "wrong" else "")
        + '" data-filter="wrong" type="button">Only Wrong</button>'
        + '<span class="qna-toolbar-spacer"></span>'
        + metadata_toggle_button
        + "</div>"
        + f'<div class="{wrap_class_name}">'
        + f'<table class="{table_class_name}">'
        + "<thead><tr>"
        + "<th>No.</th>"
        + "<th>Questions</th>"
        + "<th>Your Answers</th>"
        + "<th>Correct Answers</th>"
        + "<th>Points</th>"
        + f"{metadata_headers}"
        + "</tr></thead>"
        + f"<tbody>{''.join(render_results_row(row) for row in rows)}</tbody>"
        + "</table>"
        + "</div>"
    )


async def render_results() -> None:
    global results_rows_data, results_filter

    show_status("Scoring session...")
    update_session_elapsed_time()
    stop_timer_updates()
    hide_session_timer()

    questions: list[Question] = []
    for question_id in session_question_ids:
        questions.append(await load_question(question_id))

    results_rows_data = []
    correct_count = 0

    for row_number, question in enumerate(questions, start=1):
        user_answer = answers.get(question.question_id)
        points = 1 if response_is_correct(question, user_answer) else 0
        correct_count += points

        image_html = ""
        if question.image:
            image_html = (
                f'<img class="results-image" src="{escape(question.image)}" '
                f'data-image-src="{escape(question.image)}" '
                'alt="Question reference image">'
            )

        results_rows_data.append(
            {
                "row_number": row_number,
                "is_correct": points == 1,
                "question_html": f"{escape(question.text)}{image_html}",
                "user_answer": answer_text(question, user_answer),
                "correct_answer": answer_text(question, question.answer),
                "points": points,
                "metadata": {
                    field["key"]: question_metadata_value(question, field["key"], field.get("empty_value", ""))
                    for field in RESULTS_METADATA_FIELDS
                },
            }
        )

    total = len(questions)
    wrong_count = total - correct_count
    percent = round((correct_count / total) * 100) if total else 0
    results_filter = "all"

    results_title.textContent = "Your score"
    results_subtitle.textContent = "Review the questions below, then retry the same set or draw a new one."
    score_value.textContent = f"{percent}%"
    score_detail.textContent = f"{correct_count} / {total} correct"

    render_results_stats(percent, correct_count, wrong_count, total)
    refresh_results_table()

    clear_draft_attempt()
    show_results_tab("stats")
    show_screen("results")
    hide_status()


def refresh_results_table() -> None:
    if results_filter == "correct":
        rows = [row for row in results_rows_data if row["is_correct"]]
    elif results_filter == "wrong":
        rows = [row for row in results_rows_data if not row["is_correct"]]
    else:
        rows = list(results_rows_data)

    render_results_table(rows)


def available_question_ids_for_session() -> list[int]:
    if not advanced_options_enabled:
        return list(quiz_index["question_ids"])

    selected = selected_knowledge_areas_from_ui()
    if not selected:
        return []

    available_ids: list[int] = []
    for area in selected:
        available_ids.extend(question_ids_by_area.get(area, []))
    return available_ids


async def start_quiz(question_ids: list[int] | None = None) -> None:
    global session_question_ids, answers, current_index
    global session_advanced_options_enabled, session_selected_knowledge_areas
    global session_show_timer, session_learner_mode, session_timer_started_at_ms

    if not quiz_index:
        return

    if learner_session_active:
        return

    if question_ids is None and advanced_options_enabled and not selected_knowledge_areas_from_ui():
        window.location.href = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        return

    show_status("Preparing quiz...")

    if question_ids is None:
        available_ids = available_question_ids_for_session()
        if not available_ids:
            show_status("No questions match the selected Knowledge Areas.")
            return

        selected_areas = selected_knowledge_areas_from_ui() if advanced_options_enabled else []
        requested_count = 20
        try:
            requested_count = int(count_input.value or "20")
        except ValueError:
            requested_count = 20

        max_available = len(available_ids)
        count = question_count_value(max_available)
        if requested_count > max_available:
            show_toast(
                "The number of questions requested was above the maximum possible "
                "for the selected Knowledge Area(s), so it has been set to the maximum available."
            )
        question_ids = random.sample(list(available_ids), count)
        session_advanced_options_enabled = advanced_options_enabled
        session_selected_knowledge_areas = list(selected_areas)
        session_show_timer = advanced_options_enabled and bool(show_timer_toggle._dom_element.checked)
        session_learner_mode = advanced_options_enabled and bool(learner_mode_toggle._dom_element.checked)
    else:
        session_advanced_options_enabled = advanced_options_enabled
        session_selected_knowledge_areas = list(selected_knowledge_areas_from_ui()) if advanced_options_enabled else []
        session_show_timer = advanced_options_enabled and bool(show_timer_toggle._dom_element.checked)
        session_learner_mode = advanced_options_enabled and bool(learner_mode_toggle._dom_element.checked)

    session_question_ids = question_ids
    answers = {}
    current_index = 0
    session_timer_started_at_ms = float(window.Date.now()) if session_show_timer else None
    start_timer_updates()
    clear_learner_session_draft()
    save_draft_attempt()

    await render_current_question()
    show_screen("quiz")
    hide_status()


async def go_previous() -> None:
    global current_index
    global learner_selected_answer, learner_answer_locked, learner_selected_confidence
    global learner_review_mode, learner_review_return_state

    if learner_session_active:
        if learner_answer_locked or learner_review_mode:
            return
        review_interaction = latest_learner_review_interaction()
        if review_interaction is None:
            return
        learner_review_mode = True
        learner_review_return_state = {
            "question_id": session_question_ids[0] if session_question_ids else None,
            "selected_answer": learner_selected_answer,
            "selected_confidence": learner_selected_confidence,
            "pending_next_question_id": learner_pending_next_question_id,
            "pending_recommendation": learner_pending_recommendation,
            "question_started_at_ms": learner_question_started_at_ms,
        }
        session_question_ids[:] = [int(review_interaction["question_id"])]
        current_index = 0
        learner_selected_answer = normalized_saved_response(review_interaction.get("selected_answer"))
        learner_selected_confidence = (
            int(review_interaction.get("confidence"))
            if review_interaction.get("confidence") is not None
            else None
        )
        learner_answer_locked = True
        save_learner_session_draft()
        await render_current_question()
        return

    if current_index == 0:
        return

    current_index -= 1
    save_draft_attempt()
    await render_current_question()


async def go_next() -> None:
    global current_index
    global learner_selected_answer, learner_answer_locked, learner_question_started_at_ms
    global learner_pending_next_question_id, learner_pending_recommendation
    global learner_review_mode, learner_review_return_state
    global learner_selected_confidence

    if learner_session_active:
        if learner_review_mode:
            return_state = learner_review_return_state or {}
            return_question_id = return_state.get("question_id")
            if return_question_id is not None:
                session_question_ids[:] = [int(return_question_id)]
            current_index = 0
            learner_selected_answer = normalized_saved_response(return_state.get("selected_answer"))
            learner_selected_confidence = return_state.get("selected_confidence")
            learner_pending_next_question_id = return_state.get("pending_next_question_id")
            learner_pending_recommendation = return_state.get("pending_recommendation")
            learner_question_started_at_ms = return_state.get("question_started_at_ms")
            learner_answer_locked = False
            learner_review_mode = False
            learner_review_return_state = None
            save_learner_session_draft()
            await render_current_question()
            return
        if not learner_answer_locked:
            return
        recommendation = learner_pending_recommendation or {}
        if recommendation.get("end_session") or learner_pending_next_question_id is None:
            await end_learner_session(recommendation)
            return

        if recommendation.get("message"):
            show_toast(recommendation["message"])

        session_question_ids[:] = [learner_pending_next_question_id]
        current_index = 0
        learner_selected_answer = None
        learner_answer_locked = False
        learner_pending_next_question_id = None
        learner_pending_recommendation = None
        learner_selected_confidence = None
        learner_question_started_at_ms = float(window.Date.now())
        save_learner_session_draft()
        await render_current_question()
        return

    current_question_id = session_question_ids[current_index]
    if current_question_id not in answers:
        return

    if current_index == len(session_question_ids) - 1:
        await render_results()
        return

    current_index += 1
    save_draft_attempt()
    await render_current_question()


async def restore_draft_attempt() -> bool:
    global session_question_ids, answers, current_index
    global session_advanced_options_enabled, session_selected_knowledge_areas
    global advanced_options_enabled, selected_knowledge_areas
    global show_timer_enabled, learner_mode_enabled
    global session_show_timer, session_learner_mode, session_timer_started_at_ms

    draft = load_draft_attempt()
    if not draft:
        return False

    try:
        restored_question_ids = [int(question_id) for question_id in draft["question_ids"]]
        restored_answers = {
            int(question_id): normalized_saved_response(answer_key)
            for question_id, answer_key in draft["answers"].items()
            if normalized_saved_response(answer_key) is not None
        }
        restored_index = int(draft["current_index"])
        restored_advanced_options_enabled = bool(
            draft.get("session_advanced_options_enabled", False)
        )
        restored_selected_areas = [
            str(area)
            for area in draft.get("session_selected_knowledge_areas", [])
            if str(area) in KNOWLEDGE_AREAS
        ]
        restored_show_timer = bool(draft.get("session_show_timer", False))
        restored_learner_mode = bool(draft.get("session_learner_mode", False))
        restored_timer_started_at_ms = draft.get("session_timer_started_at_ms")
        if restored_timer_started_at_ms is not None:
            restored_timer_started_at_ms = float(restored_timer_started_at_ms)
    except Exception:
        clear_draft_attempt()
        return False

    if not restored_question_ids:
        clear_draft_attempt()
        return False

    if restored_learner_mode:
        clear_draft_attempt()
        return False

    restored_index = max(0, min(restored_index, len(restored_question_ids) - 1))

    session_question_ids = restored_question_ids
    answers = restored_answers
    current_index = restored_index
    session_advanced_options_enabled = restored_advanced_options_enabled
    session_selected_knowledge_areas = restored_selected_areas
    session_show_timer = restored_show_timer
    session_learner_mode = restored_learner_mode
    session_timer_started_at_ms = restored_timer_started_at_ms
    advanced_options_enabled = restored_advanced_options_enabled
    selected_knowledge_areas = list(restored_selected_areas)
    show_timer_enabled = restored_show_timer
    learner_mode_enabled = restored_learner_mode
    render_knowledge_area_checkboxes()
    sync_advanced_options_ui()
    start_timer_updates()

    show_status("Restoring saved attempt...")
    await render_current_question()
    show_screen("quiz")
    hide_status()
    save_draft_attempt()
    return True


def render_knowledge_area_checkboxes() -> None:
    knowledge_area_checkboxes.innerHTML = ""

    for area in KNOWLEDGE_AREAS:
        input_id = f"knowledge-area-{area_to_dom_id(area)}"
        label = document.createElement("label")
        label.className = "advanced-checkbox-item"

        checkbox = document.createElement("input")
        checkbox.type = "checkbox"
        checkbox.id = input_id
        checkbox.value = area
        checkbox.checked = area in selected_knowledge_areas
        checkbox_change_proxy = create_proxy(on_knowledge_area_checkbox_change)
        proxies.append(checkbox_change_proxy)
        checkbox.addEventListener("change", checkbox_change_proxy)

        text = document.createElement("span")
        text.textContent = area

        label.appendChild(checkbox)
        label.appendChild(text)
        knowledge_area_checkboxes._dom_element.appendChild(label)

    update_available_question_display()


def sync_advanced_options_ui() -> None:
    global advanced_options_enabled

    advanced_options_available = FEATURE_FLAGS.get("advanced_options", True)

    if advanced_options_bar is not None:
        advanced_options_bar.style.display = "" if advanced_options_available else "none"

    if not advanced_options_available:
        advanced_options_enabled = False

    advanced_options_toggle._dom_element.checked = advanced_options_enabled
    show_timer_toggle._dom_element.checked = show_timer_enabled
    learner_mode_toggle._dom_element.checked = learner_mode_enabled
    show_timer_toggle._dom_element.parentElement.style.display = (
        "" if FEATURE_FLAGS.get("timer_option", True) else "none"
    )
    learner_mode_toggle._dom_element.parentElement.style.display = (
        "" if FEATURE_FLAGS.get("learner_mode_option", True) else "none"
    )

    if advanced_options_enabled and advanced_options_available:
        advanced_options.classes.discard("hidden")
    else:
        advanced_options.classes.add("hidden")
    update_available_question_display()


def on_start_click(event) -> None:
    if learner_enabled_for_start():
        show_screen("learner-confirm")
        return
    asyncio.create_task(start_quiz())


def on_previous_click(event) -> None:
    asyncio.create_task(go_previous())


def on_next_click(event) -> None:
    asyncio.create_task(go_next())


async def copy_question_to_clipboard() -> None:
    await copy_text_to_clipboard(
        current_question_copy_text(),
        "Question copied to clipboard.",
        "There is no question to copy right now.",
    )


def on_copy_question_click(event) -> None:
    event.preventDefault()
    asyncio.create_task(copy_question_to_clipboard())


def on_quiz_help_click(event) -> None:
    event.preventDefault()
    if learner_session_active:
        show_quiz_help("Learner Mode Help", learner_mode_help_html())
    else:
        show_quiz_help("Quiz Mode Help", normal_mode_help_html())


def on_quiz_help_dismiss_click(event) -> None:
    hide_quiz_help()


def on_quit_attempt_click(event) -> None:
    if learner_session_active:
        configure_quit_confirm_screen("learner")
        show_screen("quit-confirm")
        return
    configure_quit_confirm_screen("quiz")
    show_screen("quit-confirm")


def on_retry_same_click(event) -> None:
    if session_question_ids:
        asyncio.create_task(start_quiz(question_ids=list(session_question_ids)))


def on_retry_new_click(event) -> None:
    asyncio.create_task(start_quiz())


def on_back_home_click(event) -> None:
    hide_learner_debug_panel()
    close_learner_debug_popup()
    show_screen("home")


def on_confirm_quit_click(event) -> None:
    if quit_confirm_mode == "learner":
        asyncio.create_task(leave_learner_session_to_hub())
        return
    hide_learner_debug_panel()
    close_learner_debug_popup()
    clear_active_attempt_state()
    hide_status()
    show_screen("home")


def on_cancel_quit_click(event) -> None:
    if quit_confirm_mode == "learner":
        show_screen("quiz")
        return
    show_screen("quiz")


def on_learner_confirm_yes_click(event) -> None:
    asyncio.create_task(enter_learner_passport_screen())


def on_learner_confirm_no_click(event) -> None:
    show_screen("home")


def on_learner_start_fresh_click(event) -> None:
    if learner_storage_module is None:
        return
    enter_learner_generator_screen()


def on_learner_generate_passport_click(event) -> None:
    if learner_storage_module is None:
        return
    create_fresh_learner_progress(
        learner_username_input._dom_element.value,
        learner_generator_avatar_id,
        learner_generator_avatar_bg_id,
    )


def on_learner_generator_back_click(event) -> None:
    asyncio.create_task(enter_learner_passport_screen())


def on_learner_avatar_options_click(event) -> None:
    global learner_generator_avatar_id

    target = getattr(event, "target", None)
    if target is None:
        return
    option = target.closest("[data-learner-avatar-id]")
    if option is None:
        return
    avatar_id = option.getAttribute("data-learner-avatar-id")
    if not avatar_id:
        return
    learner_generator_avatar_id = passport_avatar(avatar_id)["id"]
    render_learner_generator_avatar_picker()


def on_learner_avatar_bg_options_click(event) -> None:
    global learner_generator_avatar_bg_id

    target = getattr(event, "target", None)
    if target is None:
        return
    option = target.closest("[data-learner-avatar-bg-id]")
    if option is None:
        return
    background_id = option.getAttribute("data-learner-avatar-bg-id")
    if not background_id:
        return
    learner_generator_avatar_bg_id = passport_avatar_background(background_id)["id"]
    render_learner_generator_avatar_picker()


def on_learner_download_progress_click(event) -> None:
    if learner_storage_module is None:
        return
    download_json_payload(exported_progress_payload(), exported_progress_filename())


def on_learner_hub_back_home_click(event) -> None:
    show_screen("home")


def on_learner_summary_return_hub_click(event) -> None:
    hide_learner_debug_panel()
    close_learner_debug_popup()
    reset_learner_debug_unlock()
    reset_learner_debug_capture_state()
    asyncio.create_task(enter_learner_hub())


def on_learner_summary_continue_click(event) -> None:
    if not learner_scope_name:
        hide_learner_debug_panel()
        close_learner_debug_popup()
        reset_learner_debug_unlock()
        reset_learner_debug_capture_state()
        asyncio.create_task(enter_learner_hub())
        return
    asyncio.create_task(start_learner_session(learner_scope_name))


def on_learner_summary_home_click(event) -> None:
    hide_learner_debug_panel()
    close_learner_debug_popup()
    reset_learner_debug_unlock()
    reset_learner_debug_capture_state()
    show_screen("home")


def on_learner_progress_file_change(event) -> None:
    asyncio.create_task(import_learner_progress_from_file())


def on_learner_use_current_passport_click(event) -> None:
    asyncio.create_task(enter_learner_hub())


def on_stats_tab_click(event) -> None:
    show_results_tab("stats")


def on_qna_tab_click(event) -> None:
    show_results_tab("qna")


def on_advanced_options_toggle(event) -> None:
    global advanced_options_enabled, selected_knowledge_areas

    advanced_options_enabled = bool(advanced_options_toggle._dom_element.checked)
    if not advanced_options_enabled:
        selected_knowledge_areas = []
        render_knowledge_area_checkboxes()
    else:
        if not selected_knowledge_areas:
            selected_knowledge_areas = list(KNOWLEDGE_AREAS)
            render_knowledge_area_checkboxes()
        else:
            selected_knowledge_areas = selected_knowledge_areas_from_ui()
    sync_advanced_options_ui()
    save_advanced_options_preferences()


def on_question_metadata_toggle(event) -> None:
    if not session_advanced_options_enabled:
        return

    question_metadata_toggle._dom_element.blur()
    set_question_metadata_collapsed(not question_metadata_collapsed)
    asyncio.create_task(render_current_question())


def on_keydown(event) -> None:
    global learner_selected_answer, learner_answer_locked
    global learner_selected_confidence
    global learner_debug_unlock_buffer, multi_select_focus_key

    if learner_guidance_visible:
        return
    if "hidden" in quiz_help_modal.classes:
        pass
    else:
        key = (getattr(event, "key", "") or "").lower()
        if key in {"escape", "enter", " "}:
            event.preventDefault()
            hide_quiz_help()
        return

    target = getattr(event, "target", None)
    tag_name = ""
    if target is not None:
        tag_name = (getattr(target, "tagName", "") or "").lower()

    if tag_name in {"input", "textarea", "select"}:
        return

    if not quiz_is_visible():
        return

    key = (getattr(event, "key", "") or "").lower()
    question_id = session_question_ids[current_index] if session_question_ids else None
    question = question_cache.get(question_id) if question_id is not None else None

    if learner_session_active and question is not None and key and len(key) == 1 and key.isalpha():
        unlock_code = "qwertyuiop"
        learner_debug_unlock_buffer = (learner_debug_unlock_buffer + key)[-len(unlock_code):]
        if learner_debug_unlock_buffer == unlock_code:
            unlock_learner_debug_controls()
            start_learner_debug_updates()
            return
    elif key not in {"shift", "control", "alt", "meta"}:
        learner_debug_unlock_buffer = ""

    if learner_session_active and question is not None and learner_debug_unlocked and key in {"7", "8", "9", "0"}:
        if learner_answer_locked:
            return
        event.preventDefault()
        dev_map = {
            "7": (True, 3),
            "8": (True, 0),
            "9": (False, 0),
            "0": (False, 3),
        }
        is_correct_target, confidence_value = dev_map[key]
        answer_key = learner_dev_answer_key(question, is_correct_target)
        if answer_key is None:
            return
        learner_selected_answer = answer_key
        learner_selected_confidence = confidence_value
        save_learner_session_draft()
        asyncio.create_task(handle_learner_confidence(confidence_value))
        return

    if key in {"1", "2", "3", "4"} and question is not None:
        event.preventDefault()
        option_index = int(key) - 1
        if learner_session_active and learner_answer_locked:
            confidence_value = 4 - int(key)
            if 0 <= confidence_value <= 3:
                asyncio.create_task(handle_learner_confidence(confidence_value))
            return
        if option_index < len(question.options):
            if learner_session_active:
                learner_option = question.options[option_index]["key"]
                learner_selected_answer = toggled_response(
                    question,
                    learner_selected_answer,
                    learner_option,
                )
                multi_select_focus_key = learner_option if question_is_multi_select(question) else None
                learner_selected_confidence = None
                save_learner_session_draft()
                asyncio.create_task(render_current_question())
                return
            updated_response = toggled_response(
                question,
                answers.get(question_id),
                question.options[option_index]["key"],
            )
            multi_select_focus_key = (
                question.options[option_index]["key"] if question_is_multi_select(question) else None
            )
            if updated_response is None:
                answers.pop(question_id, None)
            else:
                answers[question_id] = updated_response
            save_draft_attempt()
            asyncio.create_task(render_current_question())
        return

    if key == "arrowdown":
        event.preventDefault()
        move_option_selection(1)
        return

    if key == "arrowup":
        event.preventDefault()
        move_option_selection(-1)
        return

    if (
        key in {"enter", " ", "space"}
        and question is not None
        and question_is_multi_select(question)
        and multi_select_focus_active(question)
        and not (learner_session_active and learner_answer_locked)
    ):
        event.preventDefault()
        toggle_focused_multi_select_option(question)
        return

    if key == "arrowleft":
        if learner_session_active:
            if learner_answer_locked:
                return
            if latest_learner_review_interaction() is not None and not response_complete(question, learner_selected_answer):
                event.preventDefault()
                asyncio.create_task(go_previous())
                return
            if response_complete(question, learner_selected_answer):
                event.preventDefault()
                multi_select_focus_key = None
                if learner_selected_confidence is None:
                    learner_selected_confidence = 0
                else:
                    learner_selected_confidence = (learner_selected_confidence + 1) % 4
                save_learner_session_draft()
                asyncio.create_task(render_current_question())
            return
        event.preventDefault()
        asyncio.create_task(go_previous())
        return

    if key in {"arrowright", " ", "space", "enter"}:
        if learner_session_active:
            if learner_answer_locked:
                event.preventDefault()
                asyncio.create_task(go_next())
                return
            if response_complete(question, learner_selected_answer):
                if key == "arrowright":
                    event.preventDefault()
                    multi_select_focus_key = None
                    if learner_selected_confidence is None:
                        learner_selected_confidence = 3
                    else:
                        learner_selected_confidence = (learner_selected_confidence - 1) % 4
                    save_learner_session_draft()
                    asyncio.create_task(render_current_question())
                    return
                if key == "enter" and learner_selected_confidence is None:
                    event.preventDefault()
                    if target is not None and hasattr(target, "blur"):
                        try:
                            target.blur()
                        except Exception:
                            pass
                    learner_selected_confidence = 1
                    save_learner_session_draft()
                    asyncio.create_task(render_current_question())
                    return
                if key in {" ", "space", "enter"} and learner_selected_confidence is not None:
                    event.preventDefault()
                    asyncio.create_task(handle_learner_confidence(learner_selected_confidence))
                    return
            return
        event.preventDefault()
        asyncio.create_task(go_next())
        return


def on_document_click(event) -> None:
    global results_filter, results_show_metadata
    global selected_knowledge_areas, show_timer_enabled, learner_mode_enabled

    note_quiz_pointer_activity()

    if learner_guidance_visible:
        target = getattr(event, "target", None)
        if target is None or getattr(target, "id", "") != "learner-guidance-dismiss-btn":
            return

    if "hidden" not in quiz_help_modal.classes:
        target = getattr(event, "target", None)
        if target is None or getattr(target, "id", "") != "quiz-help-dismiss-btn":
            return

    target = getattr(event, "target", None)
    if target is None:
        return

    image_src = target.getAttribute("data-image-src") if hasattr(target, "getAttribute") else None
    if image_src:
        show_lightbox(image_src)
        return

    filter_name = target.getAttribute("data-filter") if hasattr(target, "getAttribute") else None
    if filter_name in {"all", "correct", "wrong"}:
        results_filter = filter_name
        refresh_results_table()
        return

    learner_scope = (
        target.getAttribute("data-learner-scope")
        if hasattr(target, "getAttribute")
        else None
    )
    if learner_scope:
        asyncio.create_task(start_learner_session(learner_scope))
        return

    learner_confidence = (
        target.getAttribute("data-learner-confidence")
        if hasattr(target, "getAttribute")
        else None
    )
    if learner_confidence is not None:
        try:
            confidence_value = int(learner_confidence)
        except Exception:
            return
        asyncio.create_task(handle_learner_confidence(confidence_value))
        return

    toggle_metadata = (
        target.getAttribute("data-toggle-qna-metadata")
        if hasattr(target, "getAttribute")
        else None
    )
    if toggle_metadata == "true":
        set_results_show_metadata(not results_show_metadata)
        refresh_results_table()
        return

    if target.id in {"lightbox-close-btn", "image-lightbox"}:
        hide_lightbox()
        return

    class_list = getattr(target, "classList", None)
    if class_list and class_list.contains("image-lightbox-backdrop"):
        hide_lightbox()
        return

    if getattr(target, "type", "") == "checkbox" and getattr(target, "value", "") in KNOWLEDGE_AREAS:
        selected_knowledge_areas = selected_knowledge_areas_from_ui()
        update_available_question_display()
        save_advanced_options_preferences()
        return

    if target.id == "show-timer-toggle":
        show_timer_enabled = bool(show_timer_toggle._dom_element.checked)
        save_advanced_options_preferences()
        return

    if target.id == "learner-mode-toggle":
        learner_mode_enabled = bool(learner_mode_toggle._dom_element.checked)
        save_advanced_options_preferences()


def on_window_resize(event) -> None:
    update_quiz_image_size()


def on_mousemove(event) -> None:
    note_quiz_pointer_activity()


async def boot() -> None:
    global question_metadata_collapsed
    global advanced_options_enabled, selected_knowledge_areas
    global show_timer_enabled, learner_mode_enabled

    sys.excepthook = handle_uncaught_exception
    asyncio.get_running_loop().set_exception_handler(handle_asyncio_exception)

    show_status("Loading question index...")
    show_screen("home")
    show_results_tab("stats")

    try:
        await load_app_config()
        await load_quiz_config()
        await load_question_bank_index()
    except Exception as exc:
        show_status(f"Could not load quiz data: {exc}")
        hide_page_loader()
        return

    total = int(quiz_index["question_count"])
    total_question_count.textContent = str(total)
    count_input.max = str(total)

    question_metadata_collapsed = (
        window.sessionStorage.getItem(QUESTION_METADATA_COLLAPSED_KEY) == "true"
    )
    stored_results_metadata = window.sessionStorage.getItem(QNA_METADATA_VISIBLE_KEY)
    if stored_results_metadata is None:
        set_results_show_metadata(
            bool(APP_CONFIG.get("metadata", {}).get("results_default_visible", False))
        )
    else:
        set_results_show_metadata(stored_results_metadata == "true")
    (
        advanced_options_enabled,
        selected_knowledge_areas,
        show_timer_enabled,
        learner_mode_enabled,
    ) = load_advanced_options_preferences()

    render_knowledge_area_checkboxes()
    sync_advanced_options_ui()

    if await maybe_restore_learner_session():
        hide_page_loader()
        return

    if await restore_draft_attempt():
        hide_page_loader()
        return

    hide_status()
    hide_page_loader()


start_button.on_click.add_listener(on_start_click)
previous_button.on_click.add_listener(on_previous_click)
next_button.on_click.add_listener(on_next_click)
copy_question_link.on_click.add_listener(on_copy_question_click)
quiz_help_link.on_click.add_listener(on_quiz_help_click)
quit_attempt_button.on_click.add_listener(on_quit_attempt_click)
learner_end_session_button.on_click.add_listener(on_quit_attempt_click)
retry_same_button.on_click.add_listener(on_retry_same_click)
retry_new_button.on_click.add_listener(on_retry_new_click)
back_home_button.on_click.add_listener(on_back_home_click)
confirm_quit_button.on_click.add_listener(on_confirm_quit_click)
cancel_quit_button.on_click.add_listener(on_cancel_quit_click)
learner_confirm_yes_button.on_click.add_listener(on_learner_confirm_yes_click)
learner_confirm_no_button.on_click.add_listener(on_learner_confirm_no_click)
learner_use_current_passport_button.on_click.add_listener(on_learner_use_current_passport_click)
learner_start_fresh_button.on_click.add_listener(on_learner_start_fresh_click)
learner_avatar_options.on_click.add_listener(on_learner_avatar_options_click)
learner_avatar_bg_options.on_click.add_listener(on_learner_avatar_bg_options_click)
learner_generate_passport_button.on_click.add_listener(on_learner_generate_passport_click)
learner_generator_back_button.on_click.add_listener(on_learner_generator_back_click)
learner_download_progress_button.on_click.add_listener(on_learner_download_progress_click)
learner_hub_back_home_button.on_click.add_listener(on_learner_hub_back_home_click)
learner_summary_download_button.on_click.add_listener(on_learner_download_progress_click)
learner_summary_continue_button.on_click.add_listener(on_learner_summary_continue_click)
learner_summary_return_hub_button.on_click.add_listener(on_learner_summary_return_hub_click)
learner_summary_home_button.on_click.add_listener(on_learner_summary_home_click)
learner_guidance_dismiss_button.on_click.add_listener(on_learner_guidance_dismiss_click)
quiz_help_dismiss_button.on_click.add_listener(on_quiz_help_dismiss_click)
learner_debug_download_button.on_click.add_listener(on_learner_debug_download_click)
learner_debug_copy_button.on_click.add_listener(on_learner_debug_copy_click)
learner_debug_popout_button.on_click.add_listener(on_learner_debug_popout_click)
learner_debug_hide_button.on_click.add_listener(on_learner_debug_hide_click)
learner_debug_reopen_button.on_click.add_listener(on_learner_debug_reopen_click)
stats_tab_button.on_click.add_listener(on_stats_tab_click)
qna_tab_button.on_click.add_listener(on_qna_tab_click)
advanced_options_toggle.on_click.add_listener(on_advanced_options_toggle)
question_metadata_toggle.on_click.add_listener(on_question_metadata_toggle)
lightbox_close_button.on_click.add_listener(lambda event: hide_lightbox())

keydown_proxy = create_proxy(on_keydown)
proxies.append(keydown_proxy)
document.addEventListener("keydown", keydown_proxy)

click_proxy = create_proxy(on_document_click)
proxies.append(click_proxy)
document.addEventListener("click", click_proxy)

mousemove_proxy = create_proxy(on_mousemove)
proxies.append(mousemove_proxy)
document.addEventListener("mousemove", mousemove_proxy)

resize_proxy = create_proxy(on_window_resize)
proxies.append(resize_proxy)
window.addEventListener("resize", resize_proxy)

learner_progress_change_proxy = create_proxy(on_learner_progress_file_change)
proxies.append(learner_progress_change_proxy)
learner_progress_file._dom_element.addEventListener("change", learner_progress_change_proxy)

show_timer_change_proxy = create_proxy(on_show_timer_toggle_change)
proxies.append(show_timer_change_proxy)
show_timer_toggle._dom_element.addEventListener("change", show_timer_change_proxy)

learner_mode_change_proxy = create_proxy(on_learner_mode_toggle_change)
proxies.append(learner_mode_change_proxy)
learner_mode_toggle._dom_element.addEventListener("change", learner_mode_change_proxy)


asyncio.create_task(boot())
