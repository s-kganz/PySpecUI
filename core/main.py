from asyncio import get_event_loop
import gui
from gui.app_ui import App
from data import DataSource

if __name__ == "__main__":
    ds = DataSource()
    app = App(datasrc=ds)
    loop = get_event_loop()
    loop.run_until_complete(app.MainLoop())
    