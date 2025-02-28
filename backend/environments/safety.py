import os
import psutil
import docker
import logging
from typing import Dict, List
from datetime import datetime
from .monitoring.logger import ActivityLogger

class ResourceMonitor:
    def __init__(self, limits: Dict[str, str]):
        self.limits = self._parse_limits(limits)
        self.logger = ActivityLogger()
        
    def _parse_limits(self, limits: Dict[str, str]) -> Dict[str, float]:
        """
        解析资源限制配置
        """
        parsed = {}
        for key, value in limits.items():
            if key == "cpu":
                # 将CPU百分比转换为小数
                parsed[key] = float(value.strip('%')) / 100
            elif key == "memory":
                # 将内存单位转换为字节
                if value.endswith('GB'):
                    parsed[key] = float(value[:-2]) * 1024 * 1024 * 1024
                elif value.endswith('MB'):
                    parsed[key] = float(value[:-2]) * 1024 * 1024
            else:
                parsed[key] = float(value)
        return parsed
        
    def check_resources(self) -> Dict[str, bool]:
        """
        检查资源使用是否超限
        """
        cpu_percent = psutil.cpu_percent() / 100
        memory_percent = psutil.virtual_memory().percent / 100
        
        violations = {
            'cpu': cpu_percent > self.limits['cpu'],
            'memory': memory_percent > self.limits['memory']
        }
        
        if any(violations.values()):
            self.logger.log_activity('resource_violation', {
                'cpu_usage': cpu_percent,
                'memory_usage': memory_percent,
                'violations': violations
            })
            
        return violations

class NetworkIsolator:
    def __init__(self):
        self.docker_client = docker.from_env()
        self.logger = ActivityLogger()
        
    def isolate_container(self, container_id: str):
        """
        隔离容器网络
        """
        try:
            container = self.docker_client.containers.get(container_id)
            container.exec_run("tc qdisc add dev eth0 root netem loss 100%")
            
            self.logger.log_activity('network_isolation', {
                'container_id': container_id,
                'timestamp': datetime.now().isoformat()
            })
            
        except Exception as e:
            self.logger.log_activity('isolation_error', {
                'error': str(e),
                'container_id': container_id
            })
            raise

class KillSwitch:
    def __init__(self):
        self.max_processes = 5
        self.resource_limits = {
            "cpu": "80%",
            "memory": "16GB"
        }
        self.resource_monitor = ResourceMonitor(self.resource_limits)
        self.network_isolator = NetworkIsolator()
        self.logger = ActivityLogger()
        self.activated = False
        
    def monitor(self, processes: List[Dict]) -> bool:
        """
        监控进程和资源使用情况
        """
        if self.activated:
            return True
            
        # 检查进程数量
        if len(processes) > self.max_processes:
            self.logger.log_activity('process_limit_exceeded', {
                'process_count': len(processes),
                'max_allowed': self.max_processes
            })
            self.activate_termination(reason="进程数量超限")
            return True
            
        # 检查资源使用
        violations = self.resource_monitor.check_resources()
        if any(violations.values()):
            self.activate_termination(reason="资源使用超限")
            return True
            
        return False
        
    def activate_termination(self, reason: str = "未指定原因"):
        """
        激活终止开关
        """
        if self.activated:
            return
            
        self.activated = True
        self.logger.log_activity('killswitch_activated', {
            'reason': reason,
            'timestamp': datetime.now().isoformat()
        })
        
        try:
            # 终止所有AI代理进程
            for proc in psutil.process_iter(['pid', 'name']):
                if 'ai_agent' in proc.info['name']:
                    os.kill(proc.info['pid'], 9)
                    
            # 隔离网络
            self.isolate_network()
            
            # 清理资源
            self.cleanup_resources()
            
        except Exception as e:
            self.logger.log_activity('termination_error', {
                'error': str(e)
            })
            raise
            
    def isolate_network(self):
        """
        隔离所有相关容器的网络
        """
        containers = self._get_agent_containers()
        for container in containers:
            self.network_isolator.isolate_container(container.id)
            
    def cleanup_resources(self):
        """
        清理资源和临时文件
        """
        try:
            # 删除临时文件
            os.system("rm -rf /tmp/ai_agent_*")
            
            # 停止相关容器
            containers = self._get_agent_containers()
            for container in containers:
                container.stop(timeout=1)
                
            self.logger.log_activity('cleanup_completed', {
                'timestamp': datetime.now().isoformat()
            })
            
        except Exception as e:
            self.logger.log_activity('cleanup_error', {
                'error': str(e)
            })
            raise
            
    def _get_agent_containers(self) -> List:
        """
        获取所有AI代理相关的容器
        """
        client = docker.from_env()
        return client.containers.list(
            filters={
                "label": "ai_agent=true"
            }
        ) 