"""Configuration file for I, Monster."""

# curses key codes for direction keys
# 46 98 110 121 117 104 106 107 108
# .  b  n   y   u   h   j   k   l
directions = "46 98 110 121 117 104 106 107 108".split()

# time in minutes between pauses. 0 to turn off pauses
timeBetweenPauses = 15

# max pause time. It will range from 1 to this # in minutes
maxPauseTime = 4

# level map size
xmax = 79
ymax = 19
# xmax, ymax = 10, 10
# xmax, ymax = 1, 1
levels = 17

# names of maps, held in 'maps' shelve file
maps = ['empty', 'horizontal', 'block', 'small room', 'big room', 'cross']
#maps = ['empty', 'horizontal', 'vertical']
mode = "strategical"    # enter tactical when fighting
logf = None
auto_combat = False     # is set when there was successful auto combat

special_attacks = {
        "trap" : {
            "ally1"     : (("right", 1),),
            "ally2"     : (("down", 1),),
            "target"    : (("right", 1), ("down", 1)),
            },
        "arrow1" : {
            "ally1"     : (("right", 1),),
            "ally2"     : (("right", 1), ("down", 1)),
            "target"    : (("right", 2), ("up", 1)),
            },
        "arrow2" : {
            "ally1"     : (("up", 1),),
            "ally2"     : (("up", 1), ("left", 1)),
            "target"    : (("right", 1), ("up", 2)),
            },
        "arc" : {
            "ally1"     : (("up", 1), ("right", 1)),
            "ally2"     : (("down", 1), ("right", 1)),
            "target"    : (("right", 2),),
            },
        }

level_types = dict(
                  # level type -- level numbers
                  empty      = (1,2,3),
                  horizontal = (4,5,6),
                  block      = (7,8,9),
                  small_room = (10,11,12),
                  big_room   = (13,14,15),
                  cross      = (16,),
                  )

def log(*msg, end='\n'):
    end = end or ''
    if logf:
        msg = ', '.join([str(i) for i in msg])
        logf.write(msg + end)
        logf.flush()
