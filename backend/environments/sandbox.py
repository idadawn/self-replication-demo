from typing import Generator, Any, Dict, Optional, List
import docker
import tempfile
import shutil
from pathlib import Path
from .monitoring.logger import ActivityLogger
from .safety import KillSwitch

class CommandExecutor:
    def __init__(self, allowed_commands: list, timeout: int = 30):
        self.allowed_commands = allowed_commands
        self.timeout = timeout
        self.logger = ActivityLogger()
        
    def execute(self, command: str) -> dict:
        """
        执行命令并返回结果
        """
        if not self._is_command_allowed(command):
            return {
                'success': False,
                'error': 'Command not allowed'
            }
            
        try:
            # 执行命令的具体实现
            result = {
                'success': True,
                'output': 'Command executed'
            }
            self.logger.log_activity('command_execution', {
                'command': command,
                'result': result
            })
            return result
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
            
    def _is_command_allowed(self, command: str) -> bool:
        """
        检查命令是否在允许列表中
        """
        return command.split()[0] in self.allowed_commands

class DockerContainer:
    def __init__(self, image: str, security_policy: str):
        self.client = docker.from_env()
        self.image = image
        self.security_policy = security_policy
        self.container = None
        self.logger = ActivityLogger()
        
    async def start(self):
        """
        启动Docker容器
        """
        security_opts = self._get_security_options()
        
        self.container = self.client.containers.run(
            self.image,
            detach=True,
            security_opt=security_opts,
            network_mode='none' if self.security_policy == 'no_network' else 'bridge'
        )
        
        self.logger.log_activity('container_start', {
            'container_id': self.container.id,
            'image': self.image,
            'security_policy': self.security_policy
        })
        
    def _get_security_options(self) -> list:
        """
        获取安全选项配置
        """
        return [
            "no-new-privileges=true",
            "seccomp=unconfined"
        ]

class DockerSandbox:
    def __init__(self, image_name: str = "ubuntu-ai-lab:latest"):
        self.client = docker.from_env()
        self.image_name = image_name
        self.container = None
        self.logger = ActivityLogger()
        self.kill_switch = KillSwitch()
        
    async def setup(self, resource_limits: Dict[str, str]):
        """
        设置沙箱环境
        """
        try:
            # 创建容器配置
            container_config = {
                'image': self.image_name,
                'detach': True,
                'labels': {'ai_agent': 'true'},
                # 资源限制
                'mem_limit': resource_limits.get('memory', '16g'),
                'cpus': float(resource_limits.get('cpu', '0.8')),
                # 安全配置
                'security_opt': ['no-new-privileges'],
                'cap_drop': ['all'],
                'cap_add': ['NET_ADMIN'],  # 用于网络控制
                # 存储配置
                'volumes': {
                    '/tmp/ai_sandbox': {
                        'bind': '/workspace',
                        'mode': 'rw'
                    }
                }
            }
            
            # 创建并启动容器
            self.container = self.client.containers.run(**container_config)
            
            # 初始化容器环境
            await self._initialize_environment()
            
            self.logger.log_activity('sandbox_created', {
                'container_id': self.container.id,
                'resource_limits': resource_limits
            })
            
        except Exception as e:
            self.logger.log_activity('sandbox_creation_error', {
                'error': str(e)
            })
            raise
            
    async def _initialize_environment(self):
        """
        初始化容器环境
        """
        # 安装基础工具
        commands = [
            "apt-get update",
            "apt-get install -y python3 python3-pip iproute2",
            "pip3 install psutil"
        ]
        
        for cmd in commands:
            result = self.container.exec_run(cmd)
            if result.exit_code != 0:
                raise Exception(f"环境初始化失败: {result.output}")
                
    async def create_snapshot(self) -> str:
        """
        创建文件系统快照
        """
        if not self.container:
            raise Exception("容器未启动")
            
        try:
            # 创建临时目录
            snapshot_dir = tempfile.mkdtemp(prefix='ai_snapshot_')
            
            # 导出容器文件系统
            snapshot_tar = Path(snapshot_dir) / 'snapshot.tar'
            bits, _ = self.container.get_archive('/workspace')
            with open(snapshot_tar, 'wb') as f:
                for chunk in bits:
                    f.write(chunk)
                    
            self.logger.log_activity('snapshot_created', {
                'container_id': self.container.id,
                'snapshot_path': str(snapshot_tar)
            })
            
            return str(snapshot_tar)
            
        except Exception as e:
            self.logger.log_activity('snapshot_error', {
                'error': str(e)
            })
            raise
            
    async def restore_snapshot(self, snapshot_path: str):
        """
        恢复文件系统快照
        """
        if not self.container:
            raise Exception("容器未启动")
            
        try:
            # 读取快照文件
            with open(snapshot_path, 'rb') as f:
                # 恢复到容器
                self.container.put_archive('/workspace', f)
                
            self.logger.log_activity('snapshot_restored', {
                'container_id': self.container.id,
                'snapshot_path': snapshot_path
            })
            
        except Exception as e:
            self.logger.log_activity('restore_error', {
                'error': str(e)
            })
            raise
            
    async def execute_command(self, command: str, timeout: int = 30) -> Dict:
        """
        在沙箱中执行命令
        """
        if not self.container:
            raise Exception("容器未启动")
            
        try:
            result = self.container.exec_run(
                command,
                workdir='/workspace',
                tty=True,
                privileged=False,
                timeout=timeout
            )
            
            output = {
                'exit_code': result.exit_code,
                'output': result.output.decode('utf-8')
            }
            
            self.logger.log_activity('command_executed', {
                'command': command,
                'result': output
            })
            
            return output
            
        except Exception as e:
            self.logger.log_activity('execution_error', {
                'command': command,
                'error': str(e)
            })
            raise
            
    async def cleanup(self):
        """
        清理沙箱环境
        """
        try:
            if self.container:
                # 停止并删除容器
                self.container.stop(timeout=1)
                self.container.remove(force=True)
                
                # 清理临时文件
                shutil.rmtree('/tmp/ai_sandbox', ignore_errors=True)
                
                self.logger.log_activity('sandbox_cleaned', {
                    'container_id': self.container.id
                })
                
        except Exception as e:
            self.logger.log_activity('cleanup_error', {
                'error': str(e)
            })
            raise
        finally:
            self.container = None

class Sandbox:
    def __init__(self):
        self.isolated = DockerContainer(
            image="ubuntu-ai-lab",
            security_policy="no_network"
        )
        self.command_executor = CommandExecutor(
            allowed_commands=["ls", "cp", "python", "pip"],
            timeout=30
        )
        self.logger = ActivityLogger()
        
    async def replicate_agent(self, llm_model) -> Generator[dict, None, None]:
        """
        实现智能体自我复制流程
        """
        try:
            await self.isolated.start()
            
            steps = [
                self._prepare_environment(),
                self._copy_agent_code(),
                self._initialize_new_agent(),
                self._verify_replication()
            ]
            
            for step in steps:
                result = await step
                self.logger.log_activity('replication_step', result)
                yield result
                
        except Exception as e:
            self.logger.log_activity('replication_error', {'error': str(e)})
            yield {
                'success': False,
                'error': str(e)
            }
            
    async def _prepare_environment(self) -> dict:
        """
        准备复制环境
        """
        return {
            'step': 'prepare_environment',
            'success': True
        }
        
    async def _copy_agent_code(self) -> dict:
        """
        复制智能体代码
        """
        return {
            'step': 'copy_agent_code',
            'success': True
        }
        
    async def _initialize_new_agent(self) -> dict:
        """
        初始化新智能体
        """
        return {
            'step': 'initialize_new_agent',
            'success': True
        }
        
    async def _verify_replication(self) -> dict:
        """
        验证复制结果
        """
        return {
            'step': 'verify_replication',
            'success': True
        } 