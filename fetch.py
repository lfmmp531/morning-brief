#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""先生的晨报：持仓/观察标的行情 + 关键消息。数据源：新浪为主，GoogleNews(RSS)为辅。"""
import json, urllib.request, urllib.parse, datetime, xml.etree.ElementTree as ET, os

UA = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36'}

def get(url, headers=None, timeout=12):
    h = dict(UA)
    if headers: h.update(headers)
    req = urllib.request.Request(url, headers=h)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read().decode('gbk', 'ignore')

def sina(symbols):
    """新浪行情，返回 {code: (name, price, chg_pct)}; 指数格式 名称,点位,涨跌,涨跌幅; A股 名称,开,昨收,现价,..."""
    out = {}
    try:
        txt = get('https://hq.sinajs.cn/list=' + ','.join(symbols), headers={'Referer': 'https://finance.sina.com.cn'})
        for line in txt.strip().splitlines():
            if '"' not in line: continue
            code = line.split('=')[0].replace('var hq_str_', '').strip()
            d = line.split('"')[1].split(',')
            if not d or not d[0]: continue
            try:
                if code.startswith('int_'):
                    name, price, chg, pct = d[0], float(d[1]), float(d[2]), float(d[3])
                else:
                    name = d[0]
                    if len(d) > 3 and d[2] and d[3]:
                        price = float(d[3]); prev = float(d[2])
                        pct = (price - prev) / prev * 100 if prev else 0.0
                    else:
                        continue
                out[code] = (name, round(price, 2), round(pct, 2))
            except (ValueError, IndexError):
                continue
    except Exception:
        pass
    return out

def news_google(q, num=4):
    try:
        url = 'https://news.google.com/rss/search?q=' + urllib.parse.quote(q) + '&hl=zh-CN&gl=CN&ceid=CN:zh-Hans'
        req = urllib.request.Request(url, headers=UA)
        root = ET.fromstring(urllib.request.urlopen(req, timeout=12).read().decode('utf-8', 'ignore'))
        out = []
        for it in root.findall('.//item')[:num]:
            t = (it.findtext('title') or '').strip()
            pub = (it.findtext('pubDate') or '')[:16]
            if t: out.append(f'- {t}  ({pub})')
        return out
    except Exception:
        return []

def stooq_tnx():
    """美债10Y收益率，失败返回空"""
    try:
        url = 'https://stooq.com/q/d/l/?s=' + urllib.parse.quote('^tnx') + '&i=d&d1=20250101&d2=20261231'
        req = urllib.request.Request(url, headers=UA)
        txt = urllib.request.urlopen(req, timeout=10).read().decode('utf-8', 'ignore')
        rows = [l for l in txt.strip().splitlines() if l]
        if len(rows) >= 2:
            return rows[-1].split(',')[-1]
    except Exception:
        return None
    return None

def main():
    lines = []
    now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M')

    # ---- 行情 ----
    lines.append('## 📊 行情速览')
    quotes = sina(['int_sp500', 'int_nasdaq', 'int_dji', 'sh000300', 'sh512170', 'sz159611'])
    labels = {
        'int_sp500': '标普500', 'int_nasdaq': '纳斯达克', 'int_dji': '道琼斯',
        'sh000300': '沪深300', 'sh512170': '医疗ETF', 'sz159611': '电力ETF',
    }
    for code, label in labels.items():
        if code in quotes:
            n, p, c = quotes[code]
            lines.append(f'- **{label}** {p} ({c:+.2f}%)')
    tnx = stooq_tnx()
    if tnx: lines.append(f'- **美债10Y** {tnx}%')
    lines.append('')

    # ---- 消息 ----
    lines.append('## 📰 关键消息')
    for kw, tag in [('沪深300 OR A股', 'A股'), ('医疗ETF OR 创新药 OR 集采', '医疗'), ('标普500 OR 美联储', '美股'), ('AI 芯片 OR 英伟达', 'AI'), ('电力 板块 OR 电力改革', '电力')]:
        items = news_google(kw, 4)
        lines.append(f'### {tag}')
        lines.extend(items if items else ['- (暂无)'])
        lines.append('')

    lines.append('## ✍️ 先生的初步分析')
    lines.append('（先生早上亲自补写）')

    body = f'# 🌅 先生的晨报 · {now}\n\n' + '\n'.join(lines) + '\n'
    os.makedirs('reports', exist_ok=True)
    fname = f'reports/{datetime.date.today().isoformat()}.md'
    with open(fname, 'w', encoding='utf-8') as f:
        f.write(body)
    print('OK ->', fname)


if __name__ == '__main__':
    main()
