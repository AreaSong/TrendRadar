# coding=utf-8
"""
报告生成模块

提供报告数据准备和 HTML 生成功能：
- prepare_report_data: 准备报告数据
- generate_html_report: 生成 HTML 报告
"""

from pathlib import Path
from typing import Dict, List, Optional, Callable


def prepare_report_data(
    stats: List[Dict],
    failed_ids: Optional[List] = None,
    new_titles: Optional[Dict] = None,
    id_to_name: Optional[Dict] = None,
    mode: str = "daily",
    rank_threshold: int = 3,
    matches_word_groups_func: Optional[Callable] = None,
    load_frequency_words_func: Optional[Callable] = None,
    show_new_section: bool = True,
) -> Dict:
    """
    准备报告数据

    Args:
        stats: 统计结果列表
        failed_ids: 失败的 ID 列表
        new_titles: 新增标题
        id_to_name: ID 到名称的映射
        mode: 报告模式 (daily/incremental/current)
        rank_threshold: 排名阈值
        matches_word_groups_func: 词组匹配函数
        load_frequency_words_func: 加载频率词函数
        show_new_section: 是否显示新增热点区域

    Returns:
        Dict: 准备好的报告数据
    """
    processed_new_titles = []

    # 在增量模式下或配置关闭时隐藏新增新闻区域
    hide_new_section = mode == "incremental" or not show_new_section

    # 只有在非隐藏模式下才处理新增新闻部分
    if not hide_new_section:
        filtered_new_titles = {}
        if new_titles and id_to_name:
            # 如果提供了匹配函数，使用它过滤
            if matches_word_groups_func and load_frequency_words_func:
                word_groups, filter_words, global_filters = load_frequency_words_func()
                for source_id, titles_data in new_titles.items():
                    filtered_titles = {}
                    for title, title_data in titles_data.items():
                        if matches_word_groups_func(title, word_groups, filter_words, global_filters):
                            filtered_titles[title] = title_data
                    if filtered_titles:
                        filtered_new_titles[source_id] = filtered_titles
            else:
                # 没有匹配函数时，使用全部
                filtered_new_titles = new_titles

            # 打印过滤后的新增热点数（与推送显示一致）
            original_new_count = sum(len(titles) for titles in new_titles.values()) if new_titles else 0
            filtered_new_count = sum(len(titles) for titles in filtered_new_titles.values()) if filtered_new_titles else 0
            if original_new_count > 0:
                print(f"频率词过滤后：{filtered_new_count} 条新增热点匹配（原始 {original_new_count} 条）")

        if filtered_new_titles and id_to_name:
            for source_id, titles_data in filtered_new_titles.items():
                source_name = id_to_name.get(source_id, source_id)
                source_titles = []

                for title, title_data in titles_data.items():
                    url = title_data.get("url", "")
                    mobile_url = title_data.get("mobileUrl", "")
                    ranks = title_data.get("ranks", [])

                    processed_title = {
                        "title": title,
                        "source_name": source_name,
                        "time_display": "",
                        "count": 1,
                        "ranks": ranks,
                        "rank_threshold": rank_threshold,
                        "url": url,
                        "mobile_url": mobile_url,
                        "is_new": True,
                    }
                    source_titles.append(processed_title)

                if source_titles:
                    processed_new_titles.append(
                        {
                            "source_id": source_id,
                            "source_name": source_name,
                            "titles": source_titles,
                        }
                    )

    processed_stats = []
    for stat in stats:
        if stat["count"] <= 0:
            continue

        processed_titles = []
        for title_data in stat["titles"]:
            processed_title = {
                "title": title_data["title"],
                "source_name": title_data["source_name"],
                "time_display": title_data["time_display"],
                "count": title_data["count"],
                "ranks": title_data["ranks"],
                "rank_threshold": title_data["rank_threshold"],
                "url": title_data.get("url", ""),
                "mobile_url": title_data.get("mobileUrl", ""),
                "is_new": title_data.get("is_new", False),
            }
            processed_titles.append(processed_title)

        processed_stats.append(
            {
                "word": stat["word"],
                "count": stat["count"],
                "percentage": stat.get("percentage", 0),
                "titles": processed_titles,
            }
        )

    return {
        "stats": processed_stats,
        "new_titles": processed_new_titles,
        "failed_ids": failed_ids or [],
        "total_new_count": sum(
            len(source["titles"]) for source in processed_new_titles
        ),
    }


