# { "Depends": "py-genlayer:latest" }
import genlayer.gl as gl

class SimpleGuard(gl.Contract):
    def __init__(self):
        self.owner = ""
        self.message = "hello"

    @gl.public.write
    def init(self) -> None:
        self.owner = str(gl.message.sender_address)

    @gl.public.write
    def setMessage(self, msg: str) -> None:
        self.message = msg

    @gl.public.view
    def getMessage(self) -> str:
        return self.message

    @gl.public.view
    def getOwner(self) -> str:
        return self.owner
