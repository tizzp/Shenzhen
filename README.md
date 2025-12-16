# 深圳企业外迁：事件卡片自动抽取（cninfo 版本）

## 用途
- 从 cninfo 公告检索（上市公司）抽取“外迁相关”候选事件，并写入你提供的 Excel 模板：
  - Company_Master
  - Event_Cards
  - Evidence_Log

## 运行
```bash
pip install -r requirements.txt
python run_pipeline.py
```

## 输入
- seeds.csv：企业名称列表（建议先少量测试，确认网络与接口可用后再扩展）
- config.yaml：时间范围、关键词、限速与翻页参数

## 输出
- outputs/ 目录下生成带数据的 xlsx