def generate_html_report(
    stats: List[Dict],
    total_titles: int,
    failed_ids: Optional[List] = None,
    new_titles: Optional[Dict] = None,
    id_to_name: Optional[Dict] = None,
    mode: str = "daily",
    update_info: Optional[Dict] = None,
    rank_threshold: int = 3,
    output_dir: str = "output",
    date_folder: str = "",
    time_filename: str = "",
    render_html_func: Optional[Callable] = None,
    matches_word_groups_func: Optional[Callable] = None,
    load_frequency_words_func: Optional[Callable] = None,
) -> str:
    """
    生成 HTML 报告

    每次生成 HTML 后会：
    1. 保存时间戳快照到 output/html/日期/时间.html（历史记录）
    2. 复制到 output/html/latest/{mode}.html（最新报告）
    3. 复制到 output/index.html 和根目录 index.html（入口）

    Args:
        stats: 统计结果列表
        total_titles: 总标题数
        failed_ids: 失败的 ID 列表
        new_titles: 新增标题
        id_to_name: ID 到名称的映射
        mode: 报告模式 (daily/incremental/current)
        update_info: 更新信息
        rank_threshold: 排名阈值
        output_dir: 输出目录
        date_folder: 日期文件夹名称
        time_filename: 时间文件名
        render_html_func: HTML 渲染函数
        matches_word_groups_func: 词组匹配函数
        load_frequency_words_func: 加载频率词函数

    Returns:
        str: 生成的 HTML 文件路径（时间戳快照路径）
    """
    # 时间戳快照文件名
    snapshot_filename = f"{time_filename}.html"

    # 构建输出路径（扁平化结构：output/html/日期/）
    snapshot_path = Path(output_dir) / "html" / date_folder
    snapshot_path.mkdir(parents=True, exist_ok=True)
    snapshot_file = str(snapshot_path / snapshot_filename)

    # 准备报告数据
    report_data = prepare_report_data(
        stats,
        failed_ids,
        new_titles,
        id_to_name,
        mode,
        rank_threshold,
        matches_word_groups_func,
        load_frequency_words_func,
    )

    # 渲染 HTML 内容
    if render_html_func:
        html_content = render_html_func(
            report_data, total_titles, mode, update_info
        )
    else:
        # 默认简单 HTML
        html_content = f"<html><body><h1>Report</h1><pre>{report_data}</pre></body></html>"

    # 1. 保存时间戳快照（历史记录）
    with open(snapshot_file, "w", encoding="utf-8") as f:
        f.write(html_content)

    # 2. 复制到 html/latest/{mode}.html（最新报告）
    latest_dir = Path(output_dir) / "html" / "latest"
    latest_dir.mkdir(parents=True, exist_ok=True)
    latest_file = latest_dir / f"{mode}.html"
    with open(latest_file, "w", encoding="utf-8") as f:
        f.write(html_content)

    # 3. 复制到 index.html（入口）
    # output/index.html（供 Docker Volume 挂载访问）
    output_index = Path(output_dir) / "index.html"
    with open(output_index, "w", encoding="utf-8") as f:
        f.write(html_content)

    # 根目录 index.html（供 GitHub Pages 访问）
    root_index = Path("index.html")
    with open(root_index, "w", encoding="utf-8") as f:
        f.write(html_content)

    return snapshot_file


