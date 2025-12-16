import requests
from typing import Dict, List, Optional

CNINFO_HOST = "http://www.cninfo.com.cn"

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "X-Requested-With": "XMLHttpRequest",
    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
    "Origin": CNINFO_HOST,
    "Referer": f"{CNINFO_HOST}/new/commonUrl?url=disclosure/list/notice",
}

def cninfo_company_search(keyword: str, session: Optional[requests.Session] = None) -> List[Dict]:
    """
    公司检索接口：/new/information/topSearch/detailOfQuery
    返回候选列表（常见字段含 code, orgId, zwjc, category 等）
    """
    sess = session or requests.Session()
    url = f"{CNINFO_HOST}/new/information/topSearch/detailOfQuery"
    data = {"keyWord": keyword, "maxSecNum": 10, "maxListNum": 10}
    r = sess.post(url, headers=HEADERS, data=data, timeout=20)
    r.raise_for_status()
    payload = r.json()
    return payload.get("keyBoardList", []) or []

def pick_best_a_share(candidates: List[Dict], firm_name: str) -> Optional[Dict]:
    if not candidates:
        return None
    a = [c for c in candidates if str(c.get("category", "")).strip() == "A股"]
    pool = a if a else candidates

    def score(c):
        zwjc = str(c.get("zwjc", "")).strip()
        if zwjc == firm_name:
            return 3
        if firm_name in zwjc or zwjc in firm_name:
            return 2
        return 1

    pool.sort(key=score, reverse=True)
    return pool[0]

def build_stock_field(code: str, orgId: str) -> str:
    return f"{code},{orgId}"

def cninfo_query_announcements(
    stock: str,
    searchkey: str,
    seDate: str,
    pageNum: int = 1,
    pageSize: int = 30,
    column: str = "szse",
    tabName: str = "fulltext",
    category: str = "",
    session: Optional[requests.Session] = None,
) -> Dict:
    """
    公告列表接口：/new/hisAnnouncement/query
    stock 一般形如 "000001,gssz0000001"
    seDate 形如 "2021-01-01~2025-12-31"
    """
    sess = session or requests.Session()
    url = f"{CNINFO_HOST}/new/hisAnnouncement/query"
    data = {
        "pageNum": pageNum,
        "pageSize": pageSize,
        "column": column,
        "tabName": tabName,
        "plate": "",
        "stock": stock,
        "searchkey": searchkey,
        "secid": "",
        "category": category,
        "trade": "",
        "seDate": seDate,
        "sortName": "time",
        "sortType": "desc",
        "isHLtitle": "true",
    }
    r = sess.post(url, headers=HEADERS, data=data, timeout=30)
    r.raise_for_status()
    return r.json()
