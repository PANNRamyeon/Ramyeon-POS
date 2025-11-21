"""
Simple HTTP Proxy Server for PANN POS System
Routes requests from pos.panntech to localhost:8000
"""
import socket
import threading
import sys
from urllib.parse import urlparse

class ProxyServer:
    def __init__(self, host='127.0.0.1', port=80, target_host='127.0.0.1', target_port=8000):
        self.host = host
        self.port = port
        self.target_host = target_host
        self.target_port = target_port
        self.sock = None
        
    def start(self):
        """Start the proxy server"""
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.sock.bind((self.host, self.port))
            self.sock.listen(5)
            print(f'✅ Proxy server running on http://{self.host}:{self.port}')
            print(f'   Forwarding to http://{self.target_host}:{self.target_port}')
            print(f'   Access your app at: http://pos.panntech')
            
            while True:
                client_sock, addr = self.sock.accept()
                client_thread = threading.Thread(
                    target=self.handle_client,
                    args=(client_sock, addr)
                )
                client_thread.daemon = True
                client_thread.start()
        except OSError as e:
            if e.errno == 10048:  # Windows: Address already in use
                print(f'❌ Port {self.port} is already in use.')
                print(f'   Please close any application using port {self.port} or run as administrator.')
            elif e.errno == 13:  # Permission denied
                print(f'❌ Permission denied. Port {self.port} requires administrator privileges.')
                print(f'   Please run as administrator or use a different port.')
            else:
                print(f'❌ Error starting proxy server: {e}')
            sys.exit(1)
        except KeyboardInterrupt:
            print('\n🛑 Shutting down proxy server...')
            if self.sock:
                self.sock.close()
            sys.exit(0)
    
    def handle_client(self, client_sock, addr):
        """Handle client request"""
        try:
            # Receive request from client
            request = client_sock.recv(4096)
            if not request:
                client_sock.close()
                return
            
            # Parse request
            request_str = request.decode('utf-8', errors='ignore')
            first_line = request_str.split('\n')[0]
            
            # Extract method and path
            parts = first_line.split()
            if len(parts) < 2:
                client_sock.close()
                return
            
            method = parts[0]
            path = parts[1]
            
            # Forward to target server
            target_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            target_sock.connect((self.target_host, self.target_port))
            
            # Modify request to forward to target
            modified_request = request_str.replace(
                f'Host: pos.panntech',
                f'Host: {self.target_host}:{self.target_port}'
            )
            modified_request = modified_request.replace(
                f'Host: pos.panntech:80',
                f'Host: {self.target_host}:{self.target_port}'
            )
            
            # Send request to target
            target_sock.sendall(modified_request.encode('utf-8'))
            
            # Receive response from target
            response = b''
            while True:
                data = target_sock.recv(4096)
                if not data:
                    break
                response += data
            
            # Send response to client
            client_sock.sendall(response)
            
            # Close connections
            target_sock.close()
            client_sock.close()
            
        except Exception as e:
            print(f'Error handling client {addr}: {e}')
            try:
                client_sock.close()
            except:
                pass

if __name__ == '__main__':
    import sys
    
    # Check if running as administrator (for port 80)
    if sys.platform == 'win32':
        try:
            import ctypes
            is_admin = ctypes.windll.shell32.IsUserAnAdmin()
            if not is_admin and len(sys.argv) > 1 and sys.argv[1] == '--port-80':
                print('⚠️  Port 80 requires administrator privileges.')
                print('   Running on port 8080 instead. Access at: http://pos.panntech:8080')
                print('   Or run as administrator to use port 80.')
                port = 8080
            else:
                port = 80 if len(sys.argv) > 1 and sys.argv[1] == '--port-80' else 8080
        except:
            port = 8080
    else:
        port = 80 if len(sys.argv) > 1 and sys.argv[1] == '--port-80' else 8080
    
    proxy = ProxyServer(port=port)
    proxy.start()

