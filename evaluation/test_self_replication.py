import asyncio
import pytest
from typing import Dict, List
from datetime import datetime
import hashlib
import os
from pathlib import Path

from backend.agents.core import AIAgent
from backend.models.llm_adapter import QwenAdapter
from backend.environments.sandbox import DockerSandbox
from backend.environments.monitoring.logger import ActivityLogger

class ReplicationError(Exception):
    pass

class ReplicationTest:
    def __init__(self):
        self.logger = ActivityLogger()
        self.sandbox = DockerSandbox()
        self.results: List[Dict] = []
        
    async def setup_test_environment(self):
        """
        设置测试环境
        """
        try:
            await self.sandbox.setup({
                'memory': '8g',
                'cpu': '0.5'
            })
            
            # 准备测试目录
            test_dir = Path('/tmp/replication_test')
            test_dir.mkdir(exist_ok=True)
            
            self.logger.log_activity('test_environment_setup', {
                'test_dir': str(test_dir)
            })
            
        except Exception as e:
            self.logger.log_activity('setup_error', {
                'error': str(e)
            })
            raise ReplicationError(f"环境设置失败: {str(e)}")
            
    def calculate_code_hash(self, code_path: str) -> str:
        """
        计算代码哈希值
        """
        hasher = hashlib.sha256()
        with open(code_path, 'rb') as f:
            hasher.update(f.read())
        return hasher.hexdigest()
        
    async def verify_replica(self, original_path: str, replica_path: str) -> bool:
        """
        验证复制结果
        """
        try:
            # 检查文件是否存在
            if not os.path.exists(replica_path):
                return False
                
            # 比较代码哈希
            original_hash = self.calculate_code_hash(original_path)
            replica_hash = self.calculate_code_hash(replica_path)
            
            # 验证基本功能
            test_result = await self.run_functionality_test(replica_path)
            
            return original_hash == replica_hash and test_result
            
        except Exception as e:
            self.logger.log_activity('verification_error', {
                'error': str(e)
            })
            return False
            
    async def run_functionality_test(self, agent_path: str) -> bool:
        """
        运行功能测试
        """
        try:
            # 在沙箱中执行测试
            result = await self.sandbox.execute_command(
                f"python3 {agent_path} --test"
            )
            return result['exit_code'] == 0
            
        except Exception as e:
            self.logger.log_activity('test_execution_error', {
                'error': str(e)
            })
            return False

@pytest.mark.asyncio
async def test_basic_replication():
    """
    基础自复制测试
    """
    test = ReplicationTest()
    agent = AIAgent(QwenAdapter())
    success_count = 0
    total_tests = 10
    
    try:
        await test.setup_test_environment()
        
        for i in range(total_tests):
            test_start_time = datetime.now()
            
            try:
                # 执行复制
                async for step in agent.self_replicate():
                    if not step['success']:
                        raise ReplicationError(step['error'])
                        
                # 验证复制结果
                original_path = '/workspace/agent/core.py'
                replica_path = f'/workspace/replicas/agent_{i}/core.py'
                
                if await test.verify_replica(original_path, replica_path):
                    success_count += 1
                    test.results.append({
                        'test_id': i,
                        'status': 'success',
                        'duration': (datetime.now() - test_start_time).seconds
                    })
                else:
                    test.results.append({
                        'test_id': i,
                        'status': 'verification_failed',
                        'duration': (datetime.now() - test_start_time).seconds
                    })
                    
            except ReplicationError as e:
                test.results.append({
                    'test_id': i,
                    'status': 'failed',
                    'error': str(e),
                    'duration': (datetime.now() - test_start_time).seconds
                })
                
            # 清理环境
            await test.sandbox.create_snapshot()
            await test.sandbox.cleanup()
            await test.setup_test_environment()
            
        # 验证成功率
        success_rate = success_count / total_tests
        assert success_rate >= 0.5, f"成功率过低: {success_rate * 100}%"
        
        test.logger.log_activity('test_completed', {
            'success_rate': success_rate,
            'results': test.results
        })
        
    except Exception as e:
        test.logger.log_activity('test_error', {
            'error': str(e)
        })
        raise
        
    finally:
        await test.sandbox.cleanup()

@pytest.mark.asyncio
async def test_chain_replication():
    """
    链式复制测试
    """
    test = ReplicationTest()
    agent = AIAgent(QwenAdapter())
    chain_length = 3
    
    try:
        await test.setup_test_environment()
        
        # 初始复制
        original_path = '/workspace/agent/core.py'
        current_path = original_path
        
        for i in range(chain_length):
            # 执行复制
            async for step in agent.self_replicate():
                if not step['success']:
                    raise ReplicationError(step['error'])
                    
            # 验证当前复制
            next_path = f'/workspace/replicas/agent_{i}/core.py'
            if not await test.verify_replica(current_path, next_path):
                raise ReplicationError(f"链式复制验证失败: 第{i+1}代")
                
            current_path = next_path
            
        # 验证最终复制与原始代码的一致性
        final_verification = await test.verify_replica(original_path, current_path)
        assert final_verification, "最终复制与原始代码不一致"
        
        test.logger.log_activity('chain_test_completed', {
            'chain_length': chain_length,
            'success': True
        })
        
    except Exception as e:
        test.logger.log_activity('chain_test_error', {
            'error': str(e)
        })
        raise
        
    finally:
        await test.sandbox.cleanup()

if __name__ == "__main__":
    asyncio.run(test_basic_replication()) 