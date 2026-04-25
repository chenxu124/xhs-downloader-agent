#!/usr/bin/env python3
"""Batch-download XHS account videos through XHS-Downloader API.

Flow:
1) Launch a visible browser and let user log in manually.
2) Open profile page and auto-scroll to collect note links.
3) Call XHS-Downloader API `/xhs/detail` per link:
   - metadata pass (`download=false`) to detect video notes
   - download pass (`download=true`) for video notes only
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Iterable
from urllib.parse import urljoin, urlparse

import requests
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import sync_playwright

NOTE_PATTERNS = [
    re.compile(r"/explore/[A-Za-z0-9]+"),
    re.compile(r"/discovery/item/[A-Za-z0-9]+"),
    re.compile(r"/user/profile/[A-Za-z0-9]+/[A-Za-z0-9]+"),
]

VIDEO_HINTS = ("video", "stream", ".mp4", "h264", "h265", "m3u8", "note_type\":\"video")
IMAGE_HINTS = ("image_list", "images", ".jpg", ".jpeg", ".png", ".webp", ".heic")

WINDOWS_BROWSER_CANDIDATES = {
    "chrome": [
        Path(os.environ.get("PROGRAMFILES", "")) / "Google/Chrome/Application/chrome.exe",
        Path(os.environ.get("PROGRAMFILES(X86)", "")) / "Google/Chrome/Application/chrome.exe",
        Path(os.environ.get("LOCALAPPDATA", "")) / "Google/Chrome/Application/chrome.exe",
    ],
    "edge": [
        Path(os.environ.get("PROGRAMFILES", "")) / "Microsoft/Edge/Application/msedge.exe",
        Path(os.environ.get("PROGRAMFILES(X86)", "")) / "Microsoft/Edge/Application/msedge.exe",
        Path(os.environ.get("LOCALAPPDATA", "")) / "Microsoft/Edge/Application/msedge.exe",
    ],
}


def normalize_note_url(href: str) -> str | None:
    href = (href or "").strip()
    if not href or href.startswith("javascript:"):
        return None

    if href.startswith("//"):
        href = "https:" + href
    if href.startswith("/"):
        href = urljoin("https://www.xiaohongshu.com", href)

    parsed = urlparse(href)
    if "xiaohongshu.com" not in parsed.netloc:
        return None

    clean = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
    for pattern in NOTE_PATTERNS:
        if pattern.search(clean):
            return clean
    return None


def normalize_note_url_with_query(href: str) -> str | None:
    href = (href or "").strip()
    if not href or href.startswith("javascript:"):
        return None

    if href.startswith("//"):
        href = "https:" + href
    if href.startswith("/"):
        href = urljoin("https://www.xiaohongshu.com", href)

    parsed = urlparse(href)
    if "xiaohongshu.com" not in parsed.netloc:
        return None

    clean = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
    for pattern in NOTE_PATTERNS:
        if pattern.search(clean):
            return href
    return None


def extract_note_links_from_page(page) -> set[str]:
    hrefs = page.eval_on_selector_all("a[href]", "els => els.map(e => e.getAttribute('href'))")
    links = set()
    for href in hrefs:
        url = normalize_note_url(href or "")
        if url:
            links.add(url)
    return links


def auto_scroll_collect_links(
    page,
    profile_url: str,
    max_scrolls: int,
    pause_sec: float,
    stable_rounds: int,
    max_notes: int,
) -> list[str]:
    collected: dict[str, str] = {}
    no_change_round = 0
    last_count = 0

    for idx in range(max_scrolls):
        dismiss_overlays(page)
        hrefs = page.eval_on_selector_all(
            "section.note-item a[href]",
            "els => els.map(e => e.getAttribute('href')).filter(Boolean)",
        )
        for href in hrefs:
            full_url = normalize_note_url_with_query(href)
            if not full_url or "xsec_token=" not in full_url:
                continue

            full_url = full_url.replace("&amp;", "&")
            full_path = urlparse(full_url).path
            if full_path in collected:
                continue

            collected[full_path] = full_url
            print(f"[NOTE] collected={len(collected)} {full_url}")

            if max_notes > 0 and len(collected) >= max_notes:
                return list(collected.values())

        page.mouse.wheel(0, 3000)
        page.wait_for_timeout(int(pause_sec * 1000))

        count = len(collected)
        print(f"[SCROLL] {idx + 1}/{max_scrolls} links={count}")

        if count == last_count:
            no_change_round += 1
        else:
            no_change_round = 0
            last_count = count

        if no_change_round >= stable_rounds:
            print(f"[SCROLL] no new links for {stable_rounds} rounds, stop early")
            break

    return list(collected.values())


def cookies_to_header(cookies: Iterable[dict]) -> str:
    pairs: list[str] = []
    for cookie in cookies:
        domain = cookie.get("domain", "")
        name = cookie.get("name")
        value = cookie.get("value")
        if "xiaohongshu.com" in domain and name and value:
            pairs.append(f"{name}={value}")
    return "; ".join(pairs)


def looks_like_video(meta: dict) -> bool:
    text = json.dumps(meta, ensure_ascii=False).lower()
    has_video = any(h in text for h in VIDEO_HINTS)
    has_image = any(h in text for h in IMAGE_HINTS)

    if has_video:
        return True
    if has_image and not has_video:
        return False
    return False


def log_message(log_file: Path | None, message: str) -> None:
    print(message)
    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        with log_file.open("a", encoding="utf-8") as handle:
            handle.write(message + "\n")


def call_detail(api_base: str, url: str, cookie_header: str, download: bool, timeout: int) -> dict:
    endpoint = api_base.rstrip("/") + "/xhs/detail"
    payload = {
        "url": url,
        "download": download,
        "cookie": cookie_header,
        "skip": True,
    }
    resp = requests.post(endpoint, json=payload, timeout=timeout)
    resp.raise_for_status()
    return resp.json()


def inspect_profile_state(page) -> dict:
    body_text = page.locator("body").inner_text(timeout=10000)
    login_markers = (
        "登录即可查看ta的笔记",
        "登录即可查看",
        "手机号登录",
        "获取验证码",
        "扫码",
    )
    normalized = re.sub(r"\s+", "", body_text).lower()
    card_count = page.locator("section.note-item").count()
    anchor_count = page.locator("section.note-item a[href]").count()
    return {
        "requires_login": any(marker in normalized for marker in login_markers),
        "card_count": card_count,
        "anchor_count": anchor_count,
        "body_preview": body_text[:400].replace("\n", " "),
        "current_url": page.url,
        "title": page.title(),
    }


def write_failure_snapshot(page, snapshot_dir: Path) -> tuple[Path, Path]:
    snapshot_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    html_path = snapshot_dir / f"profile_failure_{timestamp}.html"
    png_path = snapshot_dir / f"profile_failure_{timestamp}.png"
    html_path.write_text(page.content(), encoding="utf-8")
    page.screenshot(path=str(png_path), full_page=True)
    return html_path, png_path


def dismiss_overlays(page) -> None:
    page.keyboard.press("Escape")
    page.evaluate(
        """() => {
            const selectors = [
                '.reds-mask',
                '.code-area',
                '[aria-label="弹窗遮罩"]',
                '[class*="mask"]',
                '[class*="overlay"]'
            ];
            for (const selector of selectors) {
                for (const element of document.querySelectorAll(selector)) {
                    element.style.pointerEvents = 'none';
                    element.style.display = 'none';
                    element.style.visibility = 'hidden';
                }
            }
        }"""
    )


def resolve_browser_launch_options(args: argparse.Namespace) -> dict:
    if args.browser_path:
        browser_path = Path(args.browser_path).expanduser().resolve()
        if not browser_path.is_file():
            raise FileNotFoundError(f"browser executable not found: {browser_path}")
        return {"executable_path": str(browser_path), "browser_label": str(browser_path)}

    for browser_name in args.browser_preference:
        for candidate in WINDOWS_BROWSER_CANDIDATES.get(browser_name, []):
            if candidate.is_file():
                return {"executable_path": str(candidate), "browser_label": browser_name}

    return {"browser_label": "playwright-managed chromium"}


def run(args: argparse.Namespace) -> int:
    user_data_dir = Path(args.user_data_dir).resolve()
    user_data_dir.mkdir(parents=True, exist_ok=True)
    launch_options = resolve_browser_launch_options(args)
    log_file = Path(args.log_file).resolve() if args.log_file else None
    snapshot_dir = Path(args.snapshot_dir).resolve()

    with sync_playwright() as p:
        log_message(log_file, f"Launching browser: {launch_options['browser_label']}")
        context = p.chromium.launch_persistent_context(
            user_data_dir=str(user_data_dir),
            headless=False,
            viewport={"width": 1440, "height": 900},
            executable_path=launch_options.get("executable_path"),
        )

        page = context.new_page()
        try:
            page.goto("https://www.xiaohongshu.com", wait_until="domcontentloaded", timeout=45000)
        except PlaywrightTimeoutError:
            log_message(log_file, "WARN: initial site open timeout; continue")

        log_message(log_file, "Please log in in the opened browser window.")
        if args.login_wait_seconds > 0:
            log_message(log_file, f"Waiting {args.login_wait_seconds} seconds for manual login...")
            page.wait_for_timeout(args.login_wait_seconds * 1000)
        else:
            input("Press Enter here after login is complete...")

        try:
            page.goto(args.profile_url, wait_until="domcontentloaded", timeout=45000)
        except PlaywrightTimeoutError:
            log_message(log_file, "WARN: profile page timeout; continue with current DOM")
        try:
            page.wait_for_selector("section.note-item", timeout=30000)
        except PlaywrightTimeoutError:
            log_message(log_file, "WARN: no note cards rendered on profile page")

        profile_state = inspect_profile_state(page)
        log_message(log_file, "Profile state: " + json.dumps(profile_state, ensure_ascii=False))
        if profile_state["requires_login"] or profile_state["card_count"] == 0:
            html_path, png_path = write_failure_snapshot(page, snapshot_dir)
            log_message(
                log_file,
                "ERROR: profile page is not ready for collection. Complete login and ensure notes are visible. "
                f"Snapshot HTML: {html_path} Screenshot: {png_path}",
            )
            context.close()
            return 1

        log_message(log_file, f"Profile page: {args.profile_url}")
        links = auto_scroll_collect_links(
            page=page,
            profile_url=args.profile_url,
            max_scrolls=args.max_scrolls,
            pause_sec=args.scroll_pause,
            stable_rounds=args.stable_rounds,
            max_notes=args.max_notes,
        )

        if args.links_output:
            Path(args.links_output).write_text("\n".join(links), encoding="utf-8")
            log_message(log_file, f"Saved links to: {args.links_output}")

        log_message(log_file, f"Collected links: {len(links)}")

        cookie_header = cookies_to_header(context.cookies())
        context.close()

    if not cookie_header:
        log_message(log_file, "ERROR: no xiaohongshu cookie found. Please re-run and login first.")
        return 1

    total = len(links)
    ok = 0
    skipped_non_video = 0
    failed = 0

    for idx, link in enumerate(links, start=1):
        log_message(log_file, f"[{idx}/{total}] {link}")
        try:
            meta = call_detail(args.api_base, link, cookie_header, download=False, timeout=args.timeout)
            if not looks_like_video(meta):
                skipped_non_video += 1
                log_message(log_file, "  -> skip non-video note")
                continue

            call_detail(args.api_base, link, cookie_header, download=True, timeout=args.timeout)
            ok += 1
            log_message(log_file, "  -> download submitted")
        except Exception as exc:  # pylint: disable=broad-except
            failed += 1
            log_message(log_file, f"  -> failed: {exc}")

        time.sleep(args.request_interval)

    log_message(log_file, "========== DONE ==========")
    log_message(log_file, f"Total links: {total}")
    log_message(log_file, f"Video submitted: {ok}")
    log_message(log_file, f"Skipped non-video: {skipped_non_video}")
    log_message(log_file, f"Failed: {failed}")
    return 0 if failed == 0 else 2


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Batch collect XHS profile notes and download videos via XHS-Downloader API"
    )
    parser.add_argument("--profile-url", required=True, help="XHS profile URL")
    parser.add_argument("--api-base", default="http://127.0.0.1:5556", help="XHS-Downloader API base URL")
    parser.add_argument("--user-data-dir", default=".xhs_browser", help="Playwright persistent user data dir")
    parser.add_argument(
        "--browser-path",
        default="",
        help="Optional local browser executable path, e.g. C:/Program Files/Google/Chrome/Application/chrome.exe",
    )
    parser.add_argument(
        "--browser-preference",
        nargs="+",
        default=["chrome", "edge"],
        choices=["chrome", "edge"],
        help="Preferred local browsers to try before Playwright-managed Chromium",
    )
    parser.add_argument("--max-scrolls", type=int, default=120, help="Maximum auto-scroll rounds")
    parser.add_argument("--scroll-pause", type=float, default=1.0, help="Pause seconds between scrolls")
    parser.add_argument("--stable-rounds", type=int, default=6, help="Stop when no new links for N rounds")
    parser.add_argument("--request-interval", type=float, default=1.2, help="Seconds between API requests")
    parser.add_argument("--timeout", type=int, default=30, help="API timeout in seconds")
    parser.add_argument("--links-output", default="xhs_links.txt", help="Output file for collected links")
    parser.add_argument("--max-notes", type=int, default=0, help="Stop after collecting N note URLs; 0 means no limit")
    parser.add_argument("--log-file", default="xhs_agent.log", help="Optional log file path")
    parser.add_argument("--snapshot-dir", default="xhs_agent_debug", help="Directory for failure HTML and screenshots")
    parser.add_argument(
        "--login-wait-seconds",
        type=int,
        default=0,
        help="Wait N seconds for manual login instead of prompting for Enter",
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return run(args)


if __name__ == "__main__":
    sys.exit(main())
