#!/usr/bin/env python3
"""保研skill — 夏令营/预推免通知爬虫

从各校机械学院通知页抓取最新通知，提取标题、日期、链接等关键信息。
采用两阶段策略：
  1. Python 批量抓取 HTML → 通用正文提取 → 缓存到本地
  2. Claude (WebFetch) 对重点学校做语义解析（截止日期、申请条件等）

用法:
  python notice_scraper.py --school all
  python notice_scraper.py --school 上交,浙大,华科
  python notice_scraper.py --school all --refresh  # 强制刷新
  python notice_scraper.py --school all --output data/notices/index.json
"""

import argparse
import json
import os
import random
import re
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from urllib.parse import urljoin, urlparse

import requests
import yaml
from bs4 import BeautifulSoup

# 默认路径
SKILL_DIR = Path(os.environ.get("CLAUDE_SKILL_DIR", Path(__file__).parent.parent))
CONFIG_FILE = SKILL_DIR / "config" / "schools.yaml"
DATA_DIR = SKILL_DIR / "data" / "notices"
INDEX_FILE = DATA_DIR / "index.json"

# HTTP 请求头
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/125.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    "Accept-Encoding": "gzip, deflate",
}


def load_config():
    """加载学校配置"""
    if not CONFIG_FILE.exists():
        print(f"[错误] 配置文件不存在: {CONFIG_FILE}")
        sys.exit(1)
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_cache():
    """加载缓存"""
    if INDEX_FILE.exists():
        with open(INDEX_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"updated_at": None, "schools": {}}


def save_cache(data):
    """保存缓存"""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    data["updated_at"] = datetime.now().isoformat()
    with open(INDEX_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def is_cache_valid(cache, max_hours=6):
    """检查缓存是否有效"""
    if not cache.get("updated_at"):
        return False
    updated = datetime.fromisoformat(cache["updated_at"])
    return (datetime.now() - updated) < timedelta(hours=max_hours)


def fetch_page(url, timeout=15, encoding="utf-8"):
    """获取页面 HTML，自动处理编码和常见反爬"""
    try:
        resp = requests.get(url, headers=HEADERS, timeout=timeout, allow_redirects=True)
        resp.raise_for_status()

        # 自动检测编码
        if resp.apparent_encoding and resp.apparent_encoding.lower() != "ascii":
            resp.encoding = resp.apparent_encoding
        elif encoding:
            resp.encoding = encoding

        return resp.text, resp.url
    except requests.exceptions.Timeout:
        print(f"  [超时] {url}")
        return None, url
    except requests.exceptions.ConnectionError:
        print(f"  [连接失败] {url}")
        return None, url
    except requests.exceptions.HTTPError as e:
        print(f"  [HTTP {e.response.status_code}] {url}")
        return None, url
    except Exception as e:
        print(f"  [错误] {url}: {e}")
        return None, url


def extract_notice_links(html, base_url):
    """从页面中提取通知链接列表

    通用策略：在页面中寻找 <a> 标签，链接文字包含「夏令营」「预推免」「推免」
    「研究生招生」「优秀大学生」等关键词。
    同时提取所有看起来像通知标题的链接。
    """
    soup = BeautifulSoup(html, "lxml")
    notices = []

    # 关键词列表
    keywords = [
        "夏令营", "预推免", "推免", "研究生招生", "优秀大学生",
        "暑期学校", "保研", "接收推荐", "免试", "招生简章",
        "报名通知", "复试", "选拔", "暑期夏令营",
        "summer camp", "summer school", "graduate admission",
    ]

    # 获取所有链接
    for a_tag in soup.find_all("a", href=True):
        text = a_tag.get_text(strip=True)
        href = a_tag["href"]

        if not text or len(text) < 4:
            continue

        # 构造完整 URL
        full_url = urljoin(base_url, href)

        # 检查是否匹配关键词
        matched = [kw for kw in keywords if kw.lower() in text.lower()]

        if matched:
            notices.append({
                "title": text,
                "url": full_url,
                "matched_keywords": matched,
            })

    # 如果没有精确匹配，尝试提取所有看起来像通知的链接
    if not notices:
        for a_tag in soup.find_all("a", href=True):
            text = a_tag.get_text(strip=True)
            href = a_tag["href"]
            if not text or len(text) < 6:
                continue
            # 找到包含日期格式的标题，或放在 <li> 中的链接
            parent_li = a_tag.find_parent("li")
            if parent_li:
                # 查找日期
                date_span = parent_li.find("span", class_=re.compile(r"date|time|Date"))
                date_text = date_span.get_text(strip=True) if date_span else ""
                full_url = urljoin(base_url, href)
                notices.append({
                    "title": text,
                    "url": full_url,
                    "date_hint": date_text,
                    "matched_keywords": [],
                })

    return notices[:20]  # 最多取20条


def extract_page_content(html):
    """提取页面主要文本内容

    尝试多种策略找到正文区域，去掉导航、页脚等。
    返回干净的文本内容。
    """
    soup = BeautifulSoup(html, "lxml")

    # 移除不需要的元素
    for tag in soup.find_all(["script", "style", "nav", "footer", "header"]):
        tag.decompose()

    # 策略1：常见的正文容器
    content_selectors = [
        {"class_": re.compile(r"content|article|entry|main|body|text|con|wp")},
        {"id": re.compile(r"content|article|entry|main|body")},
        {"role": "main"},
    ]

    content = None
    for selector in content_selectors:
        content = soup.find("div", **selector) or soup.find("section", **selector) or soup.find("article", **selector)
        if content:
            break

    # 策略2：取 <body> 下最大的文本块
    if not content:
        # 简单取 body 文本
        content = soup.find("body")
    if not content:
        content = soup

    # 提取文本，控制长度
    text = content.get_text(separator="\n", strip=True)

    # 清理：合并空行
    lines = [line for line in text.split("\n") if line.strip()]
    text = "\n".join(lines)

    # 限制长度（太长的页面只保留前5000字符）
    if len(text) > 5000:
        text = text[:5000] + "\n\n... [内容过长，已截断]"

    return text


def scrape_school(school, refresh=False, cache=None, delay=2):
    """抓取单个学校的通知"""
    name = school["name"]
    short = school.get("short", name)
    urls = school.get("urls", {})
    notice_url = urls.get("notice", urls.get("home"))

    print(f"\n{'='*50}")
    print(f"[{short}] {name} — {school.get('college', '')}")
    print(f" URL: {notice_url}")

    # 检查缓存
    school_cache = cache.get("schools", {}).get(short, {})
    if not refresh and school_cache.get("fetched_at"):
        fetched = datetime.fromisoformat(school_cache["fetched_at"])
        age = datetime.now() - fetched
        if age < timedelta(hours=6):
            print(f"  [缓存] 使用 {age.seconds // 3600} 小时前的缓存，跳过抓取")
            return school_cache

    if not notice_url:
        print(f"  [跳过] 无通知页URL")
        return {"fetched_at": datetime.now().isoformat(), "notice_url": None, "notices": [], "error": "无URL"}

    # 获取页面
    time.sleep(delay + random.uniform(0, 1))
    html, final_url = fetch_page(notice_url, timeout=school.get("urls", {}).get("timeout", 15))

    if not html:
        return {
            "fetched_at": datetime.now().isoformat(),
            "notice_url": notice_url,
            "notices": [],
            "error": "页面获取失败",
        }

    # 提取通知链接
    notices = extract_notice_links(html, final_url)

    # 如果没有匹配到特定通知，尝试提取页面内容
    page_text = ""
    if not notices:
        page_text = extract_page_content(html)

    result = {
        "fetched_at": datetime.now().isoformat(),
        "notice_url": notice_url,
        "final_url": final_url,
        "notice_count": len(notices),
        "notices": notices if notices else [],
        "page_text_snippet": page_text[:1000] if page_text else "",
        "error": None if (notices or page_text) else "未能提取到通知内容",
    }

    print(f"  [结果] 提取到 {len(notices)} 条通知链接")
    for n in notices[:5]:
        print(f"    - {n['title'][:60]}")

    return result


def scrape_all(schools_config, target_schools="all", refresh=False):
    """抓取所有（或指定）学校"""
    all_schools = schools_config.get("schools", [])
    scraper_config = schools_config.get("scraper", {})
    delay = scraper_config.get("delay_seconds", 2)
    cache_hours = scraper_config.get("cache_hours", 6)

    cache = load_cache()

    # 筛选目标学校
    if target_schools == "all":
        targets = all_schools
    else:
        target_shorts = [s.strip() for s in target_schools.split(",")]
        targets = [s for s in all_schools if s.get("short") in target_shorts]
        if not targets:
            print(f"[错误] 未找到匹配的学校: {target_schools}")
            print(f"       可用简称: {', '.join(s['short'] for s in all_schools)}")
            sys.exit(1)

    print(f"开始抓取 {len(targets)} 所学校...")
    print(f"请求间隔: {delay}s | 缓存有效期: {cache_hours}h\n")

    results = {}
    success_count = 0
    fail_count = 0

    for school in targets:
        try:
            result = scrape_school(school, refresh=refresh, cache=cache, delay=delay)
            results[school["short"]] = result
            if result.get("error"):
                fail_count += 1
            else:
                success_count += 1
        except Exception as e:
            print(f"  [异常] {e}")
            results[school["short"]] = {
                "fetched_at": datetime.now().isoformat(),
                "error": str(e),
            }
            fail_count += 1

    # 保存缓存
    cache["schools"] = results
    save_cache(cache)

    print(f"\n{'='*50}")
    print(f"抓取完成: {success_count} 成功, {fail_count} 失败")
    print(f"数据保存至: {INDEX_FILE}")

    return results


def print_summary(results, schools_config):
    """打印汇总"""
    all_schools = {s["short"]: s for s in schools_config.get("schools", [])}

    print(f"\n{'='*70}")
    print("📢 通知汇总")
    print(f"{'='*70}")

    total_notices = 0
    for short, result in results.items():
        school_info = all_schools.get(short, {})
        name = school_info.get("name", short)
        count = result.get("notice_count", len(result.get("notices", [])))
        error = result.get("error")
        total_notices += count

        status = "✅" if not error else "⚠️"
        print(f"\n{status} {name} ({short}) — {count} 条通知")
        if error:
            print(f"   错误: {error}")

        for notice in result.get("notices", [])[:3]:
            keywords = ", ".join(notice.get("matched_keywords", []))
            kw_str = f" [{keywords}]" if keywords else ""
            print(f"   📌 {notice['title'][:70]}{kw_str}")
            print(f"      {notice['url']}")

    print(f"\n{'='*70}")
    print(f"总计: {total_notices} 条通知，来自 {len(results)} 所学校")


def main():
    global INDEX_FILE, CONFIG_FILE

    parser = argparse.ArgumentParser(description="保研skill — 通知爬虫")
    parser.add_argument("--school", default="all",
                        help="学校简称，逗号分隔（如 '上交,浙大,华科'），或 'all' 抓取全部")
    parser.add_argument("--refresh", action="store_true",
                        help="强制刷新，忽略缓存")
    parser.add_argument("--output", default=None,
                        help="输出文件路径")
    parser.add_argument("--config", default=None,
                        help="配置文件路径")
    parser.add_argument("--summary-only", action="store_true",
                        help="仅显示缓存中的汇总（不抓取）")

    args = parser.parse_args()

    if args.output:
        INDEX_FILE = Path(args.output)
    if args.config:
        CONFIG_FILE = Path(args.config)

    config = load_config()

    if args.summary_only:
        cache = load_cache()
        print_summary(cache.get("schools", {}), config)
        return

    results = scrape_all(config, args.school, args.refresh)
    print_summary(results, config)


if __name__ == "__main__":
    main()
