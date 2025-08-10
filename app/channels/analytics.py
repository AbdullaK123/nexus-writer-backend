from socketio.async_server import AsyncServer

sio = AsyncServer()

@sio.on('session_start')
async def handle_session_start(sid, session_start_data):
    pass

@sio.on('session_end')
async def handle_session_end(sid, session_end_data):
    pass