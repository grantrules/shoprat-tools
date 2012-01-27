import random
#### change these ####
#courselength = 16.0 # miles
courselength = random.uniform(16,20)
numsteps = 30 # how many separate changes in grade
maxgrade = 6 # maximum grade
mingrade = 0 - maxgrade # minimum grade

variation = .25 # variation in step length

#### don't change these ####
totaldistance = 0
avgsteplength = courselength / numsteps
stepstart = avgsteplength * (1 - variation)
stepend = avgsteplength * (1 + variation) 


header = """[COURSE HEADER]
UNITS = METRIC
DESCRIPTION = 2005 Ironman Brazil
FILE NAME = Ironman_Brazil.crs
;DISTANCE               GRADE           WIND
; COMMENTS
[END COURSE HEADER]

[COURSE DATA]
"""

csv = []


while totaldistance < courselength:
	# multiply by 100 for hundredths of a mile
	step = random.randrange(round(stepstart * 100), round(stepend * 100), 1) / 100.0
	# multiply grade by 10 for tenths
	grade = random.randrange(round(mingrade * 10), round(maxgrade * 10), 1) / 10.0
	#wind is the final column, 0 for that
	wind = 0

	totaldistance += step

	csv.append([step,grade,wind])

f = open('course.crs', 'w')

f.write(header)

for (step,grade,wind) in csv:
        f.write('{0:.2f}\t\t{1:.2f}\t\t{2:1d}\n'.format(step,grade,wind))


	


f.write('[END COURSE DATA]');
