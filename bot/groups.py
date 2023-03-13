from typing import Sequence

import crescent

timer = crescent.Group("timer")
timesheet = crescent.Group("timesheet")
options = timesheet.sub_group("options")
reminder = crescent.Group("reminder")
jobstores = crescent.Group("jobstores")

__all__: Sequence[str] = (
    "timer",
    "timesheet",
    "options",
    "reminder",
    "jobstores",
)
