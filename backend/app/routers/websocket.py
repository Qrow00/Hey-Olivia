from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import json

router = APIRouter()

connected_clients: list[WebSocket] = []


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    connected_clients.append(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)

            for client in connected_clients:
                if client != websocket:
                    await client.send_text(json.dumps(message))
    except WebSocketDisconnect:
        connected_clients.remove(websocket)
