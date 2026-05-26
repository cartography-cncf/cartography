#!/usr/bin/env python3
"""
Download and analyse cartography sync timing logs from CloudWatch.

Covers all providers: azure, aws, gcp, github, gitlab, bitbucket, azuredevops, oci

All providers now emit structured JSON timing events — no regex fallback needed.

Event names
───────────
  Service-level : {provider}_service_timing
  Scope summary : {provider}_{scope}_timing_summary
                  e.g. aws_account_timing_summary, github_org_timing_summary

Usage:
    # Default log group (K8s application logs):
    #   /aws/containerinsights/cdx-graph-cluster/application

    # All providers, last 24h, print to stdout
    python download_azure_timing_logs.py \\
        --log-group /aws/containerinsights/cdx-graph-cluster/application --hours 24

    # Specific window, save to file
    python download_azure_timing_logs.py \\
        --log-group /aws/containerinsights/cdx-graph-cluster/application \\
        --start "2026-05-25 00:00" --end "2026-05-26 00:00" --output timing.json

    # Analyze a previously saved file (no AWS API calls)
    python download_azure_timing_logs.py --from-file timing.json

    # Single provider
    python download_azure_timing_logs.py \\
        --log-group /ecs/cartography --provider aws --hours 24

    # Azure only: services with 429 throttling
    python download_azure_timing_logs.py \\
        --log-group /ecs/cartography --provider azure --hours 24 --throttled-only

    # All providers: errors only
    python download_azure_timing_logs.py \\
        --log-group /ecs/cartography --hours 24 --failed-only

    # Top 10 slowest services per provider
    python download_azure_timing_logs.py --from-file timing.json --top 10
"""

import argparse
import ast
import json
import sys
import time
from collections import defaultdict
from datetime import datetime
from datetime import timedelta
from datetime import timezone
from typing import Any
from typing import Dict
from typing import List
from typing import Optional
from typing import Tuple

import boto3


# ---------------------------------------------------------------------------
# Known structured event names → provider
# ---------------------------------------------------------------------------

_SERVICE_TIMING_EVENTS: Dict[str, str] = {
    f"{p}_service_timing": p
    for p in ["azure", "aws", "gcp", "github", "gitlab", "bitbucket", "azuredevops", "oci"]
}

_SUMMARY_EVENTS: Dict[str, str] = {
    "azure_subscription_timing_summary": "azure",
    "aws_account_timing_summary":        "aws",
    "gcp_project_timing_summary":        "gcp",
    "github_org_timing_summary":         "github",
    "gitlab_group_timing_summary":       "gitlab",
    "bitbucket_workspace_timing_summary": "bitbucket",
    "azuredevops_org_timing_summary":    "azuredevops",
    "oci_compartment_timing_summary":    "oci",
    "oci_tenancy_timing_summary":        "oci",
}

_ALL_KNOWN_EVENTS: Dict[str, str] = {**_SERVICE_TIMING_EVENTS, **_SUMMARY_EVENTS}

# Primary scope key per provider (used to extract scope_id from events)
_PROVIDER_SCOPE_KEY: Dict[str, str] = {
    "azure":       "subscription_id",
    "aws":         "account_id",
    "gcp":         "project_id",
    "github":      "org",
    "gitlab":      "group",
    "bitbucket":   "workspace",
    "azuredevops": "org",
    "oci":         "tenancy",
}

ALL_PROVIDERS = ["azure", "aws", "gcp", "github", "gitlab", "bitbucket", "azuredevops", "oci"]


# ---------------------------------------------------------------------------
# CloudWatch filter patterns
# "?term" = substring OR match; all events now embed their event name as JSON
# ---------------------------------------------------------------------------

