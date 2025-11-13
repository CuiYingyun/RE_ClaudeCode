#!/usr/bin/env python3
"""
mitmproxy addon: 实时聚合 SSE 响应中的 content_block_delta 事件
使用方法: mitmweb -s sse_aggregator_addon.py
"""

import json
from collections import defaultdict
from mitmproxy import http, ctx
from typing import Dict, List, Any


class SSEAggregator:
    def __init__(self):
        self.aggregated_flows = {}  # 存储聚合后的数据
    
    def response(self, flow: http.HTTPFlow) -> None:
        """处理响应"""
        # 只处理 SSE 响应
        content_type = flow.response.headers.get("content-type", "")
        if "text/event-stream" not in content_type and "application/json" not in content_type:
            return
        
        # 只处理特定 API（可根据需要修改）
        if not any(domain in flow.request.pretty_url for domain in [
            "api.anthropic.com",
            "api.openai.com",
            "api.moonshot.cn",
            "generativelanguage.googleapis.com"
        ]):
            return
        
        try:
            content = flow.response.content.decode('utf-8', errors='ignore')
            
            # 解析 SSE 事件
            events = self._parse_sse_content(content)
            if not events:
                return
            
            # 聚合 content_block_delta
            aggregated_events = self._aggregate_content_deltas(events)
            
            # 格式化聚合后的内容
            aggregated_text = self._format_aggregated_events(aggregated_events)
            
            # 提取关键内容用于 comment
            summary = self._extract_summary(aggregated_events)
            
            # 设置 comment 显示聚合后的关键信息
            flow.comment = f"✅ SSE ({len(events)}→{len(aggregated_events)})\n{summary}"
            
            # 直接修改响应体为聚合后的内容（在 Response 标签查看）
            flow.response.content = aggregated_text.encode('utf-8')
            
            # 同时输出到终端
            ctx.log.info("=" * 80)
            ctx.log.info(f"SSE Response Aggregated - {flow.request.method} {flow.request.pretty_url}")
            ctx.log.info("=" * 80)
            ctx.log.info(aggregated_text)
            ctx.log.info("=" * 80)
            
        except Exception as e:
            ctx.log.error(f"SSE aggregation error: {e}")
    
    def _parse_sse_content(self, content: str) -> List[Dict[str, Any]]:
        """解析 SSE 内容"""
        events = []
        current_event = {}
        
        for line in content.split('\n'):
            line = line.rstrip('\r')
            
            if line.startswith('event: '):
                if current_event:
                    events.append(current_event)
                current_event = {'event': line[7:]}
            elif line.startswith('data: '):
                try:
                    current_event['data'] = json.loads(line[6:])
                except json.JSONDecodeError:
                    current_event['data'] = line[6:]
            elif line == '':
                if current_event:
                    events.append(current_event)
                    current_event = {}
        
        if current_event:
            events.append(current_event)
        
        return events
    
    def _aggregate_content_deltas(self, events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """聚合 content_block_delta 事件"""
        result = []
        delta_buffer = defaultdict(lambda: {
            'thinking_delta': [],
            'text_delta': [],
            'input_json_delta': []
        })
        
        for event in events:
            event_type = event.get('event')
            data = event.get('data', {})
            
            if event_type == 'content_block_delta' and isinstance(data, dict):
                index = data.get('index', 0)
                delta = data.get('delta', {})
                delta_type = delta.get('type', '')
                
                # 收集不同类型的 delta
                if delta_type == 'thinking_delta':
                    delta_buffer[index]['thinking_delta'].append(delta.get('thinking', ''))
                elif delta_type == 'text_delta':
                    delta_buffer[index]['text_delta'].append(delta.get('text', ''))
                elif delta_type == 'input_json_delta':
                    delta_buffer[index]['input_json_delta'].append(delta.get('partial_json', ''))
            else:
                # 在遇到非 delta 事件前，先输出缓存的聚合内容
                if delta_buffer:
                    for index in sorted(delta_buffer.keys()):
                        aggregated = {}
                        
                        if delta_buffer[index]['thinking_delta']:
                            aggregated['thinking_delta'] = ''.join(delta_buffer[index]['thinking_delta'])
                        if delta_buffer[index]['text_delta']:
                            aggregated['text_delta'] = ''.join(delta_buffer[index]['text_delta'])
                        if delta_buffer[index]['input_json_delta']:
                            aggregated['input_json_delta'] = ''.join(delta_buffer[index]['input_json_delta'])
                        
                        if aggregated:
                            result.append({
                                'event': 'content_block_delta (aggregated)',
                                'data': {
                                    'type': 'content_block_delta',
                                    'index': index,
                                    'aggregated_content': aggregated
                                }
                            })
                    
                    delta_buffer.clear()
                
                # 添加当前事件
                result.append(event)
        
        # 处理末尾剩余的 delta
        if delta_buffer:
            for index in sorted(delta_buffer.keys()):
                aggregated = {}
                
                if delta_buffer[index]['thinking_delta']:
                    aggregated['thinking_delta'] = ''.join(delta_buffer[index]['thinking_delta'])
                if delta_buffer[index]['text_delta']:
                    aggregated['text_delta'] = ''.join(delta_buffer[index]['text_delta'])
                if delta_buffer[index]['input_json_delta']:
                    aggregated['input_json_delta'] = ''.join(delta_buffer[index]['input_json_delta'])
                
                if aggregated:
                    result.append({
                        'event': 'content_block_delta (aggregated)',
                        'data': {
                            'type': 'content_block_delta',
                            'index': index,
                            'aggregated_content': aggregated
                        }
                    })
        
        return result
    
    def _format_aggregated_events(self, events: List[Dict[str, Any]]) -> str:
        """格式化聚合后的事件为文本"""
        lines = []
        
        for event in events:
            event_name = event.get('event', '')
            data = event.get('data')
            
            lines.append(f"event: {event_name}")
            if isinstance(data, dict):
                lines.append(f"data: {json.dumps(data, ensure_ascii=False, indent=2)}")
            elif data:
                lines.append(f"data: {data}")
            lines.append('')
        
        return '\n'.join(lines)
    
    def _extract_summary(self, events: List[Dict[str, Any]]) -> str:
        """提取聚合事件的摘要信息"""
        summary_parts = []
        
        for event in events:
            event_name = event.get('event', '')
            data = event.get('data', {})
            
            if event_name == 'content_block_delta (aggregated)':
                aggregated_content = data.get('aggregated_content', {})
                index = data.get('index', 0)
                
                if 'thinking_delta' in aggregated_content:
                    text = aggregated_content['thinking_delta'][:100]
                    summary_parts.append(f"[{index}] 💭 {text}...")
                
                if 'text_delta' in aggregated_content:
                    text = aggregated_content['text_delta'][:100]
                    summary_parts.append(f"[{index}] 📝 {text}...")
                
                if 'input_json_delta' in aggregated_content:
                    try:
                        json_obj = json.loads(aggregated_content['input_json_delta'])
                        if 'command' in json_obj:
                            cmd = json_obj['command'][:80]
                            summary_parts.append(f"[{index}] 🔧 {cmd}...")
                    except:
                        pass
        
        return '\n'.join(summary_parts[:3]) if summary_parts else "SSE Aggregated"


addons = [SSEAggregator()]
