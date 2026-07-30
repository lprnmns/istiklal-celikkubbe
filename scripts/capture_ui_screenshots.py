import base64
import json
import subprocess
import time
import urllib.request
from pathlib import Path
from urllib.error import URLError


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "reports" / "screenshots" / "ui_safety_polish"
BASE = "http://127.0.0.1:5173"
API_BASE = "http://127.0.0.1:8000"
GECKODRIVER = "/snap/bin/geckodriver"
PORT = 4444


def request(method: str, path: str, payload: dict | None = None) -> dict:
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        f"http://127.0.0.1:{PORT}{path}",
        data=data,
        method=method,
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=10) as response:
        return json.loads(response.read().decode("utf-8"))


def backend_request(method: str, path: str, payload: dict | None = None) -> dict:
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        f"{API_BASE}{path}",
        data=data,
        method=method,
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=10) as response:
        return json.loads(response.read().decode("utf-8"))


def wait_driver() -> None:
    for _ in range(50):
        try:
            request("GET", "/status")
            return
        except (URLError, TimeoutError, ConnectionError):
            time.sleep(0.1)
    raise RuntimeError("geckodriver did not start")


def execute(session_id: str, script: str):
    return request(
        "POST",
        f"/session/{session_id}/execute/sync",
        {"script": script, "args": []},
    ).get("value")


def navigate(session_id: str, path: str, wait_s: float = 1.2) -> None:
    request("POST", f"/session/{session_id}/url", {"url": f"{BASE}{path}"})
    time.sleep(wait_s)


def click_text(session_id: str, text: str, wait_s: float = 1.0) -> None:
    execute(
        session_id,
        f"""
        const wanted = {json.dumps(text)};
        const candidates = Array.from(document.querySelectorAll('button, a, option'));
        const el = candidates.find((item) => (item.textContent || '').trim().includes(wanted));
        if (!el) throw new Error('Clickable text not found: ' + wanted);
        el.click();
        """,
    )
    time.sleep(wait_s)


def click_first_available_text(session_id: str, texts: list[str], wait_s: float = 1.0) -> bool:
    clicked = bool(
        execute(
            session_id,
            f"""
            const texts = {json.dumps(texts)};
            const candidates = Array.from(document.querySelectorAll('button, a, option'));
            for (const wanted of texts) {{
              const el = candidates.find((item) => (item.textContent || '').trim().includes(wanted));
              if (el) {{
                el.click();
                return true;
              }}
            }}
            return false;
            """,
        )
    )
    time.sleep(wait_s)
    return clicked


def click_button_exact(session_id: str, text: str, wait_s: float = 1.0) -> None:
    execute(
        session_id,
        f"""
        const wanted = {json.dumps(text)};
        const el = Array.from(document.querySelectorAll('button')).find((item) =>
          (item.textContent || '').trim() === wanted
        );
        if (!el) throw new Error('Button not found: ' + wanted);
        el.scrollIntoView({{ block: 'center' }});
        el.click();
        """,
    )
    time.sleep(wait_s)


def set_input_placeholder(session_id: str, placeholder: str, value: str) -> None:
    execute(
        session_id,
        f"""
        const el = Array.from(document.querySelectorAll('input')).find((item) =>
          item.placeholder === {json.dumps(placeholder)}
        );
        if (!el) throw new Error('Input placeholder not found: ' + {json.dumps(placeholder)});
        el.value = {json.dumps(value)};
        el.dispatchEvent(new Event('input', {{ bubbles: true }}));
        """,
    )
    time.sleep(0.3)


def select_lens(session_id: str, value: str) -> None:
    execute(
        session_id,
        f"""
        const select = Array.from(document.querySelectorAll('select')).find((item) =>
          Array.from(item.options).some((option) => option.value === {json.dumps(value)})
        );
        if (!select) throw new Error('Lens select not found');
        select.value = {json.dumps(value)};
        select.dispatchEvent(new Event('change', {{ bubbles: true }}));
        """,
    )
    time.sleep(0.5)


def make_pico_profile_invalid(session_id: str) -> None:
    execute(
        session_id,
        """
        const functionSelect = Array.from(document.querySelectorAll('select')).find((item) => {
          const values = Array.from(item.options).map((option) => option.value);
          return values.includes('PAN_STEP') && values.includes('UNUSED');
        });
        if (!functionSelect) throw new Error('Pin function select not found');
        functionSelect.value = 'UNUSED';
        functionSelect.dispatchEvent(new Event('input', { bubbles: true }));
        functionSelect.dispatchEvent(new Event('change', { bubbles: true }));
        """,
    )
    time.sleep(0.4)


def scroll_to(session_id: str, y: int) -> None:
    execute(session_id, f"window.scrollTo(0, {y});")
    time.sleep(0.4)


def scroll_to_text(session_id: str, text: str) -> None:
    execute(
        session_id,
        f"""
        const wanted = {json.dumps(text)};
        const el = Array.from(document.querySelectorAll('h3, h2, div, section, p')).find((item) =>
          (item.textContent || '').includes(wanted)
        );
        if (!el) throw new Error('Text not found: ' + wanted);
        el.scrollIntoView({{ block: 'center' }});
        """,
    )
    time.sleep(0.5)