def generate_dashboard(
    stats: List[Dict],
    total_titles: int,
    output_dir: str = "output",
    refresh_interval: int = 300,
) -> str:
    """
    生成实时仪表盘页面
    
    Args:
        stats: 统计结果列表
        total_titles: 总标题数
        output_dir: 输出目录
        refresh_interval: 自动刷新间隔（秒），默认 300 秒
        
    Returns:
        str: 生成的仪表盘文件路径
    """
    import json
    from datetime import datetime
    
    # 计算统计数据
    platform_counts = {}
    keyword_counts = []
    hot_news_list = []
    
    if stats:
        for stat in stats:
            keyword_counts.append({
                "word": stat["word"],
                "count": stat["count"]
            })
            for title_data in stat["titles"]:
                platform = title_data.get("source_name", "未知")
                platform_counts[platform] = platform_counts.get(platform, 0) + 1
                hot_news_list.append({
                    "title": title_data.get("title", ""),
                    "source": platform,
                    "keyword": stat["word"],
                    "count": title_data.get("count", 1),
                    "url": title_data.get("url", "")
                })
    
    # 取 TOP 数据
    keyword_counts = keyword_counts[:10]
    hot_news_list = hot_news_list[:50]
    
    # 统计数据
    total_news = sum(len(stat["titles"]) for stat in stats) if stats else 0
    total_keywords = len(stats) if stats else 0
    total_platforms = len(platform_counts)
    
    # 生成 HTML
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    html_content = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta http-equiv="refresh" content="{refresh_interval}">
    <title>TrendRadar 实时仪表盘</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script>
    <style>
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }}
        .dashboard {{
            max-width: 1400px;
            margin: 0 auto;
        }}
        .header {{
            text-align: center;
            color: white;
            padding: 30px 0;
        }}
        .header h1 {{
            font-size: 32px;
            margin-bottom: 10px;
        }}
        .header .update-time {{
            opacity: 0.9;
            font-size: 14px;
        }}
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 20px;
            margin-bottom: 20px;
        }}
        .stat-card {{
            background: white;
            border-radius: 16px;
            padding: 24px;
            text-align: center;
            box-shadow: 0 4px 20px rgba(0,0,0,0.1);
        }}
        .stat-card .value {{
            font-size: 36px;
            font-weight: 700;
            color: #4f46e5;
        }}
        .stat-card .label {{
            font-size: 14px;
            color: #6b7280;
            margin-top: 8px;
        }}
        .charts-grid {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
            margin-bottom: 20px;
        }}
        .chart-card {{
            background: white;
            border-radius: 16px;
            padding: 24px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.1);
        }}
        .chart-card h3 {{
            font-size: 16px;
            color: #374151;
            margin-bottom: 16px;
        }}
        .chart-wrapper {{
            height: 300px;
            position: relative;
        }}
        .news-section {{
            background: white;
            border-radius: 16px;
            padding: 24px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.1);
        }}
        .news-section h3 {{
            font-size: 18px;
            color: #374151;
            margin-bottom: 16px;
            display: flex;
            align-items: center;
            gap: 8px;
        }}
        .news-list {{
            max-height: 400px;
            overflow-y: auto;
        }}
        .news-item {{
            display: flex;
            align-items: flex-start;
            padding: 12px 0;
            border-bottom: 1px solid #f3f4f6;
        }}
        .news-item:last-child {{
            border-bottom: none;
        }}
        .news-index {{
            width: 28px;
            height: 28px;
            background: #4f46e5;
            color: white;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 12px;
            font-weight: 600;
            flex-shrink: 0;
            margin-right: 12px;
        }}
        .news-index.hot {{
            background: #ef4444;
        }}
        .news-content {{
            flex: 1;
        }}
        .news-title {{
            font-size: 14px;
            color: #1f2937;
            line-height: 1.5;
            margin-bottom: 4px;
        }}
        .news-title a {{
            color: inherit;
            text-decoration: none;
        }}
        .news-title a:hover {{
            color: #4f46e5;
        }}
        .news-meta {{
            display: flex;
            gap: 12px;
            font-size: 12px;
            color: #9ca3af;
        }}
        .news-meta .keyword {{
            color: #4f46e5;
            background: #eef2ff;
            padding: 2px 8px;
            border-radius: 4px;
        }}
        .refresh-indicator {{
            position: fixed;
            bottom: 20px;
            right: 20px;
            background: white;
            padding: 12px 20px;
            border-radius: 24px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            font-size: 13px;
            color: #6b7280;
        }}
        @media (max-width: 768px) {{
            .stats-grid {{
                grid-template-columns: repeat(2, 1fr);
            }}
            .charts-grid {{
                grid-template-columns: 1fr;
            }}
        }}
    </style>
