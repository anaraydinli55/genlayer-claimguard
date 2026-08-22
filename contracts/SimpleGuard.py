import genlayer.gl as gl

class SimpleGuard(gl.Contract):
    def __init__(self):
        self.owner = ""
        self.message = "hello"

    @gl.public.write
    def init(self):
        self.owner = str(gl.message.sender_address)

    @gl.public.write
    def setMessage(self, msg):
        self.message = msg

    @gl.public.view
    def getMessage(self):
        return self.message

    @gl.public.view
    def getOwner(self):
        return self.owner
