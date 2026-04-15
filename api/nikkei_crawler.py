import requests
from bs4 import BeautifulSoup
import re
import json

# 헤더 설정 (브라우저 흉내)
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "ja,en-US;q=0.7,en;q=0.3",
    "Referer": "https://www.nikkei.com/",
}

def get_session():
    """쿠키 발급용 세션 생성"""
    session = requests.Session()
    session.headers.update(HEADERS)
    try:
        session.get("https://www.nikkei.com/", timeout=10)
    except:
        pass
    return session

def scrape_fund_data(session, fcode):
    """펀드 데이터 스크래핑"""
    url = f"https://www.nikkei.com/nkd/fund/?fcode={fcode}"
    
    resp = session.get(url, timeout=10)
    if resp.status_code in [403, 404]:
        return {"error": f"접근 차단 (Status: {resp.status_code}) 또는 코드 오류"}

    soup = BeautifulSoup(resp.text, "html.parser")

    # 1. 페이지 제목 (펀드명)
    fund_name = soup.find("span", itemprop="name")
    name = fund_name.get_text(strip=True) if fund_name else "Unknown"

    # 2. 기준가/가격 데이터 (가격 블록)
    # 니케이는 보통 .m-stockPrice 클래스 내부에 가격이 있음
    # 아니면 script 태그의 JSON 데이터에서 추출
    
    # HTML 내에서 JSON 찾기 (가장 정확)
    # var data = {...} 패턴 탐색
    scripts = soup.find_all("script")
    fund_data = {}
    
    for script in scripts:
        if script.string and fcode in script.string:
            # 숫자 패턴: 12,289 형태
            prices = re.findall(r'(\d{1,3}(?:,\d{3})+)', script.string)
            if prices:
                # 유효한 가격 데이터 (큰 숫자 위주)
                candidates = [p.replace(',', '') for p in prices if len(p.replace(',','')) >= 3]
                if candidates:
                    fund_data["raw_prices"] = candidates

    # 3. 메타 태그에서 추출 (가성비 높음)
    og_title = soup.find("meta", property="og:title")
    if og_title:
        fund_data["title"] = og_title.get("content", "")

    # 4. 텍스트 기반 파싱 (span 태그들의 텍스트 수집)
    # 12,289 같은 숫자를 가진 span 찾기
    price_spans = soup.find_all(string=re.compile(r"^\d{1,3}(?:,\d{3})+$"))
    fund_data["found_prices"] = [p.strip() for p in price_spans]

    # 5. 주요 정보 추출 시도
    # 전일비, 등락률 등
    dt_tags = soup.find_all("dt")
    dd_tags = soup.find_all("dd")
    
    # dt:dd 매핑
    info_map = {}
    for i, dt in enumerate(dt_tags):
        key = dt.get_text(strip=True)
        if i < len(dd_tags):
            val = dd_tags[i].get_text(strip=True)
            info_map[key] = val

    return {
        "fcode": fcode,
        "name": name,
        "prices": fund_data,
        "details": info_map if info_map else "Data hidden in JS or Paywall",
        "url": url
    }
