from typing import Sequence

import crescent

__all__: Sequence[str] = ('start', 'end', 'delete', 'options', 'check', 'daily')

start = crescent.Group("start")
end = crescent.Group("end")
delete = crescent.Group("delete")
options = crescent.Group("options")
check = crescent.Group("check")
daily = check.sub_group('daily')