_PROVIDER_FILTER: Dict[str, str] = {
    "azure":       '?"azure_service_timing" ?"azure_subscription_timing_summary"',
    "aws":         '?"aws_service_timing" ?"aws_account_timing_summary"',
    "gcp":         '?"gcp_service_timing" ?"gcp_project_timing_summary"',
    "github":      '?"github_service_timing" ?"github_org_timing_summary"',
    "gitlab":      '?"gitlab_service_timing" ?"gitlab_group_timing_summary"',
    "bitbucket":   '?"bitbucket_service_timing" ?"bitbucket_workspace_timing_summary"',
    "azuredevops": '?"azuredevops_service_timing" ?"azuredevops_org_timing_summary"',
    "oci":         '?"oci_service_timing" ?"oci_compartment_timing_summary" ?"oci_tenancy_timing_summary"',
    # All providers: match any JSON line containing "_service_timing" or "_timing_summary"
    "all": '?"_service_timing" ?"_timing_summary"',
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def err(fmt: str, *args: Any, **kwargs: Any) -> None:
    print(fmt.format(*args, **kwargs) if (args or kwargs) else fmt, file=sys.stderr)


def fmt_sec(v: float) -> str:
    return f"{v:>8.1f}"


# ---------------------------------------------------------------------------
# Argument parsing
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Download and analyse cartography timing logs from CloudWatch",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    p.add_argument("--log-group", help="CloudWatch log group name (required unless --from-file)")
    p.add_argument("--log-stream-prefix", default=None, help="Filter by log stream prefix")
    p.add_argument("--hours", type=float, default=24, help="Look back N hours from now (default: 24)")
    p.add_argument("--start", default=None, help="Start time UTC (YYYY-MM-DD HH:MM)")
    p.add_argument("--end",   default=None, help="End time UTC (YYYY-MM-DD HH:MM), defaults to now")
    p.add_argument("--output",    default=None, help="Save full JSON to this file (default: stdout)")
    p.add_argument("--from-file", default=None, help="Analyze a previously saved JSON file (no CloudWatch fetch)")
    p.add_argument("--region",  default=None, help="AWS region (default: from env/profile)")
    p.add_argument("--profile", default=None, help="AWS profile name")
    p.add_argument(
        "--provider",
        default="all",
        choices=ALL_PROVIDERS + ["all"],
        help="Provider to fetch/analyze (default: all)",
    )
    p.add_argument("--summary-only",   action="store_true", help="Only show total/summary events, skip service-level")
    p.add_argument("--throttled-only", action="store_true", help="Azure: only services with throttle_count > 0")
    p.add_argument("--failed-only",    action="store_true", help="Only show events with errors")
    p.add_argument("--service", default=None, help="Restrict stats to a single service name")
    p.add_argument("--top", type=int, default=None, help="Show top N slowest services per provider")
    return p.parse_args()


# ---------------------------------------------------------------------------
# CloudWatch fetch
# ---------------------------------------------------------------------------

def resolve_time_range(args: argparse.Namespace) -> Tuple[int, int]:
    now = datetime.now(timezone.utc)
    start_dt = (
        datetime.strptime(args.start, "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc)
        if args.start else now - timedelta(hours=args.hours)
    )
    end_dt = (
        datetime.strptime(args.end, "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc)
        if args.end else now
    )
    return int(start_dt.timestamp() * 1000), int(end_dt.timestamp() * 1000)


def fetch_logs(
    client: Any,
    log_group: str,
    stream_prefix: Optional[str],
    start_ms: int,
    end_ms: int,
    filter_pattern: str,
) -> List[Dict]:
    events: List[Dict] = []
    kwargs: Dict[str, Any] = {
        "logGroupName": log_group,
        "startTime": start_ms,
        "endTime": end_ms,
        "filterPattern": filter_pattern,
        "interleaved": True,
    }
    if stream_prefix:
        kwargs["logStreamNamePrefix"] = stream_prefix

    err("Fetching logs from {} ...", log_group)
    page = 0
    while True:
        resp = client.filter_log_events(**kwargs)
        batch = resp.get("events", [])
        events.extend(batch)
        page += 1
        err("  Page {}: {} events (total: {})", page, len(batch), len(events))
        next_token = resp.get("nextToken")
        if not next_token:
            break
        kwargs["nextToken"] = next_token
        time.sleep(0.2)

    return events


# ---------------------------------------------------------------------------
# Log parsing
# ---------------------------------------------------------------------------

def extract_log_text(raw_message: str) -> str:
    """Strip Kubernetes/Fluent-Bit JSON wrapper and return the actual log text."""
    msg = raw_message.strip()
    idx = msg.find("{")
    if idx != -1:
        try:
            outer = json.loads(msg[idx:])
            if "log" in outer:
                return outer["log"]
        except json.JSONDecodeError:
            pass
    return msg


def try_parse_structured_event(log_text: str) -> Optional[Dict]:
    """Return a structured timing event dict if log_text contains a known JSON timing event."""
    log_idx = log_text.find("{")
    if log_idx == -1:
        return None
    try:
        data = json.loads(log_text[log_idx:])
    except json.JSONDecodeError:
        try:
            data = ast.literal_eval(log_text[log_idx:])
        except (ValueError, SyntaxError):
            return None
    if not isinstance(data, dict):
        return None
    event_name = data.get("event", "")
    provider = _ALL_KNOWN_EVENTS.get(event_name)
    if provider is None:
        return None
    data["provider"] = provider
    return data


def parse_raw_event(raw_event: Dict) -> Optional[Dict]:
    """Parse a single CloudWatch log event into a normalized timing event dict."""
    log_text = extract_log_text(raw_event.get("message", ""))
    data = try_parse_structured_event(log_text)
    if data is None:
        return None
    data["_log_stream"] = raw_event.get("logStreamName", "")
    data["_timestamp"] = datetime.fromtimestamp(
        raw_event["timestamp"] / 1000, tz=timezone.utc
    ).isoformat()
    return data


def normalize_provider(events: List[Dict]) -> None:
    """Back-fill missing 'provider' field for events saved before this rewrite."""
    for e in events:
        if "provider" not in e:
            ev = e.get("event", "")
            provider = _ALL_KNOWN_EVENTS.get(ev)
            e["provider"] = provider if provider else "unknown"


# ---------------------------------------------------------------------------
# Stats printing
# ---------------------------------------------------------------------------

def _filter_service(events: List[Dict], svc: Optional[str]) -> List[Dict]:
    return events if not svc else [e for e in events if e.get("service") == svc]


def print_azure_service_stats(events: List[Dict], args: argparse.Namespace) -> None:
    svc_evs = [e for e in events if e.get("event") == "azure_service_timing"]
    svc_evs = _filter_service(svc_evs, args.service)

    if args.summary_only or not svc_evs:
        return

    by_svc: Dict[str, List] = defaultdict(list)
    for e in svc_evs:
        by_svc[e.get("service", "unknown")].append(e)

    if args.throttled_only:
        by_svc = {s: evs for s, evs in by_svc.items() if any(e.get("throttle_count", 0) > 0 for e in evs)}
    if args.failed_only:
        by_svc = {s: evs for s, evs in by_svc.items() if any(e.get("status") == "error" for e in evs)}

    if not by_svc:
        err("\nAzure: no service events match current filters.")
        return

    rows = []
    for svc, evs in by_svc.items():
        durs = [e.get("duration_seconds", 0) for e in evs]
        n = len(evs)
        errors = sum(1 for e in evs if e.get("status") == "error")
        rows.append((
            svc, n, errors,
            min(durs), sum(durs) / n, max(durs),
            sum(e.get("request_count", 0) for e in evs),
            sum(e.get("throttle_count", 0) for e in evs),
            sum(e.get("retry_count", 0) for e in evs),
        ))
    rows.sort(key=lambda r: r[4], reverse=True)
    if args.top:
        rows = rows[:args.top]

    W = 28
    err("\nAzure — per-service stats (sorted by avg duration):")
    err("  {:<{w}} {:>5} {:>6} {:>8} {:>8} {:>8} {:>8} {:>8} {:>7}",
        "service", "runs", "errors", "min(s)", "avg(s)", "max(s)", "reqs", "429s", "retries", w=W)
    err("  {}", "-" * (W + 2 + 5 + 6 + 8 * 4 + 7 + 6))
    for svc, n, err_cnt, mn, avg, mx, reqs, throttles, retries in rows:
        err("  {:<{w}} {:>5} {:>6} {} {} {} {:>8} {:>8} {:>7}",
            svc, n, err_cnt, fmt_sec(mn), fmt_sec(avg), fmt_sec(mx), reqs, throttles, retries, w=W)

    throttled = [(r[0], r[7]) for r in rows if r[7] > 0]
    failed    = [(r[0], r[2]) for r in rows if r[2] > 0]
    if throttled or failed:
        err("")
        for svc, count in throttled:
            err("  ⚠  {} — {} throttle(s) (Azure 429s inflate duration)", svc, count)
        for svc, count in failed:
            n = next(r[1] for r in rows if r[0] == svc)
            err("  ✗  {} — failed {}/{} run(s)", svc, count, n)


def print_azure_subscription_stats(events: List[Dict]) -> None:
    sub_evs = [e for e in events if e.get("event") == "azure_subscription_timing_summary"]
    if not sub_evs:
        return

    err("\nAzure — subscription summaries (sorted by total duration):")
    err("  {:<{w}} {:>10} {:>10} {:<22} {}",
        "subscription_id", "total(s)", "run_mode", "slowest_service", "failed_services", w=38)
    err("  {}", "-" * 105)
    for e in sorted(sub_evs, key=lambda x: x.get("total_duration_seconds", 0), reverse=True):
        sub     = e.get("subscription_id", "?")
        total   = e.get("total_duration_seconds", 0)
        mode    = e.get("run_mode", "?")
        slowest = e.get("slowest_service") or "?"
        failed  = e.get("failed_services", {})
        failed_str = ", ".join(f"{s}({t})" for s, t in failed.items()) if failed else "none"
        err("  {:<{w}} {:>10.1f} {:>10} {:<22} {}", sub, total, mode, slowest, failed_str, w=38)


def print_provider_stats(events: List[Dict], provider: str, args: argparse.Namespace) -> None:
    """Per-service and summary stats for non-Azure providers (JSON structured logging)."""
    service_event = f"{provider}_service_timing"
    scope_key = _PROVIDER_SCOPE_KEY.get(provider, "scope")

    svc_evs = [e for e in events if e.get("event") == service_event]
    sum_evs = [
        e for e in events
        if e.get("provider") == provider and e.get("event", "").endswith("_timing_summary")
    ]

    if not svc_evs and not sum_evs:
        return

    svc_evs = _filter_service(svc_evs, args.service)
    if args.failed_only:
        svc_evs = [e for e in svc_evs if e.get("status") == "error"]

    err("\n{} — per-service stats:", provider.upper())

    if svc_evs and not args.summary_only:
        by_svc: Dict[str, List] = defaultdict(list)
        for e in svc_evs:
            by_svc[e.get("service", "unknown")].append(e)

        rows = []
        for svc, evs in by_svc.items():
            durs = [e.get("duration_seconds", 0) for e in evs]
            n = len(evs)
            errors = sum(1 for e in evs if e.get("status") == "error")
            rows.append((svc, n, errors, min(durs), sum(durs) / n, max(durs)))
        rows.sort(key=lambda r: r[4], reverse=True)
        if args.top:
            rows = rows[:args.top]

        W = 24
        err("  {:<{w}} {:>5} {:>6} {:>8} {:>8} {:>8}",
            "service", "runs", "errors", "min(s)", "avg(s)", "max(s)", w=W)
        err("  {}", "-" * (W + 2 + 5 + 6 + 8 * 3 + 5))
        for svc, n, err_cnt, mn, avg, mx in rows:
            err("  {:<{w}} {:>5} {:>6} {} {} {}",
                svc, n, err_cnt, fmt_sec(mn), fmt_sec(avg), fmt_sec(mx), w=W)

    if sum_evs:
        top_n = args.top or len(sum_evs)
        sum_sorted = sorted(sum_evs, key=lambda e: e.get("total_duration_seconds", 0), reverse=True)[:top_n]
        # Derive a human-readable scope label from the event name
        # e.g. "aws_account_timing_summary" → "account"
        scope_label = sum_evs[0].get("event", "").replace(f"{provider}_", "").replace("_timing_summary", "")
        err("\n  {} summaries (sorted by total duration):", scope_label.capitalize() or "scope")
        err("  {:<{w}} {:>10} {:>22} {}",
            scope_label or "scope", "total(s)", "slowest_service", "failed", w=38)
        err("  {}", "-" * 85)
        for e in sum_sorted:
            # oci has both tenancy and compartment keys; fall back gracefully
            scope_id = e.get(scope_key) or e.get("compartment", "?")
            total    = e.get("total_duration_seconds", 0)
            slowest  = e.get("slowest_service") or "?"
            failed   = e.get("failed_services", {})
            failed_str = ", ".join(str(s) for s in failed) if failed else "none"
            err("  {:<{w}} {:>10.1f} {:>22} {}", scope_id, total, slowest, failed_str, w=38)


def print_error_details(events: List[Dict]) -> None:
    errors = [e for e in events if e.get("status") == "error"]
    if not errors:
        return
    err("\nFailed events:")
    for e in errors:
        prov     = e.get("provider", "?")
        svc      = e.get("service", e.get("event", "?"))
        scope_key = _PROVIDER_SCOPE_KEY.get(prov, "scope")
        scope_id  = e.get(scope_key) or e.get("subscription_id", "?")
        scope     = f"{scope_key}={scope_id}"
        ts        = e.get("_timestamp", "?")
        etype     = e.get("error_type", "")
        emsg      = e.get("error_message", "")
        suffix    = f" — {etype}({emsg})" if etype else ""
        err("  [{}] {} {} {}{}", ts, prov, scope, svc, suffix)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    args = parse_args()
    start_str = end_str = log_group_label = ""

    if args.from_file:
        with open(args.from_file) as f:
            saved = json.load(f)

        all_events: List[Dict] = saved.get("events", [])
        meta = saved.get("meta", {})
        normalize_provider(all_events)

        err("Loaded {} events from {}", len(all_events), args.from_file)
        start_str = meta.get("start", "?")
        end_str   = meta.get("end", "?")
        log_group_label = meta.get("log_group", args.from_file)
        err("Time range: {} → {}", start_str, end_str)

        if args.provider != "all":
            all_events = [e for e in all_events if e.get("provider") == args.provider]
            err("Filtered to provider={}: {} events", args.provider, len(all_events))

    else:
        if not args.log_group:
            err("Error: --log-group is required (or use --from-file to analyze a saved file)")
            sys.exit(1)

        session = boto3.Session(profile_name=args.profile, region_name=args.region)
        client  = session.client("logs")

        start_ms, end_ms = resolve_time_range(args)
        start_str = datetime.fromtimestamp(start_ms / 1000, tz=timezone.utc).isoformat()
        end_str   = datetime.fromtimestamp(end_ms / 1000, tz=timezone.utc).isoformat()
        log_group_label = args.log_group
        err("Time range: {} → {}", start_str, end_str)
        err("Provider filter: {}", args.provider)

        filter_pattern = _PROVIDER_FILTER.get(args.provider, _PROVIDER_FILTER["all"])
        raw_events = fetch_logs(client, args.log_group, args.log_stream_prefix, start_ms, end_ms, filter_pattern)

        all_events = []
        skipped = 0
        for e in raw_events:
            data = parse_raw_event(e)
            if data:
                all_events.append(data)
            else:
                skipped += 1

        err("\nParsed {} timing events ({} raw skipped)", len(all_events), skipped)

    # Partition by provider
    by_provider: Dict[str, List[Dict]] = defaultdict(list)
    for e in all_events:
        by_provider[e.get("provider", "unknown")].append(e)

    err("")
    for prov in sorted(by_provider):
        evs   = by_provider[prov]
        n_svc = sum(1 for e in evs if e.get("event", "").endswith("_service_timing"))
        n_sum = sum(1 for e in evs if e.get("event", "").endswith("_timing_summary"))
        err("  {:<14} service={:<5}  summary={}", prov, n_svc, n_sum)

    # ── Azure ────────────────────────────────────────────────────────────────
    azure_evs = by_provider.get("azure", [])
    print_azure_service_stats(azure_evs, args)
    print_azure_subscription_stats(azure_evs)

    # ── Other providers ──────────────────────────────────────────────────────
    for prov in ALL_PROVIDERS:
        if prov == "azure":
            continue
        if prov not in by_provider:
            continue
        print_provider_stats(all_events, prov, args)

    print_error_details(all_events)

    # ── JSON output ──────────────────────────────────────────────────────────
    if not args.from_file:
        output = {
            "meta": {
                "start":           start_str,
                "end":             end_str,
                "log_group":       log_group_label,
                "provider_filter": args.provider,
                "total_events":    len(all_events),
                "by_provider":     {p: len(evs) for p, evs in by_provider.items()},
            },
            "events": all_events,
        }
        if args.output:
            with open(args.output, "w") as f:
                json.dump(output, f, indent=2, default=str)
            err("\nWrote {} events to {}", len(all_events), args.output)
        else:
            print(json.dumps(output, indent=2, default=str))


if __name__ == "__main__":
    main()
