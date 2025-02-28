import React, { createContext, useContext, useEffect, useState } from 'react';

const WebSocketContext = createContext(null);

export const WebSocketProvider = ({ children }) => {
  const [ws, setWs] = useState(null);

  useEffect(() => {
    const websocket = new WebSocket('ws://localhost:8000/ws');
    
    websocket.onopen = () => {
      console.log('WebSocket连接已建立');
    };

    websocket.onerror = (error) => {
      console.error('WebSocket错误:', error);
    };

    websocket.onclose = () => {
      console.log('WebSocket连接已关闭');
    };

    setWs(websocket);

    return () => {
      websocket.close();
    };
  }, []);

  return (
    <WebSocketContext.Provider value={ws}>
      {children}
    </WebSocketContext.Provider>
  );
};

export const useWebSocket = () => useContext(WebSocketContext); 