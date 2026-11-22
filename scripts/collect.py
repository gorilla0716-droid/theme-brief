"""테마 브리프 뉴스 수집기.

Google 뉴스 RSS(무료, 키 필요 없음)에서 themes.json의 테마별 검색어로 최근 기사를 모아
data.json을 새로 씁니다. 외부 패키지 없이 파이썬 표준 라이브러리만 사용합니다.
GitHub Actions가 평일 아침에 실행합니다 (.github/workflows/collect.yml).
"""
import json
import re
import sys
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
KST = timezone(timedelta(hours=9))
UA = "Mozilla/5.0 (theme-brief personal news collector)"

POS = ["급등", "상승", "반등", "강세", "수주", "호실적", "최대", "신고가", "흑자", "돌파", "회복", "계약", "승인", "확대", "훈풍", "기대"]
NEG = ["급락", "하락", "약세", "폭락", "우려", "감소", "적자", "부진", "쇼크", "규제", "중단", "하향", "매도", "리스크", "충격", "파란불", "털썩", "추락"]


def rss_url(query: str) -> str:
    q = urllib.parse.quote(f"{query} when:4d")
    return f"https://news.google.com/rss/search?q={q}&hl=ko&gl=KR&ceid=KR:ko"


def fetch(url: str, tries: int = 3) -> bytes:
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=20) as r:
                return r.read()
        except Exception as e:  # 네트워크 오류는 잠시 쉬었다 재시도
            print(f"  fetch 실패({i + 1}/{tries}): {e}", file=sys.stderr)
            time.sleep(2 * (i + 1))
    return b""


def parse(xml_bytes: bytes):
    items = []
    if not xml_bytes:
        return items
    try:
        root = ET.fromstring(xml_bytes)
    except ET.ParseError as e:
        print(f"  RSS 파싱 실패: {e}", file=sys.stderr)
        return items
    for it in root.iter("item"):
        title = (it.findtext("title") or "").strip()
        link = (it.findtext("link") or "").strip()
        src_el = it.find("source")
        source = (src_el.text or "").strip() if src_el is not None else ""
        try:
            pub = parsedate_to_datetime(it.findtext("pubDate") or "")
            if pub.tzinfo is None:
                pub = pub.replace(tzinfo=timezone.utc)
        except Exception:
            continue
        # Google 뉴스 제목은 "기사 제목 - 매체명" 형식 → 매체명 떼기
        if source and title.endswith(" - " + source):
            title = title[: -(len(source) + 3)].strip()
        elif not source and " - " in title:
            title, source = title.rsplit(" - ", 1)
        if title and link:
            items.append({"title": title, "url": link, "source": source or "뉴스", "pub": pub})
    return items


def tag_of(title: str) -> str:
    p = sum(w in title for w in POS)
    n = sum(w in title for w in NEG)
    return "p" if p > n else "n" if n > p else "z"


def norm(title: str) -> str:
    return re.sub(r"[\W_]+", "", title)[:28]


def collect_theme(queries, max_age_h, limit):
    now = datetime.now(timezone.utc)
    seen, out = set(), []
    for q in queries:
        print(f"  검색: {q}")
        for it in parse(fetch(rss_url(q))):
            if now - it["pub"] > timedelta(hours=max_age_h):
                continue
            key = norm(it["title"])
            if key in seen:
                continue
            seen.add(key)
            out.append(it)
        time.sleep(1)  # 요청 간격
    out.sort(key=lambda x: x["pub"], reverse=True)
    return out[:limit]


def to_news(it):
    return {
        "date": it["pub"].astimezone(KST).strftime("%m.%d"),
        "source": it["source"],
        "tag": tag_of(it["title"]),
        "title": it["title"],
        "summary": "",
        "url": it["url"],
    }


def main():
    cfg = json.loads((ROOT / "themes.json").read_text(encoding="utf-8"))
    old_path = ROOT / "data.json"
    old = json.loads(old_path.read_text(encoding="utf-8")) if old_path.exists() else {}
    old_themes = {t["id"]: t for t in old.get("themes", [])}
    max_age, limit = cfg.get("max_age_hours", 96), cfg.get("max_news", 8)

    themes, got_any = [], False
    for t in cfg["themes"]:
        print(f"[{t['name']}]")
        items = collect_theme(t["queries"], max_age, limit)
        if items:
            got_any = True
            news = [to_news(i) for i in items]
            summary = [f"{n['title'][:70]} ({n['source']})" for n in news[:3]]
        else:  # 이번에 못 가져오면 지난 내용 유지
            prev = old_themes.get(t["id"], {})
            news, summary = prev.get("news", []), prev.get("summary", [])
            print("  새 기사 없음 → 이전 내용 유지")
        themes.append({
            "id": t["id"], "name": t["name"], "keywords": t.get("keywords", ""),
            "summary": summary, "watch": t.get("watch", ""),
            "news": news, "stocks": t.get("stocks", []),
        })

    if not got_any:
        print("모든 테마 수집 실패 → data.json을 바꾸지 않습니다.", file=sys.stderr)
        sys.exit(1)

    headline = old.get("headline")
    mq = cfg.get("market_query")
    if mq:
        print("[마감 시황]")
        hits = [i for i in collect_theme([mq], 72, 10) if "코스피" in i["title"]]
        if hits:
            h = hits[0]
            headline = {"title": h["title"], "url": h["url"], "source": h["source"],
                        "date": h["pub"].astimezone(KST).strftime("%m.%d")}

    data = {
        "updatedAt": datetime.now(KST).isoformat(timespec="seconds"),
        "asOf": "", "marketSource": "", "market": [],
        "headline": headline,
        "themes": themes,
    }
    old_path.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"완료: 테마 {len(themes)}개, 기사 {sum(len(t['news']) for t in themes)}건")


if __name__ == "__main__":
    main()
