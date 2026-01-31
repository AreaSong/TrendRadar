# coding=utf-8
"""
HTML 报告渲染模块

提供 HTML 格式的热点新闻报告生成功能
"""

from datetime import datetime
from typing import Any, Dict, List, Optional, Callable

from trendradar.report.helpers import html_escape
from trendradar.utils.time import convert_time_for_display
from trendradar.ai.formatter import render_ai_analysis_html_rich


def render_html_content(
    report_data: Dict,
    total_titles: int,
    mode: str = "daily",
    update_info: Optional[Dict] = None,
    *,
    region_order: Optional[List[str]] = None,
    get_time_func: Optional[Callable[[], datetime]] = None,
    rss_items: Optional[List[Dict]] = None,
    rss_new_items: Optional[List[Dict]] = None,
    display_mode: str = "keyword",
    standalone_data: Optional[Dict] = None,
    ai_analysis: Optional[Any] = None,
    show_new_section: bool = True,
) -> str:
    """渲染HTML内容

    Args:
        report_data: 报告数据字典，包含 stats, new_titles, failed_ids, total_new_count
        total_titles: 新闻总数
        mode: 报告模式 ("daily", "current", "incremental")
        update_info: 更新信息（可选）
        region_order: 区域显示顺序列表
        get_time_func: 获取当前时间的函数（可选，默认使用 datetime.now）
        rss_items: RSS 统计条目列表（可选）
        rss_new_items: RSS 新增条目列表（可选）
        display_mode: 显示模式 ("keyword"=按关键词分组, "platform"=按平台分组)
        standalone_data: 独立展示区数据（可选），包含 platforms 和 rss_feeds
        ai_analysis: AI 分析结果对象（可选），AIAnalysisResult 实例
        show_new_section: 是否显示新增热点区域

    Returns:
        渲染后的 HTML 字符串
    """
    # 默认区域顺序
    default_region_order = ["hotlist", "rss", "new_items", "standalone", "ai_analysis"]
    if region_order is None:
        region_order = default_region_order

    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>热点新闻分析</title>
        <script src="https://cdnjs.cloudflare.com/ajax/libs/html2canvas/1.4.1/html2canvas.min.js" integrity="sha512-BNaRQnYJYiPSqHHDb58B0yaPfCu+Wgds8Gp/gU33kqBtgNS4tSPHuGibyoeqMV/TJlSKda6FXzoEyYGjTe+vXA==" crossorigin="anonymous" referrerpolicy="no-referrer"></script>
        <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script>
        <style>
            * { box-sizing: border-box; }
            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif;
                margin: 0;
                padding: 16px;
                background: #fafafa;
                color: #333;
                line-height: 1.5;
            }

            .container {
                max-width: 600px;
                margin: 0 auto;
                background: white;
                border-radius: 12px;
                overflow: hidden;
                box-shadow: 0 2px 16px rgba(0,0,0,0.06);
            }

            .header {
                background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%);
                color: white;
                padding: 32px 24px;
                text-align: center;
                position: relative;
            }

            .save-buttons {
                position: absolute;
                top: 16px;
                right: 16px;
                display: flex;
                gap: 8px;
            }

            .save-btn {
                background: rgba(255, 255, 255, 0.2);
                border: 1px solid rgba(255, 255, 255, 0.3);
                color: white;
                padding: 8px 16px;
                border-radius: 6px;
                cursor: pointer;
                font-size: 13px;
                font-weight: 500;
                transition: all 0.2s ease;
                backdrop-filter: blur(10px);
                white-space: nowrap;
            }

            .save-btn:hover {
                background: rgba(255, 255, 255, 0.3);
                border-color: rgba(255, 255, 255, 0.5);
                transform: translateY(-1px);
            }

            .save-btn:active {
                transform: translateY(0);
            }

            .save-btn:disabled {
                opacity: 0.6;
                cursor: not-allowed;
            }

            /* 工具栏样式 */
            .toolbar {
                display: flex;
                align-items: center;
                gap: 12px;
                padding: 12px 24px;
                background: #f8f9fa;
                border-bottom: 1px solid #e5e7eb;
            }

            .search-box {
                flex: 1;
                position: relative;
            }

            .search-input {
                width: 100%;
                padding: 10px 16px 10px 40px;
                border: 1px solid #e5e7eb;
                border-radius: 8px;
                font-size: 14px;
                background: white;
                transition: all 0.2s ease;
            }

            .search-input:focus {
                outline: none;
                border-color: #4f46e5;
                box-shadow: 0 0 0 3px rgba(79, 70, 229, 0.1);
            }

            .search-icon {
                position: absolute;
                left: 12px;
                top: 50%;
                transform: translateY(-50%);
                color: #9ca3af;
                font-size: 16px;
            }

            .toolbar-btn {
                padding: 10px 16px;
                border: 1px solid #e5e7eb;
                border-radius: 8px;
                background: white;
                cursor: pointer;
                font-size: 14px;
                font-weight: 500;
                color: #374151;
                transition: all 0.2s ease;
                display: flex;
                align-items: center;
                gap: 6px;
                white-space: nowrap;
            }

            .toolbar-btn:hover {
                background: #f3f4f6;
                border-color: #d1d5db;
            }

            .toolbar-btn.active {
                background: #4f46e5;
                color: white;
                border-color: #4f46e5;
            }

            .search-stats {
                font-size: 12px;
                color: #6b7280;
                padding: 8px 24px;
                background: #fef3cd;
                border-bottom: 1px solid #ffc107;
                display: none;
            }

            .search-stats.visible {
                display: block;
            }

            /* 折叠功能样式 */
            .word-header {
                cursor: pointer;
                user-select: none;
            }

            .word-header .collapse-icon {
                transition: transform 0.2s ease;
                margin-left: 8px;
                color: #9ca3af;
            }

            .word-group.collapsed .collapse-icon {
                transform: rotate(-90deg);
            }

            .word-group.collapsed .news-item {
                display: none;
            }

            /* 暗色模式样式 */
            body.dark-mode {
                background: #1a1a2e;
                color: #e5e7eb;
            }

            body.dark-mode .container {
                background: #16213e;
                box-shadow: 0 2px 16px rgba(0,0,0,0.3);
            }

            body.dark-mode .toolbar {
                background: #0f3460;
                border-color: #1a1a2e;
            }

            body.dark-mode .search-input {
                background: #16213e;
                border-color: #1a1a2e;
                color: #e5e7eb;
            }

            body.dark-mode .search-input:focus {
                border-color: #7c3aed;
            }

            body.dark-mode .toolbar-btn {
                background: #16213e;
                border-color: #1a1a2e;
                color: #e5e7eb;
            }

            body.dark-mode .toolbar-btn:hover {
                background: #0f3460;
            }

            body.dark-mode .content {
                background: #16213e;
            }

            body.dark-mode .word-name,
            body.dark-mode .news-title,
            body.dark-mode .new-item-title {
                color: #e5e7eb;
            }

            body.dark-mode .word-header {
                border-color: #1a1a2e;
            }

            body.dark-mode .news-item {
                border-color: #1a1a2e;
            }

            body.dark-mode .news-number,
            body.dark-mode .new-item-number {
                background: #0f3460;
                color: #9ca3af;
            }

            body.dark-mode .source-name,
            body.dark-mode .time-info,
            body.dark-mode .word-count,
            body.dark-mode .word-index {
                color: #9ca3af;
            }

            body.dark-mode .news-link {
                color: #818cf8;
            }

            body.dark-mode .news-link:visited {
                color: #a78bfa;
            }

            body.dark-mode .footer {
                background: #0f3460;
                border-color: #1a1a2e;
            }

            body.dark-mode .footer-content {
                color: #9ca3af;
            }

            body.dark-mode .footer-link {
                color: #818cf8;
            }

            body.dark-mode .rss-item {
                background: #0f3460;
                border-color: #10b981;
            }

            body.dark-mode .rss-link {
                color: #e5e7eb;
            }

            body.dark-mode .ai-section {
                background: linear-gradient(135deg, #1e3a5f 0%, #0f3460 100%);
                border-color: #1a1a2e;
            }

            body.dark-mode .ai-block {
                background: #16213e;
            }

            body.dark-mode .ai-block-content {
                color: #e5e7eb;
            }

            body.dark-mode .search-stats {
                background: #0f3460;
                border-color: #1a1a2e;
                color: #e5e7eb;
            }

            /* 高亮搜索匹配 */
            .search-highlight {
                background: #fef08a;
                padding: 1px 2px;
                border-radius: 2px;
            }

            body.dark-mode .search-highlight {
                background: #854d0e;
                color: #fef08a;
            }

            .hidden-by-search {
                display: none !important;
            }

            /* 自动刷新样式 */
            .refresh-countdown {
                font-size: 12px;
                color: #059669;
                padding: 6px 24px;
                background: #ecfdf5;
                border-bottom: 1px solid #10b981;
                text-align: center;
            }

            .refresh-countdown.hidden {
                display: none;
            }

            body.dark-mode .refresh-countdown {
                background: #064e3b;
                border-color: #10b981;
                color: #34d399;
            }

            .toolbar-btn.auto-refresh-active {
                background: #059669;
                color: white;
                border-color: #059669;
            }

            .toolbar-btn.auto-refresh-active:hover {
                background: #047857;
            }

            /* AI 对话窗口样式 */
            .chat-fab {
                position: fixed;
                bottom: 24px;
                right: 24px;
                width: 56px;
                height: 56px;
                border-radius: 50%;
                background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%);
                color: white;
                border: none;
                cursor: pointer;
                box-shadow: 0 4px 16px rgba(79, 70, 229, 0.4);
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 24px;
                z-index: 1000;
                transition: all 0.3s ease;
            }

            .chat-fab:hover {
                transform: scale(1.1);
                box-shadow: 0 6px 24px rgba(79, 70, 229, 0.5);
            }

            .chat-fab.has-unread::after {
                content: '';
                position: absolute;
                top: 0;
                right: 0;
                width: 12px;
                height: 12px;
                background: #ef4444;
                border-radius: 50%;
                border: 2px solid white;
            }

            .chat-window {
                position: fixed;
                bottom: 96px;
                right: 24px;
                width: 400px;
                height: 500px;
                background: white;
                border-radius: 16px;
                box-shadow: 0 8px 32px rgba(0,0,0,0.15);
                display: none;
                flex-direction: column;
                z-index: 1001;
                overflow: hidden;
            }

            .chat-window.open {
                display: flex;
                animation: slideUp 0.3s ease;
            }

            @keyframes slideUp {
                from {
                    opacity: 0;
                    transform: translateY(20px);
                }
                to {
                    opacity: 1;
                    transform: translateY(0);
                }
            }

            .chat-header {
                padding: 16px;
                background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%);
                color: white;
                display: flex;
                align-items: center;
                justify-content: space-between;
            }

            .chat-header-title {
                font-weight: 600;
                font-size: 16px;
                display: flex;
                align-items: center;
                gap: 8px;
            }

            .chat-header-actions {
                display: flex;
                gap: 8px;
            }

            .chat-header-btn {
                background: rgba(255,255,255,0.2);
                border: none;
                color: white;
                width: 32px;
                height: 32px;
                border-radius: 8px;
                cursor: pointer;
                display: flex;
                align-items: center;
                justify-content: center;
                transition: background 0.2s;
            }

            .chat-header-btn:hover {
                background: rgba(255,255,255,0.3);
            }

            .chat-messages {
                flex: 1;
                overflow-y: auto;
                padding: 16px;
                display: flex;
                flex-direction: column;
                gap: 12px;
            }

            .chat-message {
                max-width: 85%;
                padding: 12px 16px;
                border-radius: 16px;
                font-size: 14px;
                line-height: 1.5;
            }

            .chat-message.user {
                align-self: flex-end;
                background: #4f46e5;
                color: white;
                border-bottom-right-radius: 4px;
            }

            .chat-message.assistant {
                align-self: flex-start;
                background: #f3f4f6;
                color: #1f2937;
                border-bottom-left-radius: 4px;
            }

            .chat-message.system {
                align-self: center;
                background: #fef3c7;
                color: #92400e;
                font-size: 12px;
                padding: 8px 12px;
            }

            .chat-message.loading {
                display: flex;
                gap: 4px;
            }

            .chat-message.loading span {
                width: 8px;
                height: 8px;
                background: #9ca3af;
                border-radius: 50%;
                animation: bounce 1.4s infinite ease-in-out both;
            }

            .chat-message.loading span:nth-child(1) { animation-delay: -0.32s; }
            .chat-message.loading span:nth-child(2) { animation-delay: -0.16s; }

            @keyframes bounce {
                0%, 80%, 100% { transform: scale(0); }
                40% { transform: scale(1); }
            }

            .chat-input-area {
                padding: 12px 16px;
                border-top: 1px solid #e5e7eb;
                display: flex;
                gap: 8px;
                background: #f9fafb;
            }

            .chat-input {
                flex: 1;
                padding: 10px 16px;
                border: 1px solid #e5e7eb;
                border-radius: 24px;
                font-size: 14px;
                outline: none;
                transition: border-color 0.2s;
            }

            .chat-input:focus {
                border-color: #4f46e5;
            }

            .chat-send-btn {
                width: 40px;
                height: 40px;
                border-radius: 50%;
                background: #4f46e5;
                color: white;
                border: none;
                cursor: pointer;
                display: flex;
                align-items: center;
                justify-content: center;
                transition: background 0.2s;
            }

            .chat-send-btn:hover {
                background: #4338ca;
            }

            .chat-send-btn:disabled {
                background: #9ca3af;
                cursor: not-allowed;
            }

            .chat-quick-actions {
                padding: 8px 16px;
                border-top: 1px solid #e5e7eb;
                display: flex;
                gap: 6px;
                flex-wrap: wrap;
                background: white;
            }

            .chat-quick-btn {
                padding: 6px 12px;
                border: 1px solid #e5e7eb;
                border-radius: 16px;
                background: white;
                font-size: 12px;
                color: #4b5563;
                cursor: pointer;
                transition: all 0.2s;
            }

            .chat-quick-btn:hover {
                background: #4f46e5;
                color: white;
                border-color: #4f46e5;
            }

            .chat-settings {
                padding: 16px;
                border-top: 1px solid #e5e7eb;
                display: none;
                flex-direction: column;
                gap: 12px;
                background: #f9fafb;
            }

            .chat-settings.open {
                display: flex;
            }

            .chat-settings-title {
                font-size: 14px;
                font-weight: 600;
                color: #374151;
            }

            .chat-settings-group {
                display: flex;
                flex-direction: column;
                gap: 4px;
            }

            .chat-settings-label {
                font-size: 12px;
                color: #6b7280;
            }

            .chat-settings-input {
                padding: 8px 12px;
                border: 1px solid #e5e7eb;
                border-radius: 8px;
                font-size: 13px;
            }

            .chat-settings-select {
                padding: 8px 12px;
                border: 1px solid #e5e7eb;
                border-radius: 8px;
                font-size: 13px;
                background: white;
            }

            .chat-settings-save {
                padding: 8px 16px;
                background: #4f46e5;
                color: white;
                border: none;
                border-radius: 8px;
                cursor: pointer;
                font-size: 13px;
            }

            body.dark-mode .chat-window {
                background: #1f2937;
            }

            body.dark-mode .chat-message.assistant {
                background: #374151;
                color: #e5e7eb;
            }

            body.dark-mode .chat-message.system {
                background: #78350f;
                color: #fef3c7;
            }

            body.dark-mode .chat-input-area {
                background: #111827;
                border-color: #374151;
            }

            body.dark-mode .chat-input {
                background: #1f2937;
                border-color: #374151;
                color: #e5e7eb;
            }

            body.dark-mode .chat-quick-actions {
                background: #1f2937;
                border-color: #374151;
            }

            body.dark-mode .chat-quick-btn {
                background: #374151;
                border-color: #4b5563;
                color: #e5e7eb;
            }

            body.dark-mode .chat-settings {
                background: #111827;
            }

            body.dark-mode .chat-settings-input,
            body.dark-mode .chat-settings-select {
                background: #1f2937;
                border-color: #374151;
                color: #e5e7eb;
            }

            @media (max-width: 480px) {
                .chat-window {
                    width: calc(100vw - 32px);
                    height: 70vh;
                    right: 16px;
                    bottom: 80px;
                }
                .chat-fab {
                    right: 16px;
                    bottom: 16px;
                }
            }

            /* 统计摘要卡片样式 */
            .stats-cards {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
                gap: 12px;
                padding: 16px 24px;
                background: #f8f9fa;
                border-bottom: 1px solid #e5e7eb;
            }

            .stat-card {
                background: white;
                border-radius: 8px;
                padding: 12px;
                text-align: center;
                box-shadow: 0 1px 3px rgba(0,0,0,0.05);
            }

            .stat-card .stat-value {
                font-size: 24px;
                font-weight: 700;
                color: #1a1a1a;
            }

            .stat-card .stat-label {
                font-size: 11px;
                color: #6b7280;
                margin-top: 4px;
            }

            body.dark-mode .stats-cards {
                background: #0f3460;
            }

            body.dark-mode .stat-card {
                background: #16213e;
            }

            body.dark-mode .stat-card .stat-value {
                color: #e5e7eb;
            }

            body.dark-mode .stat-card .stat-label {
                color: #9ca3af;
            }

            /* 图表容器样式 */
            .charts-section {
                padding: 16px 24px;
                background: #f8f9fa;
                border-top: 1px solid #e5e7eb;
            }

            .charts-grid {
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 16px;
            }

            .chart-container {
                background: white;
                border-radius: 12px;
                padding: 16px;
                box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            }

            .chart-title {
                font-size: 14px;
                font-weight: 600;
                color: #374151;
                margin-bottom: 12px;
                display: flex;
                align-items: center;
                gap: 6px;
            }

            .chart-canvas-wrapper {
                position: relative;
                height: 200px;
            }

            body.dark-mode .charts-section {
                background: #0f3460;
            }

            body.dark-mode .chart-container {
                background: #16213e;
            }

            body.dark-mode .chart-title {
                color: #e5e7eb;
            }

            @media (max-width: 600px) {
                .charts-grid {
                    grid-template-columns: 1fr;
                }
            }

            .header-title {
                font-size: 22px;
                font-weight: 700;
                margin: 0 0 20px 0;
            }

            .header-info {
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 16px;
                font-size: 14px;
                opacity: 0.95;
            }

            .info-item {
                text-align: center;
            }

            .info-label {
                display: block;
                font-size: 12px;
                opacity: 0.8;
                margin-bottom: 4px;
            }

            .info-value {
                font-weight: 600;
                font-size: 16px;
            }

            .content {
                padding: 24px;
            }

            .word-group {
                margin-bottom: 40px;
            }

            .word-group:first-child {
                margin-top: 0;
            }

            .word-header {
                display: flex;
                align-items: center;
                justify-content: space-between;
                margin-bottom: 20px;
                padding-bottom: 8px;
                border-bottom: 1px solid #f0f0f0;
            }

            .word-info {
                display: flex;
                align-items: center;
                gap: 12px;
            }

            .word-name {
                font-size: 17px;
                font-weight: 600;
                color: #1a1a1a;
            }

            .word-count {
                color: #666;
                font-size: 13px;
                font-weight: 500;
            }

            .word-count.hot { color: #dc2626; font-weight: 600; }
            .word-count.warm { color: #ea580c; font-weight: 600; }

            .word-index {
                color: #999;
                font-size: 12px;
            }

            .news-item {
                margin-bottom: 20px;
                padding: 16px 0;
                border-bottom: 1px solid #f5f5f5;
                position: relative;
                display: flex;
                gap: 12px;
                align-items: center;
            }

            .news-item:last-child {
                border-bottom: none;
            }

            .news-item.new::after {
                content: "NEW";
                position: absolute;
                top: 12px;
                right: 0;
                background: #fbbf24;
                color: #92400e;
                font-size: 9px;
                font-weight: 700;
                padding: 3px 6px;
                border-radius: 4px;
                letter-spacing: 0.5px;
            }

            .news-number {
                color: #999;
                font-size: 13px;
                font-weight: 600;
                min-width: 20px;
                text-align: center;
                flex-shrink: 0;
                background: #f8f9fa;
                border-radius: 50%;
                width: 24px;
                height: 24px;
                display: flex;
                align-items: center;
                justify-content: center;
                align-self: flex-start;
                margin-top: 8px;
            }

            .news-content {
                flex: 1;
                min-width: 0;
                padding-right: 40px;
            }

            .news-item.new .news-content {
                padding-right: 50px;
            }

            .news-header {
                display: flex;
                align-items: center;
                gap: 8px;
                margin-bottom: 8px;
                flex-wrap: wrap;
            }

            .source-name {
                color: #666;
                font-size: 12px;
                font-weight: 500;
            }

            .keyword-tag {
                color: #2563eb;
                font-size: 12px;
                font-weight: 500;
                background: #eff6ff;
                padding: 2px 6px;
                border-radius: 4px;
            }

            .rank-num {
                color: #fff;
                background: #6b7280;
                font-size: 10px;
                font-weight: 700;
                padding: 2px 6px;
                border-radius: 10px;
                min-width: 18px;
                text-align: center;
            }

            .rank-num.top { background: #dc2626; }
            .rank-num.high { background: #ea580c; }

            .time-info {
                color: #999;
                font-size: 11px;
            }

            .count-info {
                color: #059669;
                font-size: 11px;
                font-weight: 500;
            }

            .news-title {
                font-size: 15px;
                line-height: 1.4;
                color: #1a1a1a;
                margin: 0;
            }

            .news-link {
                color: #2563eb;
                text-decoration: none;
            }

            .news-link:hover {
                text-decoration: underline;
            }

            .news-link:visited {
                color: #7c3aed;
            }

            /* 通用区域分割线样式 */
            .section-divider {
                margin-top: 32px;
                padding-top: 24px;
                border-top: 2px solid #e5e7eb;
            }

            /* 热榜统计区样式 */
            .hotlist-section {
                /* 默认无边框，由 section-divider 动态添加 */
            }

            .new-section {
                margin-top: 40px;
                padding-top: 24px;
            }

            .new-section-title {
                color: #1a1a1a;
                font-size: 16px;
                font-weight: 600;
                margin: 0 0 20px 0;
            }

            .new-source-group {
                margin-bottom: 24px;
            }

            .new-source-title {
                color: #666;
                font-size: 13px;
                font-weight: 500;
                margin: 0 0 12px 0;
                padding-bottom: 6px;
                border-bottom: 1px solid #f5f5f5;
            }

            .new-item {
                display: flex;
                align-items: center;
                gap: 12px;
                padding: 8px 0;
                border-bottom: 1px solid #f9f9f9;
            }

            .new-item:last-child {
                border-bottom: none;
            }

            .new-item-number {
                color: #999;
                font-size: 12px;
                font-weight: 600;
                min-width: 18px;
                text-align: center;
                flex-shrink: 0;
                background: #f8f9fa;
                border-radius: 50%;
                width: 20px;
                height: 20px;
                display: flex;
                align-items: center;
                justify-content: center;
            }

            .new-item-rank {
                color: #fff;
                background: #6b7280;
                font-size: 10px;
                font-weight: 700;
                padding: 3px 6px;
                border-radius: 8px;
                min-width: 20px;
                text-align: center;
                flex-shrink: 0;
            }

            .new-item-rank.top { background: #dc2626; }
            .new-item-rank.high { background: #ea580c; }

            .new-item-content {
                flex: 1;
                min-width: 0;
            }

            .new-item-title {
                font-size: 14px;
                line-height: 1.4;
                color: #1a1a1a;
                margin: 0;
            }

            .error-section {
                background: #fef2f2;
                border: 1px solid #fecaca;
                border-radius: 8px;
                padding: 16px;
                margin-bottom: 24px;
            }

            .error-title {
                color: #dc2626;
                font-size: 14px;
                font-weight: 600;
                margin: 0 0 8px 0;
            }

            .error-list {
                list-style: none;
                padding: 0;
                margin: 0;
            }

            .error-item {
                color: #991b1b;
                font-size: 13px;
                padding: 2px 0;
                font-family: 'SF Mono', Consolas, monospace;
            }

            .footer {
                margin-top: 32px;
                padding: 20px 24px;
                background: #f8f9fa;
                border-top: 1px solid #e5e7eb;
                text-align: center;
            }

            .footer-content {
                font-size: 13px;
                color: #6b7280;
                line-height: 1.6;
            }

            .footer-link {
                color: #4f46e5;
                text-decoration: none;
                font-weight: 500;
                transition: color 0.2s ease;
            }

            .footer-link:hover {
                color: #7c3aed;
                text-decoration: underline;
            }

            .project-name {
                font-weight: 600;
                color: #374151;
            }

            @media (max-width: 480px) {
                body { padding: 12px; }
                .header { padding: 24px 20px; }
                .content { padding: 20px; }
                .footer { padding: 16px 20px; }
                .header-info { grid-template-columns: 1fr; gap: 12px; }
                .news-header { gap: 6px; }
                .news-content { padding-right: 45px; }
                .news-item { gap: 8px; }
                .new-item { gap: 8px; }
                .news-number { width: 20px; height: 20px; font-size: 12px; }
                .save-buttons {
                    position: static;
                    margin-bottom: 16px;
                    display: flex;
                    gap: 8px;
                    justify-content: center;
                    flex-direction: column;
                    width: 100%;
                }
                .save-btn {
                    width: 100%;
                }
            }

            /* RSS 订阅内容样式 */
            .rss-section {
                margin-top: 32px;
                padding-top: 24px;
            }

            .rss-section-header {
                display: flex;
                align-items: center;
                justify-content: space-between;
                margin-bottom: 20px;
            }

            .rss-section-title {
                font-size: 18px;
                font-weight: 600;
                color: #059669;
            }

            .rss-section-count {
                color: #6b7280;
                font-size: 14px;
            }

            .feed-group {
                margin-bottom: 24px;
            }

            .feed-group:last-child {
                margin-bottom: 0;
            }

            .feed-header {
                display: flex;
                align-items: center;
                justify-content: space-between;
                margin-bottom: 12px;
                padding-bottom: 8px;
                border-bottom: 2px solid #10b981;
            }

            .feed-name {
                font-size: 15px;
                font-weight: 600;
                color: #059669;
            }

            .feed-count {
                color: #666;
                font-size: 13px;
                font-weight: 500;
            }

            .rss-item {
                margin-bottom: 12px;
                padding: 14px;
                background: #f0fdf4;
                border-radius: 8px;
                border-left: 3px solid #10b981;
            }

            .rss-item:last-child {
                margin-bottom: 0;
            }

            .rss-meta {
                display: flex;
                align-items: center;
                gap: 12px;
                margin-bottom: 6px;
                flex-wrap: wrap;
            }

            .rss-time {
                color: #6b7280;
                font-size: 12px;
            }

            .rss-author {
                color: #059669;
                font-size: 12px;
                font-weight: 500;
            }

            .rss-title {
                font-size: 14px;
                line-height: 1.5;
                margin-bottom: 6px;
            }

            .rss-link {
                color: #1f2937;
                text-decoration: none;
                font-weight: 500;
            }

            .rss-link:hover {
                color: #059669;
                text-decoration: underline;
            }

            .rss-summary {
                font-size: 13px;
                color: #6b7280;
                line-height: 1.5;
                margin: 0;
                display: -webkit-box;
                -webkit-line-clamp: 2;
                -webkit-box-orient: vertical;
                overflow: hidden;
            }

            /* 独立展示区样式 - 复用热点词汇统计区样式 */
            .standalone-section {
                margin-top: 32px;
                padding-top: 24px;
            }

            .standalone-section-header {
                display: flex;
                align-items: center;
                justify-content: space-between;
                margin-bottom: 20px;
            }

            .standalone-section-title {
                font-size: 18px;
                font-weight: 600;
                color: #059669;
            }

            .standalone-section-count {
                color: #6b7280;
                font-size: 14px;
            }

            .standalone-group {
                margin-bottom: 40px;
            }

            .standalone-group:last-child {
                margin-bottom: 0;
            }

            .standalone-header {
                display: flex;
                align-items: center;
                justify-content: space-between;
                margin-bottom: 20px;
                padding-bottom: 8px;
                border-bottom: 1px solid #f0f0f0;
            }

            .standalone-name {
                font-size: 17px;
                font-weight: 600;
                color: #1a1a1a;
            }

            .standalone-count {
                color: #666;
                font-size: 13px;
                font-weight: 500;
            }

            /* AI 分析区块样式 */
            .ai-section {
                margin-top: 32px;
                padding: 24px;
                background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%);
                border-radius: 12px;
                border: 1px solid #bae6fd;
            }

            .ai-section-header {
                display: flex;
                align-items: center;
                gap: 10px;
                margin-bottom: 20px;
            }

            .ai-section-title {
                font-size: 18px;
                font-weight: 600;
                color: #0369a1;
            }

            .ai-section-badge {
                background: #0ea5e9;
                color: white;
                font-size: 11px;
                font-weight: 600;
                padding: 3px 8px;
                border-radius: 4px;
            }

            .ai-block {
                margin-bottom: 16px;
                padding: 16px;
                background: white;
                border-radius: 8px;
                box-shadow: 0 1px 3px rgba(0,0,0,0.05);
            }

            .ai-block:last-child {
                margin-bottom: 0;
            }

            .ai-block-title {
                font-size: 14px;
                font-weight: 600;
                color: #0369a1;
                margin-bottom: 8px;
            }

            .ai-block-content {
                font-size: 14px;
                line-height: 1.6;
                color: #334155;
                white-space: pre-wrap;
            }

            .ai-error {
                padding: 16px;
                background: #fef2f2;
                border: 1px solid #fecaca;
                border-radius: 8px;
                color: #991b1b;
                font-size: 14px;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <div class="save-buttons">
                    <button class="save-btn" onclick="saveAsImage()">保存为图片</button>
                    <button class="save-btn" onclick="saveAsMultipleImages()">分段保存</button>
                </div>
                <div class="header-title">热点新闻分析</div>
                <div class="header-info">
                    <div class="info-item">
                        <span class="info-label">报告类型</span>
                        <span class="info-value">"""

    # 处理报告类型显示（根据 mode 直接显示）
    if mode == "current":
        html += "当前榜单"
    elif mode == "incremental":
        html += "增量分析"
    else:
        html += "全天汇总"

    html += """</span>
                    </div>
                    <div class="info-item">
                        <span class="info-label">新闻总数</span>
                        <span class="info-value">"""

    html += f"{total_titles} 条"

    # 计算筛选后的热点新闻数量
    hot_news_count = sum(len(stat["titles"]) for stat in report_data["stats"])

    html += """</span>
                    </div>
                    <div class="info-item">
                        <span class="info-label">热点新闻</span>
                        <span class="info-value">"""

    html += f"{hot_news_count} 条"

    html += """</span>
                    </div>
                    <div class="info-item">
                        <span class="info-label">生成时间</span>
                        <span class="info-value">"""

    # 使用提供的时间函数或默认 datetime.now
    if get_time_func:
        now = get_time_func()
    else:
        now = datetime.now()
    html += now.strftime("%m-%d %H:%M")

    html += """</span>
                    </div>
                </div>
            </div>

            <div class="toolbar">
                <div class="search-box">
                    <span class="search-icon">🔍</span>
                    <input type="text" class="search-input" placeholder="搜索新闻标题..." oninput="handleSearch(this.value)">
                </div>
                <button class="toolbar-btn" onclick="toggleAllGroups()" title="展开/折叠全部">
                    <span>📂</span> 折叠
                </button>
                <button class="toolbar-btn" onclick="toggleDarkMode()" title="切换暗色模式">
                    <span class="dark-mode-icon">🌙</span> 暗色
                </button>
                <button class="toolbar-btn" id="autoRefreshBtn" onclick="toggleAutoRefresh()" title="自动刷新">
                    <span>🔄</span> <span id="autoRefreshText">自动刷新</span>
                </button>
            </div>
            <div class="search-stats" id="searchStats"></div>
            <div class="refresh-countdown hidden" id="refreshCountdown">下次刷新: <span id="countdown">--</span> 秒</div>

            <div class="stats-cards" id="statsCards">
                <div class="stat-card">
                    <div class="stat-value" id="statTotalNews">--</div>
                    <div class="stat-label">新闻总数</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value" id="statHotNews">--</div>
                    <div class="stat-label">热点新闻</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value" id="statKeywords">--</div>
                    <div class="stat-label">关键词组</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value" id="statNewItems">--</div>
                    <div class="stat-label">新增热点</div>
                </div>
            </div>

            <!-- 数据可视化图表区域 -->
            <div class="charts-section" id="chartsSection">
                <div class="charts-grid">
                    <div class="chart-container">
                        <div class="chart-title">📊 平台分布</div>
                        <div class="chart-canvas-wrapper">
                            <canvas id="platformChart"></canvas>
                        </div>
                    </div>
                    <div class="chart-container">
                        <div class="chart-title">🔥 热词 TOP 10</div>
                        <div class="chart-canvas-wrapper">
                            <canvas id="keywordChart"></canvas>
                        </div>
                    </div>
                </div>
            </div>

            <div class="content">"""

    # 处理失败ID错误信息
    if report_data["failed_ids"]:
        html += """
                <div class="error-section">
                    <div class="error-title">⚠️ 请求失败的平台</div>
                    <ul class="error-list">"""
        for id_value in report_data["failed_ids"]:
            html += f'<li class="error-item">{html_escape(id_value)}</li>'
        html += """
                    </ul>
                </div>"""

    # 计算图表数据
    platform_counts = {}
    keyword_counts = []
    
    if report_data["stats"]:
        for stat in report_data["stats"]:
            # 统计关键词热度
            keyword_counts.append({
                "word": stat["word"],
                "count": stat["count"]
            })
            # 统计平台分布
            for title_data in stat["titles"]:
                platform = title_data.get("source_name", "未知")
                platform_counts[platform] = platform_counts.get(platform, 0) + 1
    
    # 取 TOP 10 关键词
    keyword_counts = keyword_counts[:10]
    
    # 转换为 JSON 字符串供 JavaScript 使用
    import json
    platform_data_json = json.dumps(platform_counts, ensure_ascii=False)
    keyword_data_json = json.dumps(keyword_counts, ensure_ascii=False)

    # 生成热点词汇统计部分的HTML
    stats_html = ""
    if report_data["stats"]:
        total_count = len(report_data["stats"])

        for i, stat in enumerate(report_data["stats"], 1):
            count = stat["count"]

            # 确定热度等级
            if count >= 10:
                count_class = "hot"
            elif count >= 5:
                count_class = "warm"
            else:
                count_class = ""

            escaped_word = html_escape(stat["word"])

            stats_html += f"""
                <div class="word-group">
                    <div class="word-header">
                        <div class="word-info">
                            <div class="word-name">{escaped_word}</div>
                            <div class="word-count {count_class}">{count} 条</div>
                        </div>
                        <div class="word-index">{i}/{total_count}</div>
                    </div>"""

            # 处理每个词组下的新闻标题，给每条新闻标上序号
            for j, title_data in enumerate(stat["titles"], 1):
                is_new = title_data.get("is_new", False)
                new_class = "new" if is_new else ""

                stats_html += f"""
                    <div class="news-item {new_class}">
                        <div class="news-number">{j}</div>
                        <div class="news-content">
                            <div class="news-header">"""

                # 根据 display_mode 决定显示来源还是关键词
                if display_mode == "keyword":
                    # keyword 模式：显示来源
                    stats_html += f'<span class="source-name">{html_escape(title_data["source_name"])}</span>'
                else:
                    # platform 模式：显示关键词
                    matched_keyword = title_data.get("matched_keyword", "")
                    if matched_keyword:
                        stats_html += f'<span class="keyword-tag">[{html_escape(matched_keyword)}]</span>'

                # 处理排名显示
                ranks = title_data.get("ranks", [])
                if ranks:
                    min_rank = min(ranks)
                    max_rank = max(ranks)
                    rank_threshold = title_data.get("rank_threshold", 10)

                    # 确定排名等级
                    if min_rank <= 3:
                        rank_class = "top"
                    elif min_rank <= rank_threshold:
                        rank_class = "high"
                    else:
                        rank_class = ""

                    if min_rank == max_rank:
                        rank_text = str(min_rank)
                    else:
                        rank_text = f"{min_rank}-{max_rank}"

                    stats_html += f'<span class="rank-num {rank_class}">{rank_text}</span>'

                # 处理时间显示
                time_display = title_data.get("time_display", "")
                if time_display:
                    # 简化时间显示格式，将波浪线替换为~
                    simplified_time = (
                        time_display.replace(" ~ ", "~")
                        .replace("[", "")
                        .replace("]", "")
                    )
                    stats_html += (
                        f'<span class="time-info">{html_escape(simplified_time)}</span>'
                    )

                # 处理出现次数
                count_info = title_data.get("count", 1)
                if count_info > 1:
                    stats_html += f'<span class="count-info">{count_info}次</span>'

                stats_html += """
                            </div>
                            <div class="news-title">"""

                # 处理标题和链接
                escaped_title = html_escape(title_data["title"])
                link_url = title_data.get("mobile_url") or title_data.get("url", "")

                if link_url:
                    escaped_url = html_escape(link_url)
                    stats_html += f'<a href="{escaped_url}" target="_blank" class="news-link">{escaped_title}</a>'
                else:
                    stats_html += escaped_title

                stats_html += """
                            </div>
                        </div>
                    </div>"""

            stats_html += """
                </div>"""

    # 给热榜统计添加外层包装
    if stats_html:
        stats_html = f"""
                <div class="hotlist-section">{stats_html}
                </div>"""

    # 生成新增新闻区域的HTML
    new_titles_html = ""
    if show_new_section and report_data["new_titles"]:
        new_titles_html += f"""
                <div class="new-section">
                    <div class="new-section-title">本次新增热点 (共 {report_data['total_new_count']} 条)</div>"""

        for source_data in report_data["new_titles"]:
            escaped_source = html_escape(source_data["source_name"])
            titles_count = len(source_data["titles"])

            new_titles_html += f"""
                    <div class="new-source-group">
                        <div class="new-source-title">{escaped_source} · {titles_count}条</div>"""

            # 为新增新闻也添加序号
            for idx, title_data in enumerate(source_data["titles"], 1):
                ranks = title_data.get("ranks", [])

                # 处理新增新闻的排名显示
                rank_class = ""
                if ranks:
                    min_rank = min(ranks)
                    if min_rank <= 3:
                        rank_class = "top"
                    elif min_rank <= title_data.get("rank_threshold", 10):
                        rank_class = "high"

                    if len(ranks) == 1:
                        rank_text = str(ranks[0])
                    else:
                        rank_text = f"{min(ranks)}-{max(ranks)}"
                else:
                    rank_text = "?"

                new_titles_html += f"""
                        <div class="new-item">
                            <div class="new-item-number">{idx}</div>
                            <div class="new-item-rank {rank_class}">{rank_text}</div>
                            <div class="new-item-content">
                                <div class="new-item-title">"""

                # 处理新增新闻的链接
                escaped_title = html_escape(title_data["title"])
                link_url = title_data.get("mobile_url") or title_data.get("url", "")

                if link_url:
                    escaped_url = html_escape(link_url)
                    new_titles_html += f'<a href="{escaped_url}" target="_blank" class="news-link">{escaped_title}</a>'
                else:
                    new_titles_html += escaped_title

                new_titles_html += """
                                </div>
                            </div>
                        </div>"""

            new_titles_html += """
                    </div>"""

        new_titles_html += """
                </div>"""

    # 生成 RSS 统计内容
    def render_rss_stats_html(stats: List[Dict], title: str = "RSS 订阅更新") -> str:
        """渲染 RSS 统计区块 HTML

        Args:
            stats: RSS 分组统计列表，格式与热榜一致：
                [
                    {
                        "word": "关键词",
                        "count": 5,
                        "titles": [
                            {
                                "title": "标题",
                                "source_name": "Feed 名称",
                                "time_display": "12-29 08:20",
                                "url": "...",
                                "is_new": True/False
                            }
                        ]
                    }
                ]
            title: 区块标题

        Returns:
            渲染后的 HTML 字符串
        """
        if not stats:
            return ""

        # 计算总条目数
        total_count = sum(stat.get("count", 0) for stat in stats)
        if total_count == 0:
            return ""

        rss_html = f"""
                <div class="rss-section">
                    <div class="rss-section-header">
                        <div class="rss-section-title">{title}</div>
                        <div class="rss-section-count">{total_count} 条</div>
                    </div>"""

        # 按关键词分组渲染（与热榜格式一致）
        for stat in stats:
            keyword = stat.get("word", "")
            titles = stat.get("titles", [])
            if not titles:
                continue

            keyword_count = len(titles)

            rss_html += f"""
                    <div class="feed-group">
                        <div class="feed-header">
                            <div class="feed-name">{html_escape(keyword)}</div>
                            <div class="feed-count">{keyword_count} 条</div>
                        </div>"""

            for title_data in titles:
                item_title = title_data.get("title", "")
                url = title_data.get("url", "")
                time_display = title_data.get("time_display", "")
                source_name = title_data.get("source_name", "")
                is_new = title_data.get("is_new", False)

                rss_html += """
                        <div class="rss-item">
                            <div class="rss-meta">"""

                if time_display:
                    rss_html += f'<span class="rss-time">{html_escape(time_display)}</span>'

                if source_name:
                    rss_html += f'<span class="rss-author">{html_escape(source_name)}</span>'

                if is_new:
                    rss_html += '<span class="rss-author" style="color: #dc2626;">NEW</span>'

                rss_html += """
                            </div>
                            <div class="rss-title">"""

                escaped_title = html_escape(item_title)
                if url:
                    escaped_url = html_escape(url)
                    rss_html += f'<a href="{escaped_url}" target="_blank" class="rss-link">{escaped_title}</a>'
                else:
                    rss_html += escaped_title

                rss_html += """
                            </div>
                        </div>"""

            rss_html += """
                    </div>"""

        rss_html += """
                </div>"""
        return rss_html

    # 生成独立展示区内容
    def render_standalone_html(data: Optional[Dict]) -> str:
        """渲染独立展示区 HTML（复用热点词汇统计区样式）

        Args:
            data: 独立展示数据，格式：
                {
                    "platforms": [
                        {
                            "id": "zhihu",
                            "name": "知乎热榜",
                            "items": [
                                {
                                    "title": "标题",
                                    "url": "链接",
                                    "rank": 1,
                                    "ranks": [1, 2, 1],
                                    "first_time": "08:00",
                                    "last_time": "12:30",
                                    "count": 3,
                                }
                            ]
                        }
                    ],
                    "rss_feeds": [
                        {
                            "id": "hacker-news",
                            "name": "Hacker News",
                            "items": [
                                {
                                    "title": "标题",
                                    "url": "链接",
                                    "published_at": "2025-01-07T08:00:00",
                                    "author": "作者",
                                }
                            ]
                        }
                    ]
                }

        Returns:
            渲染后的 HTML 字符串
        """
        if not data:
            return ""

        platforms = data.get("platforms", [])
        rss_feeds = data.get("rss_feeds", [])

        if not platforms and not rss_feeds:
            return ""

        # 计算总条目数
        total_platform_items = sum(len(p.get("items", [])) for p in platforms)
        total_rss_items = sum(len(f.get("items", [])) for f in rss_feeds)
        total_count = total_platform_items + total_rss_items

        if total_count == 0:
            return ""

        standalone_html = f"""
                <div class="standalone-section">
                    <div class="standalone-section-header">
                        <div class="standalone-section-title">独立展示区</div>
                        <div class="standalone-section-count">{total_count} 条</div>
                    </div>"""

        # 渲染热榜平台（复用 word-group 结构）
        for platform in platforms:
            platform_name = platform.get("name", platform.get("id", ""))
            items = platform.get("items", [])
            if not items:
                continue

            standalone_html += f"""
                    <div class="standalone-group">
                        <div class="standalone-header">
                            <div class="standalone-name">{html_escape(platform_name)}</div>
                            <div class="standalone-count">{len(items)} 条</div>
                        </div>"""

            # 渲染每个条目（复用 news-item 结构）
            for j, item in enumerate(items, 1):
                title = item.get("title", "")
                url = item.get("url", "") or item.get("mobileUrl", "")
                rank = item.get("rank", 0)
                ranks = item.get("ranks", [])
                first_time = item.get("first_time", "")
                last_time = item.get("last_time", "")
                count = item.get("count", 1)

                standalone_html += f"""
                        <div class="news-item">
                            <div class="news-number">{j}</div>
                            <div class="news-content">
                                <div class="news-header">"""

                # 排名显示（复用 rank-num 样式，无 # 前缀）
                if ranks:
                    min_rank = min(ranks)
                    max_rank = max(ranks)

                    # 确定排名等级
                    if min_rank <= 3:
                        rank_class = "top"
                    elif min_rank <= 10:
                        rank_class = "high"
                    else:
                        rank_class = ""

                    if min_rank == max_rank:
                        rank_text = str(min_rank)
                    else:
                        rank_text = f"{min_rank}-{max_rank}"

                    standalone_html += f'<span class="rank-num {rank_class}">{rank_text}</span>'
                elif rank > 0:
                    if rank <= 3:
                        rank_class = "top"
                    elif rank <= 10:
                        rank_class = "high"
                    else:
                        rank_class = ""
                    standalone_html += f'<span class="rank-num {rank_class}">{rank}</span>'

                # 时间显示（复用 time-info 样式，将 HH-MM 转换为 HH:MM）
                if first_time and last_time and first_time != last_time:
                    first_time_display = convert_time_for_display(first_time)
                    last_time_display = convert_time_for_display(last_time)
                    standalone_html += f'<span class="time-info">{html_escape(first_time_display)}~{html_escape(last_time_display)}</span>'
                elif first_time:
                    first_time_display = convert_time_for_display(first_time)
                    standalone_html += f'<span class="time-info">{html_escape(first_time_display)}</span>'

                # 出现次数（复用 count-info 样式）
                if count > 1:
                    standalone_html += f'<span class="count-info">{count}次</span>'

                standalone_html += """
                                </div>
                                <div class="news-title">"""

                # 标题和链接（复用 news-link 样式）
                escaped_title = html_escape(title)
                if url:
                    escaped_url = html_escape(url)
                    standalone_html += f'<a href="{escaped_url}" target="_blank" class="news-link">{escaped_title}</a>'
                else:
                    standalone_html += escaped_title

                standalone_html += """
                                </div>
                            </div>
                        </div>"""

            standalone_html += """
                    </div>"""

        # 渲染 RSS 源（复用相同结构）
        for feed in rss_feeds:
            feed_name = feed.get("name", feed.get("id", ""))
            items = feed.get("items", [])
            if not items:
                continue

            standalone_html += f"""
                    <div class="standalone-group">
                        <div class="standalone-header">
                            <div class="standalone-name">{html_escape(feed_name)}</div>
                            <div class="standalone-count">{len(items)} 条</div>
                        </div>"""

            for j, item in enumerate(items, 1):
                title = item.get("title", "")
                url = item.get("url", "")
                published_at = item.get("published_at", "")
                author = item.get("author", "")

                standalone_html += f"""
                        <div class="news-item">
                            <div class="news-number">{j}</div>
                            <div class="news-content">
                                <div class="news-header">"""

                # 时间显示（格式化 ISO 时间）
                if published_at:
                    try:
                        from datetime import datetime as dt
                        if "T" in published_at:
                            dt_obj = dt.fromisoformat(published_at.replace("Z", "+00:00"))
                            time_display = dt_obj.strftime("%m-%d %H:%M")
                        else:
                            time_display = published_at
                    except:
                        time_display = published_at

                    standalone_html += f'<span class="time-info">{html_escape(time_display)}</span>'

                # 作者显示
                if author:
                    standalone_html += f'<span class="source-name">{html_escape(author)}</span>'

                standalone_html += """
                                </div>
                                <div class="news-title">"""

                escaped_title = html_escape(title)
                if url:
                    escaped_url = html_escape(url)
                    standalone_html += f'<a href="{escaped_url}" target="_blank" class="news-link">{escaped_title}</a>'
                else:
                    standalone_html += escaped_title

                standalone_html += """
                                </div>
                            </div>
                        </div>"""

            standalone_html += """
                    </div>"""

        standalone_html += """
                </div>"""
        return standalone_html

    # 生成 RSS 统计和新增 HTML
    rss_stats_html = render_rss_stats_html(rss_items, "RSS 订阅更新") if rss_items else ""
    rss_new_html = render_rss_stats_html(rss_new_items, "RSS 新增更新") if rss_new_items else ""

    # 生成独立展示区 HTML
    standalone_html = render_standalone_html(standalone_data)

    # 生成 AI 分析 HTML
    ai_html = render_ai_analysis_html_rich(ai_analysis) if ai_analysis else ""

    # 准备各区域内容映射
    region_contents = {
        "hotlist": stats_html,
        "rss": rss_stats_html,
        "new_items": (new_titles_html, rss_new_html),  # 元组，分别处理
        "standalone": standalone_html,
        "ai_analysis": ai_html,
    }

    def add_section_divider(content: str) -> str:
        """为内容的外层 div 添加 section-divider 类"""
        if not content or 'class="' not in content:
            return content
        first_class_pos = content.find('class="')
        if first_class_pos != -1:
            insert_pos = first_class_pos + len('class="')
            return content[:insert_pos] + "section-divider " + content[insert_pos:]
        return content

    # 按 region_order 顺序组装内容，动态添加分割线
    has_previous_content = False
    for region in region_order:
        content = region_contents.get(region, "")
        if region == "new_items":
            # 特殊处理 new_items 区域（包含热榜新增和 RSS 新增两部分）
            new_html, rss_new = content
            if new_html:
                if has_previous_content:
                    new_html = add_section_divider(new_html)
                html += new_html
                has_previous_content = True
            if rss_new:
                if has_previous_content:
                    rss_new = add_section_divider(rss_new)
                html += rss_new
                has_previous_content = True
        elif content:
            if has_previous_content:
                content = add_section_divider(content)
            html += content
            has_previous_content = True

    html += """
            </div>

            <div class="footer">
                <div class="footer-content">
                    由 <span class="project-name">TrendRadar</span> 生成 ·
                    <a href="https://github.com/sansan0/TrendRadar" target="_blank" class="footer-link">
                        GitHub 开源项目
                    </a>"""

    if update_info:
        html += f"""
                    <br>
                    <span style="color: #ea580c; font-weight: 500;">
                        发现新版本 {update_info['remote_version']}，当前版本 {update_info['current_version']}
                    </span>"""

    html += """
                </div>
            </div>
        </div>

        <!-- AI 对话浮动按钮 -->
        <button class="chat-fab" onclick="toggleChatWindow()" title="AI 智能对话">
            💬
        </button>

        <!-- AI 对话窗口 -->
        <div class="chat-window" id="chatWindow">
            <div class="chat-header">
                <div class="chat-header-title">
                    <span>🤖</span>
                    <span>AI 智能助手</span>
                </div>
                <div class="chat-header-actions">
                    <button class="chat-header-btn" onclick="toggleChatSettings()" title="设置">⚙️</button>
                    <button class="chat-header-btn" onclick="clearChatHistory()" title="清空">🗑️</button>
                    <button class="chat-header-btn" onclick="toggleChatWindow()" title="关闭">✕</button>
                </div>
            </div>

            <div class="chat-settings" id="chatSettings">
                <div class="chat-settings-title">API 配置</div>
                <div class="chat-settings-group">
                    <label class="chat-settings-label">AI 提供商</label>
                    <select class="chat-settings-select" id="chatProvider">
                        <option value="deepseek">DeepSeek</option>
                        <option value="openai">OpenAI</option>
                        <option value="anthropic">Anthropic</option>
                        <option value="custom">自定义</option>
                    </select>
                </div>
                <div class="chat-settings-group">
                    <label class="chat-settings-label">API Key</label>
                    <input type="password" class="chat-settings-input" id="chatApiKey" placeholder="输入你的 API Key">
                </div>
                <div class="chat-settings-group" id="customBaseUrlGroup" style="display:none;">
                    <label class="chat-settings-label">自定义 Base URL</label>
                    <input type="text" class="chat-settings-input" id="chatBaseUrl" placeholder="https://api.example.com/v1">
                </div>
                <div class="chat-settings-group">
                    <label class="chat-settings-label">MCP Server 地址</label>
                    <input type="text" class="chat-settings-input" id="mcpServerUrl" placeholder="http://127.0.0.1:3333" value="http://127.0.0.1:3333">
                </div>
                <button class="chat-settings-save" onclick="saveChatSettings()">保存设置</button>
            </div>

            <div class="chat-messages" id="chatMessages">
                <div class="chat-message system">
                    👋 你好！我是 TrendRadar AI 助手。我可以帮你分析热点新闻、查询历史数据、推荐关注话题。请先在设置中配置 API Key。
                </div>
            </div>

            <div class="chat-quick-actions">
                <button class="chat-quick-btn" onclick="sendQuickMessage('今日热点有哪些？')">📊 今日热点</button>
                <button class="chat-quick-btn" onclick="sendQuickMessage('分析当前新闻趋势')">📈 趋势分析</button>
                <button class="chat-quick-btn" onclick="sendQuickMessage('推荐值得关注的话题')">💡 智能推荐</button>
                <button class="chat-quick-btn" onclick="sendQuickMessage('总结今天的重要新闻')">📝 新闻摘要</button>
            </div>

            <div class="chat-input-area">
                <input type="text" class="chat-input" id="chatInput" placeholder="输入消息..." onkeypress="handleChatKeypress(event)">
                <button class="chat-send-btn" onclick="sendChatMessage()" id="chatSendBtn">➤</button>
            </div>
        </div>

        <script>
            async function saveAsImage() {
                const button = event.target;
                const originalText = button.textContent;

                try {
                    button.textContent = '生成中...';
                    button.disabled = true;
                    window.scrollTo(0, 0);

                    // 等待页面稳定
                    await new Promise(resolve => setTimeout(resolve, 200));

                    // 截图前隐藏按钮
                    const buttons = document.querySelector('.save-buttons');
                    buttons.style.visibility = 'hidden';

                    // 再次等待确保按钮完全隐藏
                    await new Promise(resolve => setTimeout(resolve, 100));

                    const container = document.querySelector('.container');

                    const canvas = await html2canvas(container, {
                        backgroundColor: '#ffffff',
                        scale: 1.5,
                        useCORS: true,
                        allowTaint: false,
                        imageTimeout: 10000,
                        removeContainer: false,
                        foreignObjectRendering: false,
                        logging: false,
                        width: container.offsetWidth,
                        height: container.offsetHeight,
                        x: 0,
                        y: 0,
                        scrollX: 0,
                        scrollY: 0,
                        windowWidth: window.innerWidth,
                        windowHeight: window.innerHeight
                    });

                    buttons.style.visibility = 'visible';

                    const link = document.createElement('a');
                    const now = new Date();
                    const filename = `TrendRadar_热点新闻分析_${now.getFullYear()}${String(now.getMonth() + 1).padStart(2, '0')}${String(now.getDate()).padStart(2, '0')}_${String(now.getHours()).padStart(2, '0')}${String(now.getMinutes()).padStart(2, '0')}.png`;

                    link.download = filename;
                    link.href = canvas.toDataURL('image/png', 1.0);

                    // 触发下载
                    document.body.appendChild(link);
                    link.click();
                    document.body.removeChild(link);

                    button.textContent = '保存成功!';
                    setTimeout(() => {
                        button.textContent = originalText;
                        button.disabled = false;
                    }, 2000);

                } catch (error) {
                    const buttons = document.querySelector('.save-buttons');
                    buttons.style.visibility = 'visible';
                    button.textContent = '保存失败';
                    setTimeout(() => {
                        button.textContent = originalText;
                        button.disabled = false;
                    }, 2000);
                }
            }

            async function saveAsMultipleImages() {
                const button = event.target;
                const originalText = button.textContent;
                const container = document.querySelector('.container');
                const scale = 1.5;
                const maxHeight = 5000 / scale;

                try {
                    button.textContent = '分析中...';
                    button.disabled = true;

                    // 获取所有可能的分割元素
                    const newsItems = Array.from(container.querySelectorAll('.news-item'));
                    const wordGroups = Array.from(container.querySelectorAll('.word-group'));
                    const newSection = container.querySelector('.new-section');
                    const errorSection = container.querySelector('.error-section');
                    const header = container.querySelector('.header');
                    const footer = container.querySelector('.footer');

                    // 计算元素位置和高度
                    const containerRect = container.getBoundingClientRect();
                    const elements = [];

                    // 添加header作为必须包含的元素
                    elements.push({
                        type: 'header',
                        element: header,
                        top: 0,
                        bottom: header.offsetHeight,
                        height: header.offsetHeight
                    });

                    // 添加错误信息（如果存在）
                    if (errorSection) {
                        const rect = errorSection.getBoundingClientRect();
                        elements.push({
                            type: 'error',
                            element: errorSection,
                            top: rect.top - containerRect.top,
                            bottom: rect.bottom - containerRect.top,
                            height: rect.height
                        });
                    }

                    // 按word-group分组处理news-item
                    wordGroups.forEach(group => {
                        const groupRect = group.getBoundingClientRect();
                        const groupNewsItems = group.querySelectorAll('.news-item');

                        // 添加word-group的header部分
                        const wordHeader = group.querySelector('.word-header');
                        if (wordHeader) {
                            const headerRect = wordHeader.getBoundingClientRect();
                            elements.push({
                                type: 'word-header',
                                element: wordHeader,
                                parent: group,
                                top: groupRect.top - containerRect.top,
                                bottom: headerRect.bottom - containerRect.top,
                                height: headerRect.height
                            });
                        }

                        // 添加每个news-item
                        groupNewsItems.forEach(item => {
                            const rect = item.getBoundingClientRect();
                            elements.push({
                                type: 'news-item',
                                element: item,
                                parent: group,
                                top: rect.top - containerRect.top,
                                bottom: rect.bottom - containerRect.top,
                                height: rect.height
                            });
                        });
                    });

                    // 添加新增新闻部分
                    if (newSection) {
                        const rect = newSection.getBoundingClientRect();
                        elements.push({
                            type: 'new-section',
                            element: newSection,
                            top: rect.top - containerRect.top,
                            bottom: rect.bottom - containerRect.top,
                            height: rect.height
                        });
                    }

                    // 添加footer
                    const footerRect = footer.getBoundingClientRect();
                    elements.push({
                        type: 'footer',
                        element: footer,
                        top: footerRect.top - containerRect.top,
                        bottom: footerRect.bottom - containerRect.top,
                        height: footer.offsetHeight
                    });

                    // 计算分割点
                    const segments = [];
                    let currentSegment = { start: 0, end: 0, height: 0, includeHeader: true };
                    let headerHeight = header.offsetHeight;
                    currentSegment.height = headerHeight;

                    for (let i = 1; i < elements.length; i++) {
                        const element = elements[i];
                        const potentialHeight = element.bottom - currentSegment.start;

                        // 检查是否需要创建新分段
                        if (potentialHeight > maxHeight && currentSegment.height > headerHeight) {
                            // 在前一个元素结束处分割
                            currentSegment.end = elements[i - 1].bottom;
                            segments.push(currentSegment);

                            // 开始新分段
                            currentSegment = {
                                start: currentSegment.end,
                                end: 0,
                                height: element.bottom - currentSegment.end,
                                includeHeader: false
                            };
                        } else {
                            currentSegment.height = potentialHeight;
                            currentSegment.end = element.bottom;
                        }
                    }

                    // 添加最后一个分段
                    if (currentSegment.height > 0) {
                        currentSegment.end = container.offsetHeight;
                        segments.push(currentSegment);
                    }

                    button.textContent = `生成中 (0/${segments.length})...`;

                    // 隐藏保存按钮
                    const buttons = document.querySelector('.save-buttons');
                    buttons.style.visibility = 'hidden';

                    // 为每个分段生成图片
                    const images = [];
                    for (let i = 0; i < segments.length; i++) {
                        const segment = segments[i];
                        button.textContent = `生成中 (${i + 1}/${segments.length})...`;

                        // 创建临时容器用于截图
                        const tempContainer = document.createElement('div');
                        tempContainer.style.cssText = `
                            position: absolute;
                            left: -9999px;
                            top: 0;
                            width: ${container.offsetWidth}px;
                            background: white;
                        `;
                        tempContainer.className = 'container';

                        // 克隆容器内容
                        const clonedContainer = container.cloneNode(true);

                        // 移除克隆内容中的保存按钮
                        const clonedButtons = clonedContainer.querySelector('.save-buttons');
                        if (clonedButtons) {
                            clonedButtons.style.display = 'none';
                        }

                        tempContainer.appendChild(clonedContainer);
                        document.body.appendChild(tempContainer);

                        // 等待DOM更新
                        await new Promise(resolve => setTimeout(resolve, 100));

                        // 使用html2canvas截取特定区域
                        const canvas = await html2canvas(clonedContainer, {
                            backgroundColor: '#ffffff',
                            scale: scale,
                            useCORS: true,
                            allowTaint: false,
                            imageTimeout: 10000,
                            logging: false,
                            width: container.offsetWidth,
                            height: segment.end - segment.start,
                            x: 0,
                            y: segment.start,
                            windowWidth: window.innerWidth,
                            windowHeight: window.innerHeight
                        });

                        images.push(canvas.toDataURL('image/png', 1.0));

                        // 清理临时容器
                        document.body.removeChild(tempContainer);
                    }

                    // 恢复按钮显示
                    buttons.style.visibility = 'visible';

                    // 下载所有图片
                    const now = new Date();
                    const baseFilename = `TrendRadar_热点新闻分析_${now.getFullYear()}${String(now.getMonth() + 1).padStart(2, '0')}${String(now.getDate()).padStart(2, '0')}_${String(now.getHours()).padStart(2, '0')}${String(now.getMinutes()).padStart(2, '0')}`;

                    for (let i = 0; i < images.length; i++) {
                        const link = document.createElement('a');
                        link.download = `${baseFilename}_part${i + 1}.png`;
                        link.href = images[i];
                        document.body.appendChild(link);
                        link.click();
                        document.body.removeChild(link);

                        // 延迟一下避免浏览器阻止多个下载
                        await new Promise(resolve => setTimeout(resolve, 100));
                    }

                    button.textContent = `已保存 ${segments.length} 张图片!`;
                    setTimeout(() => {
                        button.textContent = originalText;
                        button.disabled = false;
                    }, 2000);

                } catch (error) {
                    console.error('分段保存失败:', error);
                    const buttons = document.querySelector('.save-buttons');
                    buttons.style.visibility = 'visible';
                    button.textContent = '保存失败';
                    setTimeout(() => {
                        button.textContent = originalText;
                        button.disabled = false;
                    }, 2000);
                }
            }

            document.addEventListener('DOMContentLoaded', function() {
                window.scrollTo(0, 0);
                
                // 为所有 word-group 添加折叠功能
                document.querySelectorAll('.word-header').forEach(header => {
                    // 添加折叠图标
                    const icon = document.createElement('span');
                    icon.className = 'collapse-icon';
                    icon.textContent = '▼';
                    header.querySelector('.word-info').appendChild(icon);
                    
                    header.addEventListener('click', function() {
                        const group = this.closest('.word-group');
                        group.classList.toggle('collapsed');
                    });
                });
                
                // 检查是否有保存的暗色模式偏好
                if (localStorage.getItem('darkMode') === 'true') {
                    document.body.classList.add('dark-mode');
                    updateDarkModeButton();
                }
            });
            
            // 搜索功能
            function handleSearch(query) {
                const searchStats = document.getElementById('searchStats');
                query = query.trim().toLowerCase();
                
                if (!query) {
                    // 清空搜索时，显示所有内容
                    document.querySelectorAll('.word-group, .news-item, .rss-item, .feed-group, .new-source-group').forEach(el => {
                        el.classList.remove('hidden-by-search');
                    });
                    // 清除高亮
                    document.querySelectorAll('.search-highlight').forEach(el => {
                        el.outerHTML = el.textContent;
                    });
                    searchStats.classList.remove('visible');
                    return;
                }
                
                let matchCount = 0;
                let totalItems = 0;
                
                // 搜索热榜新闻
                document.querySelectorAll('.word-group').forEach(group => {
                    let groupHasMatch = false;
                    
                    group.querySelectorAll('.news-item').forEach(item => {
                        totalItems++;
                        const title = item.querySelector('.news-title');
                        const titleText = title.textContent.toLowerCase();
                        
                        if (titleText.includes(query)) {
                            item.classList.remove('hidden-by-search');
                            groupHasMatch = true;
                            matchCount++;
                            // 高亮匹配文字
                            highlightText(title, query);
                        } else {
                            item.classList.add('hidden-by-search');
                        }
                    });
                    
                    // 如果组内有匹配，显示组标题
                    if (groupHasMatch) {
                        group.classList.remove('hidden-by-search');
                        group.classList.remove('collapsed');
                    } else {
                        group.classList.add('hidden-by-search');
                    }
                });
                
                // 搜索 RSS 内容
                document.querySelectorAll('.feed-group').forEach(group => {
                    let groupHasMatch = false;
                    
                    group.querySelectorAll('.rss-item').forEach(item => {
                        totalItems++;
                        const title = item.querySelector('.rss-title');
                        const titleText = title.textContent.toLowerCase();
                        
                        if (titleText.includes(query)) {
                            item.classList.remove('hidden-by-search');
                            groupHasMatch = true;
                            matchCount++;
                            highlightText(title, query);
                        } else {
                            item.classList.add('hidden-by-search');
                        }
                    });
                    
                    group.classList.toggle('hidden-by-search', !groupHasMatch);
                });
                
                // 搜索新增新闻
                document.querySelectorAll('.new-source-group').forEach(group => {
                    let groupHasMatch = false;
                    
                    group.querySelectorAll('.new-item').forEach(item => {
                        totalItems++;
                        const title = item.querySelector('.new-item-title');
                        const titleText = title.textContent.toLowerCase();
                        
                        if (titleText.includes(query)) {
                            item.classList.remove('hidden-by-search');
                            groupHasMatch = true;
                            matchCount++;
                            highlightText(title, query);
                        } else {
                            item.classList.add('hidden-by-search');
                        }
                    });
                    
                    group.classList.toggle('hidden-by-search', !groupHasMatch);
                });
                
                // 更新搜索统计
                searchStats.textContent = `找到 ${matchCount} 条匹配结果（共 ${totalItems} 条）`;
                searchStats.classList.add('visible');
            }
            
            function highlightText(element, query) {
                // 先清除已有高亮
                element.querySelectorAll('.search-highlight').forEach(el => {
                    el.outerHTML = el.textContent;
                });
                
                // 获取所有文本节点
                const walker = document.createTreeWalker(element, NodeFilter.SHOW_TEXT, null, false);
                const textNodes = [];
                while(walker.nextNode()) textNodes.push(walker.currentNode);
                
                textNodes.forEach(node => {
                    const text = node.textContent;
                    const lowerText = text.toLowerCase();
                    const index = lowerText.indexOf(query.toLowerCase());
                    
                    if (index !== -1) {
                        const before = text.substring(0, index);
                        const match = text.substring(index, index + query.length);
                        const after = text.substring(index + query.length);
                        
                        const span = document.createElement('span');
                        span.className = 'search-highlight';
                        span.textContent = match;
                        
                        const fragment = document.createDocumentFragment();
                        if (before) fragment.appendChild(document.createTextNode(before));
                        fragment.appendChild(span);
                        if (after) fragment.appendChild(document.createTextNode(after));
                        
                        node.parentNode.replaceChild(fragment, node);
                    }
                });
            }
            
            // 折叠/展开全部功能
            let allCollapsed = false;
            function toggleAllGroups() {
                const groups = document.querySelectorAll('.word-group');
                allCollapsed = !allCollapsed;
                
                groups.forEach(group => {
                    if (allCollapsed) {
                        group.classList.add('collapsed');
                    } else {
                        group.classList.remove('collapsed');
                    }
                });
                
                // 更新按钮文字
                const btn = event.target.closest('.toolbar-btn');
                btn.innerHTML = allCollapsed ? '<span>📂</span> 展开' : '<span>📂</span> 折叠';
            }
            
            // 暗色模式切换
            function toggleDarkMode() {
                document.body.classList.toggle('dark-mode');
                const isDark = document.body.classList.contains('dark-mode');
                localStorage.setItem('darkMode', isDark);
                updateDarkModeButton();
            }
            
            function updateDarkModeButton() {
                const isDark = document.body.classList.contains('dark-mode');
                const btn = document.querySelector('.toolbar-btn:nth-last-child(2)');
                if (btn) {
                    btn.innerHTML = isDark ? '<span class="dark-mode-icon">☀️</span> 亮色' : '<span class="dark-mode-icon">🌙</span> 暗色';
                    btn.classList.toggle('active', isDark);
                }
            }
            
            // 自动刷新功能
            let autoRefreshEnabled = false;
            let autoRefreshInterval = null;
            let countdownInterval = null;
            let countdownSeconds = 300; // 5分钟刷新一次
            
            function toggleAutoRefresh() {
                autoRefreshEnabled = !autoRefreshEnabled;
                const btn = document.getElementById('autoRefreshBtn');
                const countdownEl = document.getElementById('refreshCountdown');
                const textEl = document.getElementById('autoRefreshText');
                
                if (autoRefreshEnabled) {
                    btn.classList.add('auto-refresh-active');
                    textEl.textContent = '停止刷新';
                    countdownEl.classList.remove('hidden');
                    startAutoRefresh();
                } else {
                    btn.classList.remove('auto-refresh-active');
                    textEl.textContent = '自动刷新';
                    countdownEl.classList.add('hidden');
                    stopAutoRefresh();
                }
                
                // 保存偏好
                localStorage.setItem('autoRefresh', autoRefreshEnabled);
            }
            
            function startAutoRefresh() {
                countdownSeconds = 300;
                updateCountdown();
                
                countdownInterval = setInterval(() => {
                    countdownSeconds--;
                    updateCountdown();
                    
                    if (countdownSeconds <= 0) {
                        location.reload();
                    }
                }, 1000);
            }
            
            function stopAutoRefresh() {
                if (countdownInterval) {
                    clearInterval(countdownInterval);
                    countdownInterval = null;
                }
            }
            
            function updateCountdown() {
                const el = document.getElementById('countdown');
                if (el) {
                    const mins = Math.floor(countdownSeconds / 60);
                    const secs = countdownSeconds % 60;
                    el.textContent = mins > 0 ? `${mins}:${secs.toString().padStart(2, '0')}` : secs;
                }
            }
            
            // 初始化统计数据
            function initStats() {
                const totalNews = document.querySelector('.info-value')?.textContent?.match(/\\d+/) || ['--'];
                document.getElementById('statTotalNews').textContent = totalNews[0];
                
                // 计算热点新闻数
                const hotNews = document.querySelectorAll('.word-group .news-item').length;
                document.getElementById('statHotNews').textContent = hotNews;
                
                // 计算关键词组数
                const keywords = document.querySelectorAll('.word-group').length;
                document.getElementById('statKeywords').textContent = keywords;
                
                // 计算新增热点数
                const newItems = document.querySelectorAll('.new-section .new-item').length;
                document.getElementById('statNewItems').textContent = newItems || 0;
            }
            
            // 页面加载完成后初始化
            window.addEventListener('load', function() {
                initStats();
                initCharts();
                
                // 检查是否启用了自动刷新
                if (localStorage.getItem('autoRefresh') === 'true') {
                    toggleAutoRefresh();
                }
                
                // 初始化对话设置
                initChatSettings();
            });
            
            // ==================== 数据可视化图表 ====================
            
            let platformChart = null;
            let keywordChart = null;
            
            function initCharts() {
                // 从嵌入的数据中获取图表数据
                const platformData = window.chartData?.platform || {};
                const keywordData = window.chartData?.keywords || [];
                
                // 初始化平台分布饼图
                const platformCtx = document.getElementById('platformChart');
                if (platformCtx && Object.keys(platformData).length > 0) {
                    const labels = Object.keys(platformData);
                    const data = Object.values(platformData);
                    const colors = generateColors(labels.length);
                    
                    platformChart = new Chart(platformCtx, {
                        type: 'doughnut',
                        data: {
                            labels: labels,
                            datasets: [{
                                data: data,
                                backgroundColor: colors,
                                borderWidth: 0
                            }]
                        },
                        options: {
                            responsive: true,
                            maintainAspectRatio: false,
                            plugins: {
                                legend: {
                                    position: 'right',
                                    labels: {
                                        boxWidth: 12,
                                        padding: 8,
                                        font: { size: 11 },
                                        color: document.body.classList.contains('dark-mode') ? '#e5e7eb' : '#374151'
                                    }
                                }
                            }
                        }
                    });
                } else if (platformCtx) {
                    platformCtx.parentElement.innerHTML = '<div style="display:flex;align-items:center;justify-content:center;height:100%;color:#9ca3af;font-size:14px;">暂无数据</div>';
                }
                
                // 初始化关键词热度柱状图
                const keywordCtx = document.getElementById('keywordChart');
                if (keywordCtx && keywordData.length > 0) {
                    const labels = keywordData.map(k => k.word.length > 8 ? k.word.substring(0, 8) + '...' : k.word);
                    const data = keywordData.map(k => k.count);
                    
                    keywordChart = new Chart(keywordCtx, {
                        type: 'bar',
                        data: {
                            labels: labels,
                            datasets: [{
                                label: '热度',
                                data: data,
                                backgroundColor: 'rgba(79, 70, 229, 0.8)',
                                borderRadius: 4
                            }]
                        },
                        options: {
                            responsive: true,
                            maintainAspectRatio: false,
                            indexAxis: 'y',
                            plugins: {
                                legend: { display: false }
                            },
                            scales: {
                                x: {
                                    grid: { display: false },
                                    ticks: { 
                                        color: document.body.classList.contains('dark-mode') ? '#9ca3af' : '#6b7280'
                                    }
                                },
                                y: {
                                    grid: { display: false },
                                    ticks: { 
                                        color: document.body.classList.contains('dark-mode') ? '#e5e7eb' : '#374151',
                                        font: { size: 11 }
                                    }
                                }
                            }
                        }
                    });
                } else if (keywordCtx) {
                    keywordCtx.parentElement.innerHTML = '<div style="display:flex;align-items:center;justify-content:center;height:100%;color:#9ca3af;font-size:14px;">暂无数据</div>';
                }
            }
            
            function generateColors(count) {
                const baseColors = [
                    '#4f46e5', '#7c3aed', '#ec4899', '#f43f5e', '#f97316',
                    '#eab308', '#22c55e', '#14b8a6', '#06b6d4', '#3b82f6',
                    '#8b5cf6', '#d946ef', '#f472b6', '#fb923c', '#a3e635'
                ];
                const colors = [];
                for (let i = 0; i < count; i++) {
                    colors.push(baseColors[i % baseColors.length]);
                }
                return colors;
            }
            
            // ==================== AI 对话功能 ====================
            
            let chatHistory = [];
            let isWaitingResponse = false;
            
            // 切换对话窗口
            function toggleChatWindow() {
                const chatWindow = document.getElementById('chatWindow');
                chatWindow.classList.toggle('open');
                
                if (chatWindow.classList.contains('open')) {
                    document.getElementById('chatInput').focus();
                }
            }
            
            // 切换设置面板
            function toggleChatSettings() {
                const settings = document.getElementById('chatSettings');
                settings.classList.toggle('open');
            }
            
            // 初始化对话设置
            function initChatSettings() {
                const provider = localStorage.getItem('chatProvider') || 'deepseek';
                const apiKey = localStorage.getItem('chatApiKey') || '';
                const baseUrl = localStorage.getItem('chatBaseUrl') || '';
                const mcpUrl = localStorage.getItem('mcpServerUrl') || 'http://127.0.0.1:3333';
                
                document.getElementById('chatProvider').value = provider;
                document.getElementById('chatApiKey').value = apiKey;
                document.getElementById('chatBaseUrl').value = baseUrl;
                document.getElementById('mcpServerUrl').value = mcpUrl;
                
                // 监听提供商变化
                document.getElementById('chatProvider').addEventListener('change', function() {
                    const customGroup = document.getElementById('customBaseUrlGroup');
                    customGroup.style.display = this.value === 'custom' ? 'flex' : 'none';
                });
                
                // 触发一次变化检测
                if (provider === 'custom') {
                    document.getElementById('customBaseUrlGroup').style.display = 'flex';
                }
                
                // 如果有 API Key，更新欢迎消息
                if (apiKey) {
                    const messagesDiv = document.getElementById('chatMessages');
                    messagesDiv.innerHTML = `<div class="chat-message system">👋 欢迎回来！我是 TrendRadar AI 助手。有什么我可以帮你的？</div>`;
                }
            }
            
            // 保存对话设置
            function saveChatSettings() {
                const provider = document.getElementById('chatProvider').value;
                const apiKey = document.getElementById('chatApiKey').value;
                const baseUrl = document.getElementById('chatBaseUrl').value;
                const mcpUrl = document.getElementById('mcpServerUrl').value;
                
                localStorage.setItem('chatProvider', provider);
                localStorage.setItem('chatApiKey', apiKey);
                localStorage.setItem('chatBaseUrl', baseUrl);
                localStorage.setItem('mcpServerUrl', mcpUrl);
                
                toggleChatSettings();
                addChatMessage('system', '✅ 设置已保存');
            }
            
            // 清空对话历史
            function clearChatHistory() {
                chatHistory = [];
                const messagesDiv = document.getElementById('chatMessages');
                messagesDiv.innerHTML = `<div class="chat-message system">💬 对话已清空，可以开始新的对话了</div>`;
            }
            
            // 添加消息到对话框
            function addChatMessage(role, content) {
                const messagesDiv = document.getElementById('chatMessages');
                const messageDiv = document.createElement('div');
                messageDiv.className = `chat-message ${role}`;
                messageDiv.innerHTML = content.replace(/\\n/g, '<br>');
                messagesDiv.appendChild(messageDiv);
                messagesDiv.scrollTop = messagesDiv.scrollHeight;
                
                if (role !== 'system' && role !== 'loading') {
                    chatHistory.push({ role, content });
                }
            }
            
            // 显示加载动画
            function showLoadingMessage() {
                const messagesDiv = document.getElementById('chatMessages');
                const loadingDiv = document.createElement('div');
                loadingDiv.className = 'chat-message assistant loading';
                loadingDiv.id = 'loadingMessage';
                loadingDiv.innerHTML = '<span></span><span></span><span></span>';
                messagesDiv.appendChild(loadingDiv);
                messagesDiv.scrollTop = messagesDiv.scrollHeight;
            }
            
            // 移除加载动画
            function removeLoadingMessage() {
                const loading = document.getElementById('loadingMessage');
                if (loading) loading.remove();
            }
            
            // 处理键盘事件
            function handleChatKeypress(event) {
                if (event.key === 'Enter' && !event.shiftKey) {
                    event.preventDefault();
                    sendChatMessage();
                }
            }
            
            // 发送快捷消息
            function sendQuickMessage(message) {
                document.getElementById('chatInput').value = message;
                sendChatMessage();
            }
            
            // 发送对话消息
            async function sendChatMessage() {
                const input = document.getElementById('chatInput');
                const message = input.value.trim();
                
                if (!message || isWaitingResponse) return;
                
                // 添加用户消息
                addChatMessage('user', message);
                input.value = '';
                
                // 显示加载状态
                isWaitingResponse = true;
                document.getElementById('chatSendBtn').disabled = true;
                showLoadingMessage();
                
                try {
                    // 1. 先尝试使用 MCP 直接处理数据查询
                    const mcpResult = await processWithMCP(message);
                    if (mcpResult) {
                        removeLoadingMessage();
                        addChatMessage('assistant', mcpResult);
                        return;
                    }
                    
                    // 2. 尝试使用 MCP Server 的 AI 对话（复用后端配置）
                    try {
                        const mcpAiResult = await callMCPTool('chat_with_ai', { 
                            message: message,
                            include_context: true,
                            context_type: 'trending'
                        });
                        if (mcpAiResult && mcpAiResult.success && mcpAiResult.reply) {
                            removeLoadingMessage();
                            addChatMessage('assistant', mcpAiResult.reply);
                            return;
                        }
                        // 如果 MCP AI 返回错误，继续尝试本地配置
                        if (mcpAiResult && !mcpAiResult.success) {
                            console.log('MCP AI 未配置:', mcpAiResult.error);
                        }
                    } catch (mcpAiError) {
                        console.log('MCP AI 调用失败，尝试本地配置:', mcpAiError);
                    }
                    
                    // 3. MCP AI 不可用，检查本地 API Key
                    const apiKey = localStorage.getItem('chatApiKey');
                    if (!apiKey) {
                        removeLoadingMessage();
                        addChatMessage('system', '⚠️ AI 未配置。\\n\\n方式1: 在 docker/.env 中设置 AI_API_KEY（推荐）\\n方式2: 点击右上角 ⚙️ 在此配置 API Key');
                        return;
                    }
                    
                    // 4. 使用本地配置的 AI API
                    const newsContext = await getNewsContext();
                    const response = await callAIAPI(message, newsContext);
                    
                    removeLoadingMessage();
                    addChatMessage('assistant', response);
                    
                } catch (error) {
                    removeLoadingMessage();
                    addChatMessage('system', `❌ 错误: ${error.message}`);
                } finally {
                    isWaitingResponse = false;
                    document.getElementById('chatSendBtn').disabled = false;
                }
            }
            
            // 获取新闻上下文
            async function getNewsContext() {
                // 先尝试从 MCP Server 获取最新数据
                const mcpUrl = localStorage.getItem('mcpServerUrl') || 'http://127.0.0.1:3333';
                try {
                    const mcpData = await callMCPTool('get_trending_topics', { top_n: 15 });
                    if (mcpData && mcpData.topics) {
                        return `当前热点话题（来自 MCP Server）:\\n` +
                               mcpData.topics.map(t => `- ${t.keyword}: ${t.frequency} 条相关新闻`).join('\\n');
                    }
                } catch (e) {
                    console.log('MCP Server 不可用，使用页面数据:', e.message);
                }
                
                // 回退：从当前页面提取新闻数据
                const newsItems = [];
                document.querySelectorAll('.word-group').forEach(group => {
                    const keyword = group.querySelector('.word-name')?.textContent || '';
                    group.querySelectorAll('.news-item').forEach(item => {
                        const title = item.querySelector('.news-title')?.textContent || '';
                        const source = item.querySelector('.source-name')?.textContent || '';
                        newsItems.push({ keyword, title, source });
                    });
                });
                
                return `当前页面包含 ${newsItems.length} 条热点新闻:\\n` +
                       newsItems.slice(0, 20).map(n => `- [${n.keyword}] ${n.title}`).join('\\n');
            }
            
            // 调用 MCP Server 工具
            async function callMCPTool(toolName, params = {}) {
                const mcpUrl = localStorage.getItem('mcpServerUrl') || 'http://127.0.0.1:3333';
                
                try {
                    const response = await fetch(`${mcpUrl}/mcp`, {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify({
                            jsonrpc: '2.0',
                            method: 'tools/call',
                            params: {
                                name: toolName,
                                arguments: params
                            },
                            id: Date.now()
                        })
                    });
                    
                    if (!response.ok) {
                        throw new Error(`MCP 请求失败: ${response.status}`);
                    }
                    
                    const data = await response.json();
                    if (data.error) {
                        throw new Error(data.error.message);
                    }
                    
                    // 解析结果
                    const content = data.result?.content?.[0]?.text;
                    return content ? JSON.parse(content) : null;
                } catch (error) {
                    console.error('MCP 调用失败:', error);
                    throw error;
                }
            }
            
            // 智能意图识别和 MCP 工具调用
            async function processWithMCP(message) {
                const lowerMsg = message.toLowerCase();
                
                // 1. 搜索意图
                if (lowerMsg.includes('搜索') || lowerMsg.includes('查找') || lowerMsg.includes('找')) {
                    const keyword = message.replace(/搜索|查找|找|关于|的新闻|新闻/g, '').trim();
                    if (keyword) {
                        try {
                            const result = await callMCPTool('search_news', { 
                                query: keyword, 
                                limit: 10 
                            });
                            if (result && result.data) {
                                return `🔍 找到 ${result.summary?.total || 0} 条关于"${keyword}"的新闻:\\n\\n` +
                                       result.data.slice(0, 10).map((n, i) => 
                                           `${i+1}. [${n.platform_name}] ${n.title}`
                                       ).join('\\n');
                            }
                        } catch (e) {
                            return null;
                        }
                    }
                }
                
                // 2. 热点/趋势意图
                if (lowerMsg.includes('热点') || lowerMsg.includes('趋势') || lowerMsg.includes('热门') || lowerMsg.includes('今日')) {
                    try {
                        const result = await callMCPTool('get_trending_topics', { top_n: 10 });
                        if (result && result.topics) {
                            return `📊 当前热门话题 TOP 10:\\n\\n` +
                                   result.topics.map((t, i) => {
                                       const icon = i < 3 ? '🔥' : (i < 6 ? '📈' : '📌');
                                       return `${icon} ${i+1}. ${t.keyword} - ${t.frequency} 条相关新闻`;
                                   }).join('\\n');
                        }
                    } catch (e) {
                        return null;
                    }
                }
                
                // 3. RSS 订阅意图
                if (lowerMsg.includes('rss') || lowerMsg.includes('订阅')) {
                    try {
                        const result = await callMCPTool('get_latest_rss', { days: 1, limit: 10 });
                        if (result && result.data) {
                            return `📰 最新 RSS 订阅内容:\\n\\n` +
                                   result.data.slice(0, 10).map((r, i) => 
                                       `${i+1}. [${r.feed_name}] ${r.title}`
                                   ).join('\\n');
                        }
                    } catch (e) {
                        return null;
                    }
                }
                
                // 4. 深度分析意图
                if (lowerMsg.includes('分析') && (lowerMsg.includes('趋势') || lowerMsg.includes('话题'))) {
                    // 提取话题关键词
                    const topicMatch = message.match(/分析[""'']?(.+?)[""'']?的?趋势/);
                    const topic = topicMatch ? topicMatch[1] : '';
                    
                    if (topic) {
                        try {
                            const result = await callMCPTool('analyze_topic_trend', { 
                                topic: topic,
                                analysis_type: 'trend'
                            });
                            if (result && result.trend_analysis) {
                                const ta = result.trend_analysis;
                                return `📈 "${topic}" 趋势分析:\\n\\n` +
                                       `• 数据周期: ${ta.date_range?.start || '今天'} 至 ${ta.date_range?.end || '今天'}\\n` +
                                       `• 相关新闻: ${ta.total_news || 0} 条\\n` +
                                       `• 趋势方向: ${ta.trend_direction || '稳定'}\\n` +
                                       (ta.daily_counts ? `• 每日分布: ${JSON.stringify(ta.daily_counts)}` : '');
                            }
                        } catch (e) {
                            return null;
                        }
                    }
                }
                
                // 5. 情感分析意图
                if (lowerMsg.includes('情感') || lowerMsg.includes('舆情') || lowerMsg.includes('态度')) {
                    const topicMatch = message.match(/[关于对]?[""'']?(.+?)[""'']?的?[情感舆情态度]/);
                    const topic = topicMatch ? topicMatch[1].replace(/[的关于对]/g, '') : '';
                    
                    if (topic) {
                        try {
                            const result = await callMCPTool('analyze_sentiment', { 
                                topic: topic,
                                limit: 20
                            });
                            if (result && result.sentiment_analysis) {
                                const sa = result.sentiment_analysis;
                                return `🎭 "${topic}" 情感分析:\\n\\n` +
                                       `• 正面: ${sa.positive_ratio || 0}%\\n` +
                                       `• 中性: ${sa.neutral_ratio || 0}%\\n` +
                                       `• 负面: ${sa.negative_ratio || 0}%\\n` +
                                       `• 样本量: ${sa.total_analyzed || 0} 条新闻`;
                            }
                        } catch (e) {
                            return null;
                        }
                    }
                }
                
                // 6. 平台对比意图
                if (lowerMsg.includes('平台') && (lowerMsg.includes('对比') || lowerMsg.includes('比较'))) {
                    try {
                        const result = await callMCPTool('analyze_data_insights', { 
                            insight_type: 'platform_activity'
                        });
                        if (result && result.platform_stats) {
                            const stats = result.platform_stats;
                            return `📱 平台活跃度对比:\\n\\n` +
                                   Object.entries(stats)
                                       .sort((a, b) => b[1].news_count - a[1].news_count)
                                       .slice(0, 8)
                                       .map(([ name, data], i) => 
                                           `${i+1}. ${name}: ${data.news_count} 条新闻`
                                       ).join('\\n');
                        }
                    } catch (e) {
                        return null;
                    }
                }
                
                // 7. 系统状态意图
                if (lowerMsg.includes('状态') || lowerMsg.includes('系统') || lowerMsg.includes('版本')) {
                    try {
                        const result = await callMCPTool('get_system_status', {});
                        if (result && result.system) {
                            return `⚙️ 系统状态:\\n\\n` +
                                   `• 版本: ${result.system.version || '未知'}\\n` +
                                   `• 数据存储: ${result.data?.total_storage || '未知'}\\n` +
                                   `• 最新数据: ${result.data?.latest_record || '无'}\\n` +
                                   `• 健康状态: ${result.health || '正常'}`;
                        }
                    } catch (e) {
                        return null;
                    }
                }
                
                // 8. 导出数据意图
                if (lowerMsg.includes('导出') || lowerMsg.includes('下载')) {
                    return `📥 数据导出功能:\\n\\n` +
                           `你可以使用以下命令导出数据：\\n\\n` +
                           `• "导出今日新闻" - 导出今天的新闻数据\\n` +
                           `• "导出 RSS 数据" - 导出 RSS 订阅内容\\n\\n` +
                           `提示：导出功能需要 MCP Server 支持，请确保服务已启动。`;
                }
                
                // 9. 帮助意图
                if (lowerMsg.includes('帮助') || lowerMsg.includes('help') || lowerMsg === '?') {
                    return `🤖 TrendRadar AI 助手功能：\\n\\n` +
                           `📊 **数据查询**\\n` +
                           `• 今日热点 - 查看当前热门话题\\n` +
                           `• 搜索 [关键词] - 搜索相关新闻\\n` +
                           `• RSS 订阅 - 查看最新订阅内容\\n\\n` +
                           `📈 **深度分析**\\n` +
                           `• 分析 [话题] 的趋势 - 话题趋势分析\\n` +
                           `• [话题] 的情感/舆情 - 情感倾向分析\\n` +
                           `• 平台对比 - 各平台活跃度对比\\n\\n` +
                           `⚙️ **系统功能**\\n` +
                           `• 系统状态 - 查看系统运行状态\\n` +
                           `• 帮助 - 显示此帮助信息`;
                }
                
                return null; // 无法处理，交给 AI
            }
            
            // 调用 AI API
            async function callAIAPI(message, context) {
                const provider = localStorage.getItem('chatProvider') || 'deepseek';
                const apiKey = localStorage.getItem('chatApiKey');
                const customBaseUrl = localStorage.getItem('chatBaseUrl');
                
                // 构建 API 配置
                let baseUrl, model;
                switch (provider) {
                    case 'deepseek':
                        baseUrl = 'https://api.deepseek.com/v1';
                        model = 'deepseek-chat';
                        break;
                    case 'openai':
                        baseUrl = 'https://api.openai.com/v1';
                        model = 'gpt-4o-mini';
                        break;
                    case 'anthropic':
                        baseUrl = 'https://api.anthropic.com/v1';
                        model = 'claude-3-haiku-20240307';
                        break;
                    case 'custom':
                        baseUrl = customBaseUrl || 'https://api.openai.com/v1';
                        model = 'gpt-4o-mini';
                        break;
                    default:
                        baseUrl = 'https://api.deepseek.com/v1';
                        model = 'deepseek-chat';
                }
                
                // 构建系统提示词
                const systemPrompt = `你是 TrendRadar AI 助手，专门帮助用户分析热点新闻。你的能力包括：
1. 分析新闻趋势和热度变化
2. 总结重要新闻要点
3. 识别新闻之间的关联
4. 提供投资/关注建议
5. 回答用户关于新闻的问题

当前新闻数据：
${context}

请用简洁专业的中文回答用户问题。如果涉及投资建议，请加上风险提示。`;
                
                // 构建消息
                const messages = [
                    { role: 'system', content: systemPrompt },
                    ...chatHistory.slice(-10).map(m => ({
                        role: m.role === 'user' ? 'user' : 'assistant',
                        content: m.content
                    })),
                    { role: 'user', content: message }
                ];
                
                // 发送请求
                const response = await fetch(`${baseUrl}/chat/completions`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'Authorization': `Bearer ${apiKey}`
                    },
                    body: JSON.stringify({
                        model: model,
                        messages: messages,
                        temperature: 0.7,
                        max_tokens: 1000
                    })
                });
                
                if (!response.ok) {
                    const error = await response.json().catch(() => ({}));
                    throw new Error(error.error?.message || `API 请求失败: ${response.status}`);
                }
                
                const data = await response.json();
                return data.choices?.[0]?.message?.content || '无法获取回复';
            }
            
            // 图表数据（由服务端注入）
            window.chartData = {
                platform: """ + platform_data_json + """,
                keywords: """ + keyword_data_json + """
            };
        </script>
    </body>
    </html>
    """

    return html
