import re
import matplotlib.pyplot as plt
import numpy as np
fname=raw_input('enter filename:')
print 'attempt to read file...'
try:
	fobj=open(fname,'r')
except IOError,e:
	print '%s open error' % (fname),e
else:
	data='';
	for line in fobj:
		data+=(str(line))
	pattern=re.compile(']\W+(\d+)\..*?sec.*?KBytes\W+([0-9\.]+)\W+[MK]bits.*?([0-9\.]+)\W+ms.*?([0-9\.]+)%',re.S)
	items=re.findall(pattern,data)
	x=[]
	y=[]
	for item in items:
#print item
		seq=int(item[0])
		b=float(item[1])
		if b<10.0:
			b=b*125.0
		else:
			b=b/8.0
		j=float(item[2])
		loss=float(item[3])/100.0
		print '%d\t%.1f' % (seq,b)
		x.append(seq)
		y.append(b)
#print '%d\t%.3f\t%.3f\t%.3f' % (seq,b,j,loss)
#print line
	fobj.close()
	x=x[0:-1]
	y=y[0:-1]
	plt.figure(1)
	plt.plot(x,y)
	plt.show()
