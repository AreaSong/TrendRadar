"""
数据导出工具

实现数据导出为 CSV、JSON 等格式的功能。
"""

import csv
import json
import io
from typing import Dict, List, Optional, Union
from datetime import datetime

from ..services.data_service import DataService
from ..utils.validators import (
    validate_platforms,
    validate_date_range,
    validate_limit
)
from ..utils.errors import MCPError


class ExportTools:
    """数据导出工具类"""

    def __init__(self, project_root: str = None):
        """
        初始化数据导出工具

        Args:
            project_root: 项目根目录
        """
        self.data_service = DataService(project_root)

    def export_news_csv(
        self,
        date_range: Optional[Union[Dict, str]] = None,
        platforms: Optional[List[str]] = None,
        limit: Optional[int] = None,
        include_url: bool = True
    ) -> Dict:
        """
        导出新闻数据为 CSV 格式

        Args:
            date_range: 日期范围，格式: {"start": "YYYY-MM-DD", "end": "YYYY-MM-DD"}
                       或相对日期如 "今天"、"最近7天"
            platforms: 平台ID列表，如 ['zhihu', 'weibo']
            limit: 返回条数限制
            include_url: 是否包含URL链接，默认True

        Returns:
            包含 CSV 内容的字典

        Example:
            >>> tools = ExportTools()
            >>> result = tools.export_news_csv(
            ...     date_range={"start": "2025-01-01", "end": "2025-01-07"},
            ...     platforms=['zhihu', 'weibo']
            ... )
            >>> print(result['data']['csv_content'][:100])
        """
        try:
            # 参数验证
            date_range_tuple = validate_date_range(date_range)
            platforms = validate_platforms(platforms)
            if limit is not None:
                limit = validate_limit(limit, default=1000)

            # 获取数据
            news_list = self.data_service.get_news_for_export(
                date_range=date_range_tuple,
                platforms=platforms,
                limit=limit,
                include_url=include_url
            )

            if not news_list:
                return {
                    "success": True,
                    "summary": {
                        "description": "没有找到符合条件的数据",
                        "total": 0,
                        "format": "csv"
                    },
                    "data": {
                        "csv_content": "",
                        "row_count": 0
                    }
                }

            # 生成 CSV
            output = io.StringIO()
            fieldnames = ['date', 'time', 'platform', 'title', 'rank', 'hotness']
            if include_url:
                fieldnames.append('url')

            writer = csv.DictWriter(output, fieldnames=fieldnames, quoting=csv.QUOTE_ALL)
            writer.writeheader()

            for item in news_list:
                row = {
                    'date': item.get('date', ''),
                    'time': item.get('time', ''),
                    'platform': item.get('platform', ''),
                    'title': item.get('title', ''),
                    'rank': item.get('rank', ''),
                    'hotness': item.get('hotness', '')
                }
                if include_url:
                    row['url'] = item.get('url', '')
                writer.writerow(row)

            csv_content = output.getvalue()
            output.close()

            return {
                "success": True,
                "summary": {
                    "description": f"成功导出 {len(news_list)} 条新闻数据为 CSV 格式",
                    "total": len(news_list),
                    "format": "csv",
                    "date_range": date_range,
                    "platforms": platforms or "全部平台"
                },
                "data": {
                    "csv_content": csv_content,
                    "row_count": len(news_list),
                    "columns": fieldnames
                }
            }

        except MCPError as e:
            return {
                "success": False,
                "error": e.to_dict()
            }
        except Exception as e:
            return {
                "success": False,
                "error": {
                    "code": "EXPORT_ERROR",
                    "message": f"导出 CSV 失败: {str(e)}"
                }
            }

    def export_news_json(
        self,
        date_range: Optional[Union[Dict, str]] = None,
        platforms: Optional[List[str]] = None,
        limit: Optional[int] = None,
        include_url: bool = True,
        pretty: bool = True
    ) -> Dict:
        """
        导出新闻数据为 JSON 格式

        Args:
            date_range: 日期范围，格式: {"start": "YYYY-MM-DD", "end": "YYYY-MM-DD"}
                       或相对日期如 "今天"、"最近7天"
            platforms: 平台ID列表，如 ['zhihu', 'weibo']
            limit: 返回条数限制
            include_url: 是否包含URL链接，默认True
            pretty: 是否格式化输出（缩进），默认True

        Returns:
            包含 JSON 内容的字典

        Example:
            >>> tools = ExportTools()
            >>> result = tools.export_news_json(
            ...     date_range="最近3天",
            ...     platforms=['zhihu']
            ... )
            >>> print(result['data']['json_content'][:100])
        """
        try:
            # 参数验证
            date_range_tuple = validate_date_range(date_range)
            platforms = validate_platforms(platforms)
            if limit is not None:
                limit = validate_limit(limit, default=1000)

            # 获取数据
            news_list = self.data_service.get_news_for_export(
                date_range=date_range_tuple,
                platforms=platforms,
                limit=limit,
                include_url=include_url
            )

            if not news_list:
                return {
                    "success": True,
                    "summary": {
                        "description": "没有找到符合条件的数据",
                        "total": 0,
                        "format": "json"
                    },
                    "data": {
                        "json_content": "[]",
                        "item_count": 0
                    }
                }

            # 构建导出数据结构
            export_data = {
                "metadata": {
                    "exported_at": datetime.now().isoformat(),
                    "total_items": len(news_list),
                    "date_range": date_range,
                    "platforms": platforms or "all"
                },
                "news": news_list
            }

            # 生成 JSON
            if pretty:
                json_content = json.dumps(export_data, ensure_ascii=False, indent=2)
            else:
                json_content = json.dumps(export_data, ensure_ascii=False)

            return {
                "success": True,
                "summary": {
                    "description": f"成功导出 {len(news_list)} 条新闻数据为 JSON 格式",
                    "total": len(news_list),
                    "format": "json",
                    "date_range": date_range,
                    "platforms": platforms or "全部平台"
                },
                "data": {
                    "json_content": json_content,
                    "item_count": len(news_list)
                }
            }

        except MCPError as e:
            return {
                "success": False,
                "error": e.to_dict()
            }
        except Exception as e:
            return {
                "success": False,
                "error": {
                    "code": "EXPORT_ERROR",
                    "message": f"导出 JSON 失败: {str(e)}"
                }
            }

    def export_rss_csv(
        self,
        feeds: Optional[List[str]] = None,
        days: int = 7,
        limit: Optional[int] = None,
        include_summary: bool = False
    ) -> Dict:
        """
        导出 RSS 数据为 CSV 格式

        Args:
            feeds: RSS 源 ID 列表
            days: 导出最近 N 天的数据，默认 7 天
            limit: 返回条数限制
            include_summary: 是否包含摘要

        Returns:
            包含 CSV 内容的字典
        """
        try:
            if limit is not None:
                limit = validate_limit(limit, default=500)

            if days < 1 or days > 30:
                days = 7

            # 获取数据
            rss_list = self.data_service.get_rss_for_export(
                feeds=feeds,
                days=days,
                limit=limit,
                include_summary=include_summary
            )

            if not rss_list:
                return {
                    "success": True,
                    "summary": {
                        "description": "没有找到符合条件的 RSS 数据",
                        "total": 0,
                        "format": "csv"
                    },
                    "data": {
                        "csv_content": "",
                        "row_count": 0
                    }
                }

            # 生成 CSV
            output = io.StringIO()
            fieldnames = ['date', 'feed_id', 'feed_name', 'title', 'url', 'published']
            if include_summary:
                fieldnames.append('summary')

            writer = csv.DictWriter(output, fieldnames=fieldnames, quoting=csv.QUOTE_ALL)
            writer.writeheader()

            for item in rss_list:
                row = {
                    'date': item.get('date', ''),
                    'feed_id': item.get('feed_id', ''),
                    'feed_name': item.get('feed_name', ''),
                    'title': item.get('title', ''),
                    'url': item.get('url', ''),
                    'published': item.get('published', '')
                }
                if include_summary:
                    row['summary'] = item.get('summary', '')
                writer.writerow(row)

            csv_content = output.getvalue()
            output.close()

            return {
                "success": True,
                "summary": {
                    "description": f"成功导出 {len(rss_list)} 条 RSS 数据为 CSV 格式",
                    "total": len(rss_list),
                    "format": "csv",
                    "days": days,
                    "feeds": feeds or "全部订阅源"
                },
                "data": {
                    "csv_content": csv_content,
                    "row_count": len(rss_list),
                    "columns": fieldnames
                }
            }

        except MCPError as e:
            return {
                "success": False,
                "error": e.to_dict()
            }
        except Exception as e:
            return {
                "success": False,
                "error": {
                    "code": "EXPORT_ERROR",
                    "message": f"导出 RSS CSV 失败: {str(e)}"
                }
            }

    def export_rss_json(
        self,
        feeds: Optional[List[str]] = None,
        days: int = 7,
        limit: Optional[int] = None,
        include_summary: bool = False,
        pretty: bool = True
    ) -> Dict:
        """
        导出 RSS 数据为 JSON 格式

        Args:
            feeds: RSS 源 ID 列表
            days: 导出最近 N 天的数据，默认 7 天
            limit: 返回条数限制
            include_summary: 是否包含摘要
            pretty: 是否格式化输出

        Returns:
            包含 JSON 内容的字典
        """
        try:
            if limit is not None:
                limit = validate_limit(limit, default=500)

            if days < 1 or days > 30:
                days = 7

            # 获取数据
            rss_list = self.data_service.get_rss_for_export(
                feeds=feeds,
                days=days,
                limit=limit,
                include_summary=include_summary
            )

            if not rss_list:
                return {
                    "success": True,
                    "summary": {
                        "description": "没有找到符合条件的 RSS 数据",
                        "total": 0,
                        "format": "json"
                    },
                    "data": {
                        "json_content": "[]",
                        "item_count": 0
                    }
                }

            # 构建导出数据结构
            export_data = {
                "metadata": {
                    "exported_at": datetime.now().isoformat(),
                    "total_items": len(rss_list),
                    "days": days,
                    "feeds": feeds or "all"
                },
                "rss_items": rss_list
            }

            # 生成 JSON
            if pretty:
                json_content = json.dumps(export_data, ensure_ascii=False, indent=2)
            else:
                json_content = json.dumps(export_data, ensure_ascii=False)

            return {
                "success": True,
                "summary": {
                    "description": f"成功导出 {len(rss_list)} 条 RSS 数据为 JSON 格式",
                    "total": len(rss_list),
                    "format": "json",
                    "days": days,
                    "feeds": feeds or "全部订阅源"
                },
                "data": {
                    "json_content": json_content,
                    "item_count": len(rss_list)
                }
            }

        except MCPError as e:
            return {
                "success": False,
                "error": e.to_dict()
            }
        except Exception as e:
            return {
                "success": False,
                "error": {
                    "code": "EXPORT_ERROR",
                    "message": f"导出 RSS JSON 失败: {str(e)}"
                }
            }
