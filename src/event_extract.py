import re
from typing import Dict, Tuple, List

FUNC_RULES = {
    "MFG": [r"生产基地", r"工厂", r"产线", r"制造基地", r"投产", r"扩产", r"厂房", r"车间"],
    "RD":  [r"研发中心", r"研究院", r"实验室", r"创新中心", r"研发基地"],
    "OPS": [r"运营中心", r"区域总部", r"结算中心", r"销售中心", r"客服中心", r"总部"],
}

REASON_RULES = {
    "COST":   [r"成本", r"用工", r"租金", r"地价", r"能耗", r"税负"],
    "LAND":   [r"用地", r"供地", r"拿地", r"厂房紧缺", r"扩产空间", r"园区"],
    "ENV":    [r"环保", r"排放", r"环评", r"合规"],
    "SCM":    [r"供应链", r"配套", r"物流", r"港口", r"通关"],
    "MARKET": [r"客户", r"市场", r"订单", r"交付"],
    "TALENT": [r"人才", r"招聘", r"用工结构", r"工程师"],
    "POLICY": [r"补贴", r"优惠", r"招商", r"支持政策", r"专项资金", r"奖励"],
    "FIN":    [r"融资", r"资金", r"利率", r"财务费用"],
    "GEO":    [r"关税", r"出口管制", r"制裁", r"地缘", r"贸易摩擦", r"合规要求"],
    "STRATEGY":[r"战略", r"重组", r"并购", r"分拆", r"组织优化"],
}

def classify_functions(text: str) -> Tuple[str, Dict[str,int]]:
    flags = {"MFG":0,"RD":0,"OPS":0}
    for k, pats in FUNC_RULES.items():
        for p in pats:
            if re.search(p, text):
                flags[k] = 1
                break
    if sum(flags.values()) >= 2:
        return "MIX", flags
    for k in ["MFG","RD","OPS"]:
        if flags[k]:
            return k, flags
    return "UNK", flags

def classify_reasons(text: str) -> List[str]:
    found = []
    for code, pats in REASON_RULES.items():
        if any(re.search(p, text) for p in pats):
            found.append(code)
    found = found[:3]
    while len(found) < 3:
        found.append("")
    return found
