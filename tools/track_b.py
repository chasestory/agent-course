from common import write
from track_b1 import modules as part1
from track_b2 import modules as part2

track = {
    "id": "B",
    "title": "Track B — Ship Agents",
    "subtitle": "30 practical skills for building, operating, and showing off agents real people use.",
    "order": 2,
    "modules": part1 + part2,
}
assert len(track["modules"]) == 30, len(track["modules"])
write("../content/track-b-ship-agents.json", track)
