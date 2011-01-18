import os
import sys

validPaths = []

for path in sys.path:
    if os.path.exists(os.path.join(path, 'openwns')):
        newPath = os.path.join(path, 'openwns')
        if os.path.join('lib', 'PyConfig') in newPath:
            validPaths.insert(0, newPath)
        else:
            validPaths.append(newPath)

if len(validPaths) == 0:
    raise ImportError('Cannot import module')

__path__ = validPaths

for path in validPaths:
    initPath = os.path.join(path, '__init__.py')
    if not os.path.exists(os.path.join(path, '__openwns__mainModule__.py')):
        try:
            execfile(initPath)
        except IOError:
            pass
