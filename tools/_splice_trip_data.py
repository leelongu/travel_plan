#!/usr/bin/env python3
"""Replace trip-data JSON in shanxi-7d-followtour.html with 7d group-tour data.

Usage:
  python3 tools/_splice_trip_data.py            # write top-level fields (days=[])
  python3 tools/_splice_trip_data.py days       # splice 7 days from tools/_days.json
"""
import json, re, sys
from pathlib import Path

HTML = Path('shanxi-7d-followtour.html')
DAYS_JSON_PATH = Path('tools/_days.json')

NEW_TOP_LEVEL = {
    "title": "山西晋北 7 日跟团游 · 开元心旅行",
    "startDate": "2026-09-25",
    "colorScheme": "由设计步骤决定（与现有山西橙黄调区分）",
    "preTrip": {
        "weather": {
            "summary": "9 月末 10 月初山西 8–22°C，昼夜温差 10°C+；五台山/大同夜间近 0°C",
            "typhoon": "无台风季；10 月寒潮可能降雪，五台山/恒山山顶可能封山"
        },
        "packing": "薄羽绒/冲锋衣（早晚）+ 卫衣（白天）+ 防水鞋 + 保温杯",
        "payment": "移动支付普及；景区刷身份证入场",
        "apps": ["开元心旅行小程序", "高德/百度地图", "山西文旅公众号"],
        "ticketTip": "热门景点提前 1 周官方公众号预约；跟团门票已含由导游统一购票"
    },
    "flights": {
        "booked": [],
        "candidates": [
            {
                "label": "自行往返太原·参考",
                "code": "广州—太原",
                "time": "示例：南航 CZ3377 广州 22:00 → 太原 00:30（实际以购票为准）",
                "note": "跟团不含大交通，建议提前 7–14 天自行预订往返机票/高铁"
            }
        ]
    },
    "hotelAreas": [
        {
            "area": "太原（集合日 + Day 6）",
            "reason": "亲贤街 / 南内环街五一广场；4 钻，地铁/餐饮便利",
            "options": [
                {
                    "tier": "4 钻（参考）",
                    "name": "太原亲贤街美居酒店 / 太原南内环街五一广场美居酒店",
                    "priceRange": "跟团含 2 晚（按团费）",
                    "note": "或同级 · 14:00 后入住"
                }
            ]
        },
        {
            "area": "五台山（Day 2）",
            "reason": "龙泉寺片区；山区酒店条件偏简陋",
            "options": [
                {
                    "tier": "特色住宿",
                    "name": "五台山一盏明灯·禅心殊院（龙泉寺店）/ 花卉山庄",
                    "priceRange": "跟团含 1 晚",
                    "note": "或同级 · 山上住宿周边营业商家较少，不适合补给"
                }
            ]
        },
        {
            "area": "大同（Day 3–4）",
            "reason": "永泰片区；靠近古城",
            "options": [
                {
                    "tier": "4 钻",
                    "name": "建国璞隐酒店旗舰店（大同永泰店）",
                    "priceRange": "跟团含 2 晚",
                    "note": "或同级 · 含早餐"
                }
            ]
        },
        {
            "area": "桐悦（Day 5，朔州/应县片区）",
            "reason": "桐悦臻选；县城住宿条件一般",
            "options": [
                {
                    "tier": "臻选",
                    "name": "桐悦臻选酒店",
                    "priceRange": "跟团含 1 晚",
                    "note": "或同级 · 县城服务意识较一般"
                }
            ]
        }
    ],
    "disclaimer": "本页行程信息来源于公众号「开元心旅行」发布的山西晋北 7 日跟团游产品（2026-08-29），所有信息（团期、价格、住宿、景点、餐饮、交通）均为参考，可能不准确或已过时；最终以旅行社小程序/客服确认为准。所有联网信息（天气、景点开放、门票政策）均为 AI 整理的参考建议，请务必在官方渠道核实后再做决定。",
    "dataSources": [
        {"name": "开元心旅行（公众号）", "scope": "团期/价格/行程/酒店/餐饮/景点门票", "realtime": False}
    ],
    "tips": [
        "跟团产品 18–55 周岁（可带娃陪同，限 79 周岁以下）",
        "9/25 团期单房差 1230 元/位（最后一晚房费 330 元/间）；单人报名默认接受拼房",
        "退损政策：集合日前 7 天以上无损；7–4 天收 50%；3–1 天收 80%；当天 100%",
        "儿童费用：小娃（1.2m 以下 / 6 岁以下）¥1090；中娃（1.2m 以上–12 岁）¥1780；大娃（12–18 岁）¥2790；每房免一名 12 岁以下儿童车位费",
        "塔院寺大白塔维修中，只能看局部",
        "悬空寺为安全考虑，跟团行程不登临",
        "国庆团期（10/1）人流大，应县木塔可能排队"
    ],
    "reminders": [
        {"item": "提前 7 天：提交航班/车次信息给客服（接机/站安排）", "leadDays": 7},
        {"item": "提前 3 天：确认团期/天气/着装清单", "leadDays": 3},
        {"item": "出发前 1 天：充电宝/身份证/保温杯/防水鞋", "leadDays": 1}
    ],
    "days": []
}


def write_top_level():
    src = HTML.read_text(encoding='utf-8')
    new_body = '\n  ' + json.dumps(NEW_TOP_LEVEL, ensure_ascii=False, indent=2) + '\n'
    replaced = re.sub(
        r'(<script id="trip-data" type="application/json">)([\s\S]*?)(</script>)',
        lambda mm: mm.group(1) + new_body + mm.group(3),
        src, count=1,
    )
    HTML.write_text(replaced, encoding='utf-8')
    print('OK · trip top-level fields updated; days=[]')


def splice_days():
    if not DAYS_JSON_PATH.exists():
        sys.exit(f'MISSING {DAYS_JSON_PATH} — write days JSON first (Task 3 step 2)')
    src = HTML.read_text(encoding='utf-8')
    m = re.search(r'(<script id="trip-data" type="application/json">)([\s\S]*?)(</script>)', src)
    trip = json.loads(m.group(2))
    trip['days'] = json.loads(DAYS_JSON_PATH.read_text(encoding='utf-8'))
    new_body = '\n  ' + json.dumps(trip, ensure_ascii=False, indent=2) + '\n'
    replaced = re.sub(
        r'(<script id="trip-data" type="application/json">)([\s\S]*?)(</script>)',
        lambda mm: mm.group(1) + new_body + mm.group(3),
        src, count=1,
    )
    HTML.write_text(replaced, encoding='utf-8')
    print(f'OK · {len(trip["days"])} days spliced')


if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == 'days':
        splice_days()
    else:
        write_top_level()