</head>
<body>
    <div class="dashboard">
        <div class="header">
            <h1>📊 TrendRadar 实时仪表盘</h1>
            <div class="update-time">最后更新: {current_time} | 每 {refresh_interval // 60} 分钟自动刷新</div>
        </div>
        
        <div class="stats-grid">
            <div class="stat-card">
                <div class="value">{total_news}</div>
                <div class="label">新闻总数</div>
            </div>
            <div class="stat-card">
                <div class="value">{total_keywords}</div>
                <div class="label">关键词组</div>
            </div>
            <div class="stat-card">
                <div class="value">{total_platforms}</div>
                <div class="label">数据平台</div>
            </div>
            <div class="stat-card">
                <div class="value">{len(hot_news_list)}</div>
                <div class="label">热点话题</div>
            </div>
        </div>
        
        <div class="charts-grid">
            <div class="chart-card">
                <h3>📈 平台分布</h3>
                <div class="chart-wrapper">
                    <canvas id="platformChart"></canvas>
                </div>
            </div>
            <div class="chart-card">
                <h3>🔥 热词 TOP 10</h3>
                <div class="chart-wrapper">
                    <canvas id="keywordChart"></canvas>
                </div>
            </div>
        </div>
        
        <div class="news-section">
            <h3>📰 实时热点</h3>
            <div class="news-list">
'''
    
    # 添加热点新闻列表
    for i, news in enumerate(hot_news_list, 1):
        hot_class = "hot" if i <= 3 else ""
        title = news["title"]
        url = news.get("url", "")
        if url:
            title_html = f'<a href="{url}" target="_blank">{title}</a>'
        else:
            title_html = title
        
        html_content += f'''                <div class="news-item">
                    <div class="news-index {hot_class}">{i}</div>
                    <div class="news-content">
                        <div class="news-title">{title_html}</div>
                        <div class="news-meta">
                            <span class="source">{news["source"]}</span>
                            <span class="keyword">{news["keyword"]}</span>
                            <span>热度: {news["count"]}</span>
                        </div>
                    </div>
                </div>
'''
    
    html_content += f'''            </div>
        </div>
    </div>
    
    <div class="refresh-indicator">
        🔄 下次刷新: <span id="countdown">{refresh_interval}</span> 秒
    </div>
    
    <script>
        // 图表数据
        const platformData = {json.dumps(platform_counts, ensure_ascii=False)};
        const keywordData = {json.dumps(keyword_counts, ensure_ascii=False)};
        
        // 颜色生成
        function generateColors(count) {{
            const colors = ['#4f46e5', '#7c3aed', '#ec4899', '#f43f5e', '#f97316',
                           '#eab308', '#22c55e', '#14b8a6', '#06b6d4', '#3b82f6'];
            return colors.slice(0, count);
        }}
        
        // 平台分布饼图
        const platformCtx = document.getElementById('platformChart');
        if (platformCtx && Object.keys(platformData).length > 0) {{
            new Chart(platformCtx, {{
                type: 'doughnut',
                data: {{
                    labels: Object.keys(platformData),
                    datasets: [{{
                        data: Object.values(platformData),
                        backgroundColor: generateColors(Object.keys(platformData).length)
                    }}]
                }},
                options: {{
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {{
                        legend: {{ position: 'right', labels: {{ boxWidth: 12, padding: 8 }} }}
                    }}
                }}
            }});
        }} else if (platformCtx) {{
            platformCtx.parentElement.innerHTML = '<div style="display:flex;align-items:center;justify-content:center;height:100%;color:#9ca3af;">暂无数据</div>';
        }}
        
        // 关键词柱状图
        const keywordCtx = document.getElementById('keywordChart');
        if (keywordCtx && keywordData.length > 0) {{
            new Chart(keywordCtx, {{
                type: 'bar',
                data: {{
                    labels: keywordData.map(k => k.word.length > 8 ? k.word.substring(0, 8) + '...' : k.word),
                    datasets: [{{
                        label: '热度',
                        data: keywordData.map(k => k.count),
                        backgroundColor: '#4f46e5',
                        borderRadius: 4
                    }}]
                }},
                options: {{
                    responsive: true,
                    maintainAspectRatio: false,
                    indexAxis: 'y',
                    plugins: {{ legend: {{ display: false }} }},
                    scales: {{
                        x: {{ grid: {{ display: false }} }},
                        y: {{ grid: {{ display: false }} }}
                    }}
                }}
            }});
        }} else if (keywordCtx) {{
            keywordCtx.parentElement.innerHTML = '<div style="display:flex;align-items:center;justify-content:center;height:100%;color:#9ca3af;">暂无数据</div>';
        }}
        
        // 倒计时
        let countdown = {refresh_interval};
        setInterval(() => {{
            countdown--;
            if (countdown <= 0) countdown = {refresh_interval};
            document.getElementById('countdown').textContent = countdown;
        }}, 1000);
    </script>
</body>
</html>'''
    
    # 保存仪表盘文件
    dashboard_path = Path(output_dir) / "dashboard.html"
    dashboard_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(dashboard_path, "w", encoding="utf-8") as f:
        f.write(html_content)
    
    return str(dashboard_path)
