"""
TrendRadar REST API 模块

提供 RESTful API 接口，复用 MCP Server 的工具实例。
"""

import asyncio
from typing import Optional, List, Dict, Any
from datetime import datetime

from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
import io

# 延迟导入以避免循环依赖
_tools_cache = None


def _get_tools():
    """获取工具实例（延迟导入）"""
    global _tools_cache
    if _tools_cache is None:
        from .server import _get_tools as get_mcp_tools
        _tools_cache = get_mcp_tools()
    return _tools_cache


# 创建 FastAPI 应用
app = FastAPI(
    title="TrendRadar REST API",
    description="热点新闻聚合与分析工具的 RESTful API",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json"
)

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==================== 健康检查 ====================

@app.get("/api/v1/health", tags=["系统"])
async def health_check():
    """健康检查端点"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "TrendRadar REST API"
    }


# ==================== 新闻数据 ====================

@app.get("/api/v1/news/latest", tags=["新闻"])
async def get_latest_news(
    platforms: Optional[str] = Query(None, description="平台ID，逗号分隔，如: zhihu,weibo"),
    limit: int = Query(50, ge=1, le=200, description="返回条数限制"),
    include_url: bool = Query(False, description="是否包含URL")
):
    """
    获取最新新闻
    
    返回今日最新的热榜新闻数据。
    """
    try:
        tools = _get_tools()
        platforms_list = platforms.split(',') if platforms else None
        result = await asyncio.to_thread(
            tools['data'].get_latest_news,
            platforms=platforms_list,
            limit=limit,
            include_url=include_url
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/news/search", tags=["新闻"])
async def search_news(
    query: str = Query(..., min_length=1, description="搜索关键词"),
    date_range: Optional[str] = Query(None, description="日期范围，如: 今天, 最近7天"),
    platforms: Optional[str] = Query(None, description="平台ID，逗号分隔"),
    limit: int = Query(50, ge=1, le=200, description="返回条数限制")
):
    """
    搜索新闻
    
    根据关键词搜索历史新闻数据。
    """
    try:
        tools = _get_tools()
        platforms_list = platforms.split(',') if platforms else None
        result = await asyncio.to_thread(
            tools['search'].search_news_unified,
            query=query,
            date_range=date_range,
            platforms=platforms_list,
            limit=limit
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/news/by-date", tags=["新闻"])
async def get_news_by_date(
    date: str = Query(..., description="日期，格式: YYYY-MM-DD 或 今天/昨天"),
    platforms: Optional[str] = Query(None, description="平台ID，逗号分隔"),
    limit: int = Query(100, ge=1, le=500, description="返回条数限制")
):
    """
    按日期获取新闻
    
    获取指定日期的热榜新闻数据。
    """
    try:
        tools = _get_tools()
        platforms_list = platforms.split(',') if platforms else None
        result = await asyncio.to_thread(
            tools['data'].get_news_by_date,
            date=date,
            platforms=platforms_list,
            limit=limit
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 热门话题 ====================

@app.get("/api/v1/topics/trending", tags=["话题"])
async def get_trending_topics(
    top_n: int = Query(20, ge=1, le=50, description="返回TOP N话题"),
    date_range: Optional[str] = Query(None, description="日期范围")
):
    """
    获取热门话题
    
    返回当前热度最高的话题关键词。
    """
    try:
        tools = _get_tools()
        result = await asyncio.to_thread(
            tools['data'].get_trending_topics,
            top_n=top_n,
            date_range=date_range
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/topics/analyze", tags=["话题"])
async def analyze_topic(
    topic: str = Query(..., min_length=1, description="话题关键词"),
    analysis_type: str = Query("trend", description="分析类型: trend/sentiment/related")
):
    """
    分析话题趋势
    
    对指定话题进行深度分析。
    """
    try:
        tools = _get_tools()
        result = await asyncio.to_thread(
            tools['analytics'].analyze_topic_trend_unified,
            topic=topic,
            analysis_type=analysis_type
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== RSS ====================

@app.get("/api/v1/rss/latest", tags=["RSS"])
async def get_latest_rss(
    feeds: Optional[str] = Query(None, description="RSS源ID，逗号分隔"),
    days: int = Query(1, ge=1, le=7, description="最近N天"),
    limit: int = Query(50, ge=1, le=200, description="返回条数限制")
):
    """
    获取最新RSS内容
    
    返回最新的RSS订阅内容。
    """
    try:
        tools = _get_tools()
        feeds_list = feeds.split(',') if feeds else None
        result = await asyncio.to_thread(
            tools['data'].get_latest_rss,
            feeds=feeds_list,
            days=days,
            limit=limit
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/rss/search", tags=["RSS"])
async def search_rss(
    query: str = Query(..., min_length=1, description="搜索关键词"),
    feeds: Optional[str] = Query(None, description="RSS源ID，逗号分隔"),
    days: int = Query(7, ge=1, le=30, description="搜索范围天数"),
    limit: int = Query(50, ge=1, le=200, description="返回条数限制")
):
    """
    搜索RSS内容
    
    根据关键词搜索RSS订阅内容。
    """
    try:
        tools = _get_tools()
        feeds_list = feeds.split(',') if feeds else None
        result = await asyncio.to_thread(
            tools['data'].search_rss,
            query=query,
            feeds=feeds_list,
            days=days,
            limit=limit
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/rss/feeds", tags=["RSS"])
async def get_rss_feeds_status():
    """
    获取RSS源状态
    
    返回所有配置的RSS源及其状态。
    """
    try:
        tools = _get_tools()
        result = await asyncio.to_thread(
            tools['data'].get_rss_feeds_status
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 统计分析 ====================

@app.get("/api/v1/stats/platform", tags=["统计"])
async def get_platform_stats(
    date_range: Optional[str] = Query(None, description="日期范围")
):
    """
    平台统计
    
    返回各平台的新闻数量统计。
    """
    try:
        tools = _get_tools()
        result = await asyncio.to_thread(
            tools['analytics'].analyze_data_insights_unified,
            insight_type="platform_compare",
            date_range=date_range
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/stats/keywords", tags=["统计"])
async def get_keyword_stats(
    top_n: int = Query(20, ge=1, le=50, description="返回TOP N关键词"),
    date_range: Optional[str] = Query(None, description="日期范围")
):
    """
    关键词统计
    
    返回热门关键词的统计数据。
    """
    try:
        tools = _get_tools()
        result = await asyncio.to_thread(
            tools['data'].get_trending_topics,
            top_n=top_n,
            date_range=date_range
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/stats/insights", tags=["统计"])
async def get_data_insights(
    insight_type: str = Query("platform_compare", description="洞察类型: platform_compare/keyword_cooccurrence/time_distribution"),
    date_range: Optional[str] = Query(None, description="日期范围")
):
    """
    数据洞察
    
    返回多维度的数据分析洞察。
    """
    try:
        tools = _get_tools()
        result = await asyncio.to_thread(
            tools['analytics'].analyze_data_insights_unified,
            insight_type=insight_type,
            date_range=date_range
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 数据导出 ====================

@app.get("/api/v1/export/news/csv", tags=["导出"])
async def export_news_csv(
    date_range: Optional[str] = Query(None, description="日期范围"),
    platforms: Optional[str] = Query(None, description="平台ID，逗号分隔"),
    limit: int = Query(1000, ge=1, le=5000, description="导出条数限制")
):
    """
    导出新闻CSV
    
    将新闻数据导出为CSV格式。
    """
    try:
        tools = _get_tools()
        platforms_list = platforms.split(',') if platforms else None
        result = await asyncio.to_thread(
            tools['export'].export_news_csv,
            date_range=date_range,
            platforms=platforms_list,
            limit=limit
        )
        
        if result.get("success") and result.get("data", {}).get("csv_content"):
            csv_content = result["data"]["csv_content"]
            return StreamingResponse(
                io.StringIO(csv_content),
                media_type="text/csv",
                headers={
                    "Content-Disposition": f"attachment; filename=news_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
                }
            )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/export/news/json", tags=["导出"])
async def export_news_json(
    date_range: Optional[str] = Query(None, description="日期范围"),
    platforms: Optional[str] = Query(None, description="平台ID，逗号分隔"),
    limit: int = Query(1000, ge=1, le=5000, description="导出条数限制")
):
    """
    导出新闻JSON
    
    将新闻数据导出为JSON格式。
    """
    try:
        tools = _get_tools()
        platforms_list = platforms.split(',') if platforms else None
        result = await asyncio.to_thread(
            tools['export'].export_news_json,
            date_range=date_range,
            platforms=platforms_list,
            limit=limit
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/export/rss/csv", tags=["导出"])
async def export_rss_csv(
    feeds: Optional[str] = Query(None, description="RSS源ID，逗号分隔"),
    days: int = Query(7, ge=1, le=30, description="导出天数"),
    limit: int = Query(500, ge=1, le=2000, description="导出条数限制")
):
    """
    导出RSS CSV
    
    将RSS数据导出为CSV格式。
    """
    try:
        tools = _get_tools()
        feeds_list = feeds.split(',') if feeds else None
        result = await asyncio.to_thread(
            tools['export'].export_rss_csv,
            feeds=feeds_list,
            days=days,
            limit=limit
        )
        
        if result.get("success") and result.get("data", {}).get("csv_content"):
            csv_content = result["data"]["csv_content"]
            return StreamingResponse(
                io.StringIO(csv_content),
                media_type="text/csv",
                headers={
                    "Content-Disposition": f"attachment; filename=rss_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
                }
            )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 系统管理 ====================

@app.get("/api/v1/system/status", tags=["系统"])
async def get_system_status():
    """
    系统状态
    
    返回系统运行状态和配置信息。
    """
    try:
        tools = _get_tools()
        result = await asyncio.to_thread(
            tools['system'].get_system_status
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/system/config", tags=["系统"])
async def get_current_config():
    """
    当前配置
    
    返回当前的系统配置信息。
    """
    try:
        tools = _get_tools()
        result = await asyncio.to_thread(
            tools['config'].get_current_config
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/system/dates", tags=["系统"])
async def list_available_dates(
    source: str = Query("local", description="数据源: local/remote")
):
    """
    可用日期列表
    
    返回本地或远程存储中可用的数据日期。
    """
    try:
        tools = _get_tools()
        result = await asyncio.to_thread(
            tools['storage'].list_available_dates,
            source=source
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def run_rest_api(host: str = "0.0.0.0", port: int = 8000):
    """启动 REST API 服务器"""
    import uvicorn
    print(f"\n{'=' * 60}")
    print("TrendRadar REST API 启动中...")
    print(f"{'=' * 60}")
    print(f"\n  API 文档: http://{host}:{port}/api/docs")
    print(f"  ReDoc:    http://{host}:{port}/api/redoc")
    print(f"  健康检查: http://{host}:{port}/api/v1/health")
    print(f"\n{'=' * 60}\n")
    
    uvicorn.run(app, host=host, port=port, log_level="info")


if __name__ == "__main__":
    run_rest_api()
