interface WebSocketConfig {
  url: string;
  reconnectInterval: number;
  maxReconnectAttempts: number;
}

interface MessageHandler {
  (message: any): void;
}

export class WebSocketClient {
  private ws: WebSocket | null = null;
  private reconnectAttempts = 0;
  private messageHandlers: Map<string, MessageHandler[]> = new Map();
  private messageBuffer: any[] = [];
  private lastMessageId = 0;
  
  constructor(private config: WebSocketConfig) {
    this.connect();
  }
  
  private connect() {
    try {
      this.ws = new WebSocket(this.config.url);
      
      this.ws.onopen = () => {
        console.log('WebSocket连接已建立');
        this.reconnectAttempts = 0;
        this.handleReconnection();
      };
      
      this.ws.onmessage = (event) => {
        const message = JSON.parse(event.data);
        this.handleMessage(message);
      };
      
      this.ws.onclose = () => {
        console.log('WebSocket连接已关闭');
        this.handleReconnection();
      };
      
      this.ws.onerror = (error) => {
        console.error('WebSocket错误:', error);
      };
      
    } catch (error) {
      console.error('WebSocket连接失败:', error);
      this.handleReconnection();
    }
  }
  
  private handleReconnection() {
    if (this.reconnectAttempts >= this.config.maxReconnectAttempts) {
      console.error('达到最大重连次数');
      return;
    }
    
    this.reconnectAttempts++;
    setTimeout(() => {
      console.log(`尝试重连 (${this.reconnectAttempts})`);
      this.connect();
    }, this.config.reconnectInterval);
  }
  
  private handleMessage(message: any) {
    this.lastMessageId++;
    this.messageBuffer.push(message);
    
    // 限制缓冲区大小
    if (this.messageBuffer.length > 1000) {
      this.messageBuffer.shift();
    }
    
    // 调用消息处理器
    const handlers = this.messageHandlers.get(message.type) || [];
    handlers.forEach(handler => handler(message.payload));
  }
  
  public subscribe(messageType: string, handler: MessageHandler) {
    if (!this.messageHandlers.has(messageType)) {
      this.messageHandlers.set(messageType, []);
    }
    this.messageHandlers.get(messageType)!.push(handler);
  }
  
  public unsubscribe(messageType: string, handler: MessageHandler) {
    const handlers = this.messageHandlers.get(messageType);
    if (handlers) {
      const index = handlers.indexOf(handler);
      if (index !== -1) {
        handlers.splice(index, 1);
      }
    }
  }
  
  public send(type: string, payload: any) {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({ type, payload }));
    } else {
      console.error('WebSocket未连接');
    }
  }
} 