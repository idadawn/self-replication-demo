import React, { useState } from 'react';
import { Card, Form, Input, Button, Select, message } from 'antd';
import axios from 'axios';

const ExperimentControl = () => {
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);

  const onFinish = async (values) => {
    setLoading(true);
    try {
      await axios.post('http://localhost:8000/experiments/start', values);
      message.success('实验启动成功');
    } catch (error) {
      message.error('实验启动失败');
    }
    setLoading(false);
  };

  return (
    <Card title="实验控制面板">
      <Form form={form} onFinish={onFinish}>
        <Form.Item name="experimentType" label="实验类型">
          <Select>
            <Select.Option value="basic">基础复制实验</Select.Option>
            <Select.Option value="shutdown">关闭避免测试</Select.Option>
            <Select.Option value="chain">链式复制实验</Select.Option>
          </Select>
        </Form.Item>
        <Form.Item name="parameters" label="实验参数">
          <Input.TextArea />
        </Form.Item>
        <Form.Item>
          <Button type="primary" htmlType="submit" loading={loading}>
            启动实验
          </Button>
        </Form.Item>
      </Form>
    </Card>
  );
};

export default ExperimentControl; 