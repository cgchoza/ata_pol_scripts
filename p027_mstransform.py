import sys


inms = sys.argv[1]
outms = sys.argv[2]

mstransform(vis=inms, outputvis=outms, chanaverage=True, chanbin=8, antenna='!*&&&', datacolumn='data')
