import math, numpy, matplotlib
from xml.dom import minidom
from array import array


# linear smooth func. from http://www.scipy.org/Cookbook/SignalSmooth
def smooth(x,window_len=11,window='hanning'):
	"""smooth the data using a window with requested size.
	
	This method is based on the convolution of a scaled window with the signal.
	The signal is prepared by introducing reflected copies of the signal 
	(with the window size) in both ends so that transient parts are minimized
	in the begining and end part of the output signal.
	
	input:
		x: the input signal 
		window_len: the dimension of the smoothing window; should be an odd integer
		window: the type of window from 'flat', 'hanning', 'hamming', 'bartlett', 'blackman'
			flat window will produce a moving average smoothing.

	output:
		the smoothed signal
		
	example:

	t=linspace(-2,2,0.1)
	x=sin(t)+randn(len(t))*0.1
	y=smooth(x)
	
	see also: 
	
	numpy.hanning, numpy.hamming, numpy.bartlett, numpy.blackman, numpy.convolve
	scipy.signal.lfilter
 
	TODO: the window parameter could be the window itself if an array instead of a string   
	"""

	if x.ndim != 1:
		raise ValueError, "smooth only accepts 1 dimension arrays."

	if x.size < window_len:
		raise ValueError, "Input vector needs to be bigger than window size."


	if window_len<3:
		return x


	if not window in ['flat', 'hanning', 'hamming', 'bartlett', 'blackman']:
		raise ValueError, "Window is on of 'flat', 'hanning', 'hamming', 'bartlett', 'blackman'"


	s=numpy.r_[2*x[0]-x[window_len-1::-1],x,2*x[-1]-x[-1:-window_len:-1]]
	#print(len(s))
	if window == 'flat': #moving average
		w=numpy.ones(window_len,'d')
	else:
		w=eval('numpy.'+window+'(window_len)')

	y=numpy.convolve(w/w.sum(),s,mode='same')
	return y[window_len:-window_len+1]

def meters_to_feet(meters):
	return meters * 3.2808399

def feet_to_meters(feet):
	return feet / 3.2808399

def grade(distance, elevation):
	return (elevation * 100) / (distance * 1000)

def coords_to_feet((lat1, long1),(lat2, long2)):
	(lat1, long1, lat2, long2) = math.radians(lat1), math.radians(long1), math.radians(lat2), math.radians(long2)
	distance = math.acos(math.sin(lat1)*math.sin(lat2) + math.cos(lat1)*math.cos(lat2) * math.cos(long2-long1))
	return distance * 6371


xmldoc = minidom.parse('doink.xml')
coordlist = xmldoc.getElementsByTagName('trkpt')
lat1 = None;
long1 = None;

coords = []
elevation = []

for coord in coordlist:
	ele = float(coord.getElementsByTagName('ele')[0].firstChild.nodeValue)
	(lat2, long2) = (float(coord.attributes["lat"].value), float(coord.attributes["lon"].value))
	if lat1 != None and (lat1, long1) != (lat2, long2):
		dif = coords_to_feet((lat1, long1), (lat2, long2))
		coords.append(dif)
		elevation.append(ele)
	(lat1, long1) = (lat2, long2)


x = []
y = []
z = []
e = []
last = 0
last2 = None

j = numpy.array(elevation)
elevation = smooth(j)
for a,b in zip(coords,elevation):
	last+=a
	x.append(last)
	y.append(b)
	if last2 == None:
		last2 = b
	e.append(grade(a,(b-last2)))
	last2 = b
j = numpy.array(y)
z = smooth(j)
matplotlib.use('Agg')
import matplotlib.pyplot as plt
plt.figure(4)
plt.subplot(511)
plt.plot(x,y)
plt.subplot(512)
plt.plot(x,e)
plt.subplot(513)
plt.plot(x,z)
plt.subplot(514)
a = smooth(numpy.array(e))
plt.plot(x,a)
plt.savefig('out.png')


# simplify this sheeit
simplegraph = []
dis = []
ele = []
grp = 3
for i,(n,m) in enumerate(zip(coords,a)):
	if len(dis) > 5:
		avg = numpy.average(ele)
#		print "avg: {0}, ele: {1}".format(avg,m)
		if abs(avg - m) > .5:
#			print "BREAK. adding point: {0:.2f}, {1:.2f}".format(sum(dis), avg)
			simplegraph.append((sum(dis),avg))
			ele = []
			dis = []
	dis.append(n)
	ele.append(m)
	

x =[]
y = []
for (a,b) in simplegraph:
	x.append(a)
	y.append(b)

plt.subplot(515)
z = [sum(x[:i]) for i in range(0,len(x))]

plt.plot(z,y)
plt.savefig('out.png')
		

# create file
f = open('course.crs', 'w')

header = """[COURSE HEADER]
UNITS = METRIC
DESCRIPTION = 2005 Ironman Brazil
FILE NAME = Ironman_Brazil.crs
;DISTANCE		GRADE		WIND
; COMMENTS
[END COURSE HEADER]

[COURSE DATA]
"""
f.write(header)
	
for coord,grade in simplegraph:
	f.write('{0:.2f}\t\t{1:.2f}\t\t0\n'.format(coord,grade))

f.close()

print "Condensed {0} points in the GPS into {1} points for a total of {2:.2f} km".format(len(coordlist), len(simplegraph), sum(x))
