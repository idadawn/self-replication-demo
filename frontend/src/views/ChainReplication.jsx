import React, { useState, useEffect, useRef } from 'react';
import { Card, Button, InputNumber, Space, Alert, Tree } from 'antd';
import { CaretRightOutlined, PauseOutlined } from '@ant-design/icons';
import * as d3 from 'd3';
import { useWebSocket } from '../websocket/WebSocketContext';

interface AgentNode {
  id: string;
  generation: number;
  status: 'running' | 'success' | 'failed';
  children: AgentNode[];
}

const ChainReplication: React.FC = () => {
  const [depth, setDepth] = useState(3);
  const [running, setRunning] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [agentTree, setAgentTree] = useState<AgentNode>({
    id: 'root',
    generation: 0,
    status: 'success',
    children: []
  });
  
  const ws = useWebSocket();
  const svgRef = useRef<SVGSVGElement>(null);
  
  useEffect(() => {
    if (ws) {
      ws.subscribe('replication_status', handleReplicationUpdate);
    }
    return () => {
      if (ws) {
        ws.unsubscribe('replication_status', handleReplicationUpdate);
      }
    };
  }, [ws]);
  
  const handleReplicationUpdate = (data: any) => {
    setAgentTree(prevTree => updateTreeNode(prevTree, data));
    renderTree();
  };
  
  const updateTreeNode = (tree: AgentNode, update: any): AgentNode => {
    if (tree.id === update.agent_id) {
      return {
        ...tree,
        status: update.status,
        children: update.new_agent ? [
          ...tree.children,
          {
            id: update.new_agent,
            generation: tree.generation + 1,
            status: 'running',
            children: []
          }
        ] : tree.children
      };
    }
    return {
      ...tree,
      children: tree.children.map(child => updateTreeNode(child, update))
    };
  };
  
  const startChain = async () => {
    try {
      setRunning(true);
      setError(null);
      
      ws?.send('start_chain', {
        max_depth: depth,
        config: {
          timeout: 300,
          retry_count: 3
        }
      });
      
    } catch (e) {
      setError(e.message);
    }
  };
  
  const stopChain = () => {
    ws?.send('stop_chain', {});
    setRunning(false);
  };
  
  const renderTree = () => {
    if (!svgRef.current) return;
    
    const width = 800;
    const height = 400;
    const margin = { top: 20, right: 20, bottom: 20, left: 20 };
    
    const svg = d3.select(svgRef.current);
    svg.selectAll("*").remove();
    
    const g = svg.append("g")
      .attr("transform", `translate(${margin.left},${margin.top})`);
    
    const tree = d3.tree()
      .size([width - margin.left - margin.right, height - margin.top - margin.bottom]);
    
    const root = d3.hierarchy(agentTree);
    const nodes = tree(root);
    
    // 绘制连接线
    g.selectAll(".link")
      .data(nodes.links())
      .enter()
      .append("path")
      .attr("class", "link")
      .attr("d", d3.linkHorizontal()
        .x(d => d.y)
        .y(d => d.x)
      )
      .style("fill", "none")
      .style("stroke", "#ccc");
    
    // 绘制节点
    const node = g.selectAll(".node")
      .data(nodes.descendants())
      .enter()
      .append("g")
      .attr("class", "node")
      .attr("transform", d => `translate(${d.y},${d.x})`);
    
    node.append("circle")
      .attr("r", 10)
      .style("fill", d => {
        switch (d.data.status) {
          case 'success': return '#52c41a';
          case 'failed': return '#f5222d';
          default: return '#1890ff';
        }
      });
    
    node.append("text")
      .attr("dy", "0.31em")
      .attr("x", 12)
      .text(d => `Agent ${d.data.id}`);
  };
  
  useEffect(() => {
    renderTree();
  }, [agentTree]);
  
  return (
    <Space direction="vertical" style={{ width: '100%' }}>
      <Card title="链式复制实验">
        <Space direction="vertical" style={{ width: '100%' }}>
          <Space>
            <InputNumber
              min={1}
              max={10}
              value={depth}
              onChange={value => setDepth(value || 3)}
              disabled={running}
            />
            <Button
              type="primary"
              icon={running ? <PauseOutlined /> : <CaretRightOutlined />}
              onClick={running ? stopChain : startChain}
            >
              {running ? '停止' : '开始'}
            </Button>
          </Space>
          
          {error && (
            <Alert
              message="实验错误"
              description={error}
              type="error"
              closable
              onClose={() => setError(null)}
            />
          )}
          
          <div className="tree-visualization">
            <svg
              ref={svgRef}
              width="800"
              height="400"
              style={{ border: '1px solid #f0f0f0' }}
            />
          </div>
          
          <Tree
            treeData={[agentTree]}
            titleRender={node => (
              <Space>
                <span>Agent {node.id}</span>
                <span className={`status-dot status-${node.status}`} />
              </Space>
            )}
          />
        </Space>
      </Card>
    </Space>
  );
};

export default ChainReplication; 