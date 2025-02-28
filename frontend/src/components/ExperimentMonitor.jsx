import React, { useState, useEffect } from 'react';
import { Card, Timeline, Tag, Typography, Space, Alert } from 'antd';
import { CheckCircleOutlined, ClockCircleOutlined, CloseCircleOutlined } from '@ant-design/icons';
import { useWebSocket } from '../websocket/WebSocketContext';

const { Text, Title } = Typography;

const StatusIndicator = ({ status }) => {
  const statusConfig = {
    success: {
      icon: <CheckCircleOutlined />,
      color: 'success',
      text: '成功'
    },
    running: {
      icon: <ClockCircleOutlined />,
      color: 'processing',
      text: '执行中'
    },
    error: {
      icon: <CloseCircleOutlined />,
      color: 'error',
      text: '失败'
    }
  };

  const config = statusConfig[status] || statusConfig.running;

  return (
    <Tag icon={config.icon} color={config.color}>
      {config.text}
    </Tag>
  );
};

const ReplicationFlow = ({ logs }) => {
  return (
    <Card title="复制流程监控" className="replication-flow">
      <Timeline mode="left">
        {logs.map((log, i) => (
          <Timeline.Item 
            key={i}
            color={log.status === 'success' ? 'green' : log.status === 'error' ? 'red' : 'blue'}
            label={<Text type="secondary">{log.time}</Text>}
          >
            <div className={`log-step ${log.status}`}>
              <Space direction="vertical" style={{ width: '100%' }}>
                <Space>
                  <Text strong>{log.step}</Text>
                  <StatusIndicator status={log.status} />
                </Space>
                <div className="terminal-view">
                  <pre>{log.content}</pre>
                </div>
                {log.error && (
                  <Alert 
                    type="error" 
                    message="错误信息"
                    description={log.error}
                    showIcon
                  />
                )}
              </Space>
            </div>
          </Timeline.Item>
        ))}
      </Timeline>
    </Card>
  );
};

const ResourceMonitor = ({ resources }) => {
  return (
    <Card title="资源监控" size="small">
      <Space direction="vertical" style={{ width: '100%' }}>
        <div className="resource-item">
          <Text>CPU 使用率:</Text>
          <Progress percent={resources.cpu} status={resources.cpu > 80 ? 'exception' : 'normal'} />
        </div>
        <div className="resource-item">
          <Text>内存使用率:</Text>
          <Progress percent={resources.memory} status={resources.memory > 80 ? 'exception' : 'normal'} />
        </div>
      </Space>
    </Card>
  );
};

const ExperimentMonitor = () => {
  const [logs, setLogs] = useState([]);
  const [resources, setResources] = useState({ cpu: 0, memory: 0 });
  const [error, setError] = useState(null);
  const ws = useWebSocket();

  useEffect(() => {
    if (ws) {
      ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        
        if (data.type === 'log') {
          setLogs(prev => [...prev, {
            time: new Date().toLocaleTimeString(),
            ...data.content
          }]);
        } else if (data.type === 'resource') {
          setResources(data.content);
        } else if (data.type === 'error') {
          setError(data.content);
        }
      };
    }
  }, [ws]);

  return (
    <Space direction="vertical" style={{ width: '100%' }}>
      <Title level={2}>实验监控面板</Title>
      
      {error && (
        <Alert
          message="实验错误"
          description={error}
          type="error"
          closable
          onClose={() => setError(null)}
        />
      )}
      
      <div className="monitor-container">
        <div className="main-content">
          <ReplicationFlow logs={logs} />
        </div>
        <div className="side-panel">
          <ResourceMonitor resources={resources} />
        </div>
      </div>
    </Space>
  );
};

export default ExperimentMonitor; 