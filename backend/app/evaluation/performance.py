import statistics
import threading
import time
from contextlib import contextmanager
from contextvars import ContextVar
from functools import wraps
from math import isfinite


PERFORMANCE_STAGES = (
    "pdf_upload_time",
    "pdf_parsing_time",
    "chunking_time",
    "embedding_generation_time",
    "retrieval_latency",
    "llm_generation_latency",
    "end_to_end_response_time",
)

_samples = {stage: [] for stage in PERFORMANCE_STAGES}
_samples_lock = threading.Lock()
_query_count = 0
_retrieval_success_count = 0
_similarity_total = 0.0
_similarity_sample_count = 0
_active_capture = ContextVar("evaluation_performance_capture", default=None)


def record_timing(stage, duration_seconds):
    """Record a duration globally and in the current evaluation capture."""
    if stage not in _samples:
        raise ValueError(f"Unknown performance stage: {stage}")

    duration = max(0.0, float(duration_seconds))
    with _samples_lock:
        _samples[stage].append(duration)

    active_capture = _active_capture.get()
    if active_capture is not None:
        active_capture.setdefault(stage, []).append(duration)


@contextmanager
def timed_stage(stage):
    """Measure a block while preserving any exception it raises."""
    started_at = time.perf_counter()
    try:
        yield
    finally:
        record_timing(stage, time.perf_counter() - started_at)


@contextmanager
def capture_timings():
    """Collect timings attributable to one benchmark run."""
    captured = {}
    token = _active_capture.set(captured)
    try:
        yield captured
    finally:
        _active_capture.reset(token)


def timed_function(stage):
    """Decorate a synchronous operation with a performance measurement."""
    def decorate(function):
        @wraps(function)
        def wrapped(*args, **kwargs):
            with timed_stage(stage):
                return function(*args, **kwargs)

        return wrapped

    return decorate


def timing_snapshot():
    """Return a thread-safe copy of all process-recorded timings."""
    with _samples_lock:
        return {stage: list(values) for stage, values in _samples.items()}


def record_query(retrieval_succeeded, similarity_scores=()):
    """Record aggregate query metrics without retaining query content."""
    global _query_count, _retrieval_success_count
    global _similarity_total, _similarity_sample_count

    scores = []
    for score in similarity_scores:
        try:
            value = float(score)
        except (TypeError, ValueError):
            continue
        if isfinite(value):
            scores.append(value)

    with _samples_lock:
        _query_count += 1
        if retrieval_succeeded:
            _retrieval_success_count += 1
        _similarity_total += sum(scores)
        _similarity_sample_count += len(scores)


def query_snapshot():
    """Return aggregate query counts and similarity without query content."""
    with _samples_lock:
        return {
            "total_queries_asked": _query_count,
            "retrieval_success_count": _retrieval_success_count,
            "average_similarity_score": (
                round(_similarity_total / _similarity_sample_count, 6)
                if _similarity_sample_count
                else None
            ),
        }


def summarize_samples(samples):
    """Calculate descriptive statistics for each stage's duration samples."""
    summaries = {}
    for stage in PERFORMANCE_STAGES:
        values = list(samples.get(stage, []))
        count = len(values)
        summaries[stage] = {
            "samples": count,
            "average": statistics.mean(values) if values else None,
            "median": statistics.median(values) if values else None,
            "minimum": min(values) if values else None,
            "maximum": max(values) if values else None,
            "standard_deviation": (
                statistics.stdev(values) if count > 1 else None
            ),
        }
    return summaries
