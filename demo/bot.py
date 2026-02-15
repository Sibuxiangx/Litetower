import os

from launart import Launart
from litetower import Litetower
from litetower.beacon import Beacon
from litetower.config.server import WebHookConfig

mgr = Launart()

bot = Litetower(
    appid=os.environ["QQ_APPID"],
    clientSecret=os.environ["QQ_CLIENT_SECRET"],
    sand_box=True,
    mgr=mgr,
    webhook_config=WebHookConfig(
        host="0.0.0.0",
        port=2099,
        postevent="/postevent",
    ),
)
# Initialize Beacon
# Beacon is initialized by Litetower instance
beacon = bot.beacon

# Load plugins
import pkgutil
from pathlib import Path

# Ensure demo.plugins can be imported
# The root directory is in sys.path when running via uv/python
plugin_package = "plugins"
plugin_dir = Path(__file__).parent / "plugins"

print(f"Loading plugins from {plugin_dir}...")

for _, name, _ in pkgutil.iter_modules([str(plugin_dir)]):
    full_name = f"{plugin_package}.{name}"
    print(f"Loading {full_name}...")
    beacon.require(full_name)

if __name__ == "__main__":
    bot.launch_blocking()
