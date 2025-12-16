import time
import yaml
import pandas as pd
import requests
from datetime import datetime

from src.cninfo_search import cninfo_company_search, pick_best_a_share, build_stock_field, cninfo_query_announcements
from src.event_extract import classify_functions, classify_reasons
from src.write_template import write_to_template

def make_event_id(date_str: str, idx: int) -> str:
    y = (date_str or "2021")[:4]
    return f"SZOUT-{y}-{idx:06d}"

def main():
    cfg = yaml.safe_load(open("config.yaml","r",encoding="utf-8"))
    seDate = f"{cfg['years']['start']}~{cfg['years']['end']}"
    sleep_s = float(cfg["cninfo"]["sleep_seconds"])
    page_size = int(cfg["cninfo"]["page_size"])
    max_pages = int(cfg["cninfo"]["max_pages_per_firm"])

    seeds = pd.read_csv("seeds.csv", encoding="utf-8")
    seeds["企业名称"] = seeds["企业名称"].astype(str).str.strip()
    firm_list = seeds["企业名称"].dropna().unique().tolist()

    sess = requests.Session()
    events, evidences, companies = [], [], []
    event_idx = 0

    for firm in firm_list:
        try:
            cands = cninfo_company_search(firm, session=sess)
        except Exception as e:
            print("company_search failed:", firm, e)
            continue

        best = pick_best_a_share(cands, firm)
        if not best:
            continue

        code = str(best.get("code","")).strip()
        orgId = str(best.get("orgId","")).strip()
        secName = str(best.get("zwjc","")).strip() or firm
        stock_field = build_stock_field(code, orgId)

        companies.append({
            "Firm_ID（自定义）": f"{code}_{orgId}",
            "企业名称": secName,
            "是否上市(1/0/UNK)": 1,
            "上市代码": code,
        })

        ann_seen = set()
        for kw in cfg["keywords"]["core"]:
            for page in range(1, max_pages+1):
                try:
                    payload = cninfo_query_announcements(
                        stock=stock_field, searchkey=kw, seDate=seDate,
                        pageNum=page, pageSize=page_size, session=sess
                    )
                except Exception as e:
                    print("query failed:", secName, kw, page, e)
                    break

                anns = payload.get("announcements", []) or []
                if not anns:
                    break

                for a in anns:
                    aid = str(a.get("announcementId","")).strip()
                    if not aid or aid in ann_seen:
                        continue
                    ann_seen.add(aid)

                    title = str(a.get("announcementTitle","")).strip()
                    dt = ""
                    if a.get("announcementTime"):
                        dt = str(a.get("announcementTime"))[:10]

                    adjunct = str(a.get("adjunctUrl","")).strip()
                    url = f"http://static.cninfo.com.cn/{adjunct}" if adjunct else ""

                    text_for_classify = f"{title} {kw}"
                    func_code, flags = classify_functions(text_for_classify)
                    r1, r2, r3 = classify_reasons(text_for_classify)

                    event_idx += 1
                    event_id = make_event_id(dt or cfg['years']['start'], event_idx)

                    events.append({
                        "Event_ID（唯一）": event_id,
                        "Firm_ID（关联）": f"{code}_{orgId}",
                        "企业名称（冗余）": secName,
                        "事件年份(2021-2025)": (dt[:4] if dt else ""),
                        "事件日期（可空）": dt,
                        "外迁类型（法人/功能）": "功能",
                        "功能类型代码": func_code,
                        "是否多功能(1/0)": 1 if func_code == "MIX" else 0,
                        "制造外迁(1/0)": 1 if flags.get("MFG") else 0,
                        "研发外迁(1/0)": 1 if flags.get("RD") else 0,
                        "运营外迁(1/0)": 1 if flags.get("OPS") else 0,
                        "Reason_1": r1,
                        "Reason_2": r2,
                        "Reason_3": r3,
                        "证据强度(主)": "3-强",
                        "主证据链接/文件名": url,
                        "备注（含不确定性披露）": f"kw={kw}; announcementId={aid}"
                    })

                    evidences.append({
                        "Evidence_ID（唯一）": f"EVI-{event_id}-01",
                        "Event_ID（关联）": event_id,
                        "证据类型代码": "FIRM",
                        "证据强度(1-3)": "3-强",
                        "来源机构/媒体": "cninfo",
                        "标题/描述": title,
                        "发布日期": dt,
                        "链接/文件名": url,
                        "关键信息摘录（<=200字）": title[:200],
                        "是否支持制造(1/0)": 1 if flags.get("MFG") else 0,
                        "是否支持研发(1/0)": 1 if flags.get("RD") else 0,
                        "是否支持运营(1/0)": 1 if flags.get("OPS") else 0,
                        "备注": f"stock={code}; orgId={orgId}"
                    })

                time.sleep(sleep_s)

            time.sleep(sleep_s)

    event_df = pd.DataFrame(events)
    evidence_df = pd.DataFrame(evidences)
    company_df = pd.DataFrame(companies)

    out_path = f"outputs/深圳企业外迁_事件卡片_自动抽取_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    write_to_template(
        template_path="深圳企业外迁_事件卡片模板_v1.xlsx",
        out_path=out_path,
        event_df=event_df,
        evidence_df=evidence_df,
        company_df=company_df
    )
    print("Done:", out_path, "events=", len(event_df), "evidence=", len(evidence_df))

if __name__ == "__main__":
    main()