def scroll_to_heading(session_id: str, text: str) -> None:
    execute(
        session_id,
        f"""
        if (!document.getElementById('screenshot-scroll-spacer')) {{
          const spacer = document.createElement('div');
          spacer.id = 'screenshot-scroll-spacer';
          spacer.style.height = '1300px';
          document.body.appendChild(spacer);
        }}
        const wanted = {json.dumps(text)};
        const el = Array.from(document.querySelectorAll('h3, h2')).find((item) =>
          (item.textContent || '').trim() === wanted
        );
        if (!el) throw new Error('Heading not found: ' + wanted);
        const top = el.getBoundingClientRect().top + window.scrollY - 160;
        window.scrollTo(0, Math.max(0, top));
        """,
    )
    time.sleep(0.5)


def hide_card_by_heading(session_id: str, text: str) -> None:
    execute(
        session_id,
        f"""
        const wanted = {json.dumps(text)};
        const headings = Array.from(document.querySelectorAll('h3, h2')).filter((item) =>
          (item.textContent || '').trim() === wanted
        );
        for (const heading of headings) {{
          const section = heading.closest('section');
          if (section) section.style.display = 'none';
        }}
        """,
    )
    time.sleep(0.2)


def compress_card_by_heading(session_id: str, text: str, max_height: int = 260) -> None:
    execute(
        session_id,
        f"""
        const wanted = {json.dumps(text)};
        const heading = Array.from(document.querySelectorAll('h3, h2')).find((item) =>
          (item.textContent || '').trim() === wanted
        );
        if (heading) {{
          const section = heading.closest('section');
          if (section) {{
            section.style.height = {json.dumps(str(max_height) + 'px')};
            section.style.overflow = 'hidden';
          }}
        }}
        """,
    )
    time.sleep(0.2)


def screenshot(session_id: str, name: str) -> None:
    raw = request("GET", f"/session/{session_id}/screenshot")["value"]
    path = OUT / name
    path.write_bytes(base64.b64decode(raw))
    print(path)


def clear_old_screenshots() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    for path in OUT.glob("*.png"):
        path.unlink()


def main() -> None:
    clear_old_screenshots()
    backend_request("POST", "/api/safety/arm")
    driver = subprocess.Popen(
        [GECKODRIVER, "--host", "127.0.0.1", "--port", str(PORT)],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    try:
        wait_driver()
        session = request(
            "POST",
            "/session",
            {
                "capabilities": {
                    "alwaysMatch": {
                        "browserName": "firefox",
                        "acceptInsecureCerts": True,
                        "moz:firefoxOptions": {"args": ["-headless"]},
                    }
                }
            },
        )
        session_id = session["value"]["sessionId"]
        request("POST", f"/session/{session_id}/window/rect", {"width": 1440, "height": 1200})

        navigate(session_id, "/pico")
        make_pico_profile_invalid(session_id)
        click_button_exact(session_id, "Validate Preview", wait_s=2.0)
        scroll_to_text(session_id, "Apply / Save")
        screenshot(session_id, "01_pico_invalid_apply_save_disabled.png")
        scroll_to(session_id, 0)
        screenshot(session_id, "02_pico_pinout_color_badges.png")

        navigate(session_id, "/serial")
        click_text(session_id, "Clear Logs", wait_s=0.7)
        for _ in range(3):
            click_text(session_id, "Send Safe JSON", wait_s=0.7)
        scroll_to_text(session_id, "Serial Log")
        screenshot(session_id, "03_serial_heartbeat_seq_1_2_3_log.png")

        navigate(session_id, "/safety")
        click_first_available_text(session_id, ["Arm Dry-run", "Re-evaluate Arm Readiness"], wait_s=1.2)
        scroll_to_heading(session_id, "Safety Gates Matrix")
        screenshot(session_id, "04_safety_armed_dry_run_gate_names.png")
        click_text(session_id, "Fire Request Evaluation", wait_s=1.2)
        hide_card_by_heading(session_id, "Latest Decision Events")
        scroll_to_heading(session_id, "Fire Request Evaluation Response")
        screenshot(session_id, "05_safety_fire_request_response_card.png")

        navigate(session_id, "/color")
        click_text(session_id, "Preview Mask")
        scroll_to_heading(session_id, "Mask Preview / Warnings")
        screenshot(session_id, "06_color_preview_mask_placeholder.png")

        navigate(session_id, "/calibration")
        select_lens(session_id, "8mm")
        select_lens(session_id, "12mm")
        scroll_to_heading(session_id, "Lens Comparison")
        screenshot(session_id, "07_calibration_lens_comparison_width.png")

        navigate(session_id, "/logs")
        set_input_placeholder(session_id, "Search type or summary", "serial")
        click_text(session_id, "Export JSONL")
        hide_card_by_heading(session_id, "Logs")
        scroll_to_heading(session_id, "Log Controls")
        screenshot(session_id, "08_logs_filter_search_detail.png")

        request("DELETE", f"/session/{session_id}")
    finally:
        driver.terminate()
        try:
            driver.wait(timeout=3)
        except subprocess.TimeoutExpired:
            driver.kill()


if __name__ == "__main__":
    main()
