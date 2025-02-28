import asyncio
import json
from typing import Dict, Set, Optional
from fastapi import WebSocket
from google.protobuf.json_format import MessageToDict
from ..proto import messages_pb2 as pb
from ..monitoring.logger import ActivityLogger

class ConnectionManager:
    def __init__(self):
        self.active_connections: Set[WebSocket] = set()
        self.connection_states: Dict[WebSocket, Dict] = {}
        self.logger = ActivityLogger()
        
    async def connect(self, websocket: WebSocket):
        """
        处理新的WebSocket连接
        """
        await websocket.accept()
        self.active_connections.add(websocket)
        self.connection_states[websocket] = {
            'last_message_id': 0,
            'subscribed_topics': set()
        }
        
        self.logger.log_activity('websocket_connected', {
            'client_id': id(websocket)
        })
        
    async def disconnect(self, websocket: WebSocket):
        """
        处理WebSocket断开连接
        """
        self.active_connections.remove(websocket)
        self.connection_states.pop(websocket, None)
        
        self.logger.log_activity('websocket_disconnected', {
            'client_id': id(websocket)
        })
        
    async def broadcast_message(self, message_type: str, payload: dict):
        """
        广播消息到所有连接
        """
        # 创建protobuf消息
        ws_message = pb.WebSocketMessage()
        ws_message.type = message_type
        
        if message_type == 'log':
            log_msg = pb.LogMessage()
            log_msg.timestamp = payload['timestamp']
            log_msg.level = payload['level']
            log_msg.content = payload['content']
            for k, v in payload.get('metadata', {}).items():
                log_msg.metadata[k] = str(v)
            ws_message.log.CopyFrom(log_msg)
            
        elif message_type == 'metrics':
            metrics = pb.ResourceMetrics()
            metrics.cpu_usage = payload['cpu_usage']
            metrics.memory_usage = payload['memory_usage']
            metrics.process_count = payload['process_count']
            for k, v in payload.get('custom_metrics', {}).items():
                metrics.custom_metrics[k] = float(v)
            ws_message.metrics.CopyFrom(metrics)
            
        elif message_type == 'status':
            status = pb.ExperimentStatus()
            status.experiment_id = payload['experiment_id']
            status.status = payload['status']
            status.current_step = payload['current_step']
            status.errors.extend(payload.get('errors', []))
            ws_message.status.CopyFrom(status)
            
        elif message_type == 'error':
            ws_message.error = payload['error']
            
        # 序列化消息
        message_dict = MessageToDict(
            ws_message,
            preserving_proto_field_name=True,
            including_default_value_fields=True
        )
        
        # 广播消息
        for websocket in self.active_connections:
            try:
                await websocket.send_json(message_dict)
            except Exception as e:
                self.logger.log_activity('broadcast_error', {
                    'client_id': id(websocket),
                    'error': str(e)
                })
                await self.disconnect(websocket)
                
    async def send_message(self, websocket: WebSocket, message_type: str, payload: dict):
        """
        发送消息到特定连接
        """
        try:
            await websocket.send_json({
                'type': message_type,
                'payload': payload
            })
        except Exception as e:
            self.logger.log_activity('send_error', {
                'client_id': id(websocket),
                'error': str(e)
            })
            await self.disconnect(websocket)

class ReconnectionHandler:
    def __init__(self, manager: ConnectionManager):
        self.manager = manager
        self.message_buffer: Dict[str, list] = {}
        self.max_buffer_size = 1000
        
    def store_message(self, client_id: str, message: dict):
        """
        存储消息用于重连恢复
        """
        if client_id not in self.message_buffer:
            self.message_buffer[client_id] = []
            
        buffer = self.message_buffer[client_id]
        buffer.append(message)
        
        # 限制缓冲区大小
        if len(buffer) > self.max_buffer_size:
            buffer.pop(0)
            
    async def handle_reconnection(self, websocket: WebSocket, client_id: str, last_message_id: int):
        """
        处理客户端重连
        """
        if client_id in self.message_buffer:
            # 发送错过的消息
            messages = self.message_buffer[client_id][last_message_id:]
            for message in messages:
                await self.manager.send_message(websocket, message['type'], message['payload']) 