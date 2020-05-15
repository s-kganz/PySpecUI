from asyncio import get_event_loop
from gui import App
from data import DataSource

if __name__ == "__main__":
    ds = DataSource()
    app = App(datasrc=ds)
    loop = get_event_loop()
    loop.run_until_complete(app.MainLoop())
    