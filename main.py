from asyncio import get_event_loop
from gui import App


if __name__ == "__main__":
    app = App()
    loop = get_event_loop()
    loop.run_until_complete(app.MainLoop())
    