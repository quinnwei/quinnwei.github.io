import pandas as pd
import numpy as np
import json
import sys
import math
import codecs

import psycopg2


def readFile(filename):
	with open(filename) as f:
		data=json.load(f)

	data_list = []
	for items in data['features']:
		obj_id = items['id']
		lat = items['geometry']['coordinates'][1]
		lon = items['geometry']['coordinates'][0]
		mag = items['properties']['mag']
		effective_radius = 225*2**(mag-4)
		title = items['properties']['title']
		time = items['properties']['time']
		data_list.append([obj_id,lat,lon,mag,effective_radius,title,time])
	return data_list

data = readFile('6_china_central.json')
data = pd.DataFrame(data,columns=['id','lat','lon','mag','effective_radius','title','time'])

def into_postgres(data):
	con = None
	# establish connection
	try:
		con = psycopg2.connect(database='dong_eq',user='Quinn',host='localhost',password='qingwei_1992')
		cur = con.cursor()
		cur.execute('select version()')
		ver = cur.fetchall()
		print ver

		# #create extension
		ext = "CREATE EXTENSION postgis"
		cur.execute(ext)
		con.commit()

		#create table
		create_table = """ CREATE TABLE location (id VARCHAR PRIMARY KEY,
			location GEOMETRY(POINT), mag NUMERIC, radius GEOMETRY(POLYGON),
			title VARCHAR, time NUMERIC)"""
		cur.execute(create_table)
		con.commit()

		# insert data into dable
		for index,row in data.iterrows():
			obj_id = row['id']
			lat = row['lat']
			lon = row['lon']
			mag = row['mag']
			radius = row['effective_radius']
			title =  row['title']
			time = row['time']

			point = "POINT(%s %s)"%(lon,lat)

			# cacluate the polygon
			delta_lat = radius/110.54
			delta_lon = radius/(111.320*math.cos(math.radians(delta_lat)))

			topleft_lat = lat+delta_lat
			topleft_lon = lon+delta_lon

			topright_lat = lat+delta_lat
			topright_lon = lon-delta_lon

			botleft_lat = lat-delta_lat
			botleft_lon = lon+delta_lon

			botright_lat = lat-delta_lat
			botright_lon = lon-delta_lon

			poly = "POLYGON((%s %s, %s %s, %s %s, %s %s,%s %s))"%(topleft_lon,topleft_lat,
															topright_lon,topright_lat,
															botright_lon,botright_lat,
															botleft_lon,botleft_lat,
															topleft_lon,topleft_lat)

			cmd = """ INSERT INTO location(id,location,mag,radius,title,time) VALUES
			(%s,ST_GeomFromText(%s,'4326'),%s,ST_GeomFromText(%s),%s,%s)"""
			print point
			print poly
			cur.execute(cmd,(obj_id,point,mag,poly,title,time))
			con.commit()
			print "inserted data %s" % (obj_id)



	except psycopg2.DatabaseError, e:
		print 'Error %s' %e
		sys.exit(1)
	finally:
		if con:
			con.close()




def inSide(point,left_bound,right_bound):
	lat,lon = point
	left_lat,left_lon = left_bound
	right_lat,right_lon = right_bound


	"""
	left_bound -----------
	|					  |
	|					  |
	|					  |
	|					  |
	|					  |
	|					  |
	|----------------right_bound
	"""
	# check top and bottom
	if (lat > left_lat):
		return False
	elif ( lat < right_lat):
		return False
	# check left and right
	elif (lon > left_lon):
		return False
	elif (lon < right_lon):
		return False
	else:
		return True
def checkWithin(point,data):
	mask = []
	for index,row in data.iterrows():
			obj_id = row['id']
			lat = row['lat']
			lon = row['lon']
			mag = row['mag']
			radius = row['effective_radius']
			title =  row['title']
			time = row['time']

			delta_lat = radius/110.54
			delta_lon = radius/(111.320*math.cos(math.radians(delta_lat)))

			topleft_lat = lat+delta_lat
			topleft_lon = lon+delta_lon

			topright_lat = lat+delta_lat
			topright_lon = lon-delta_lon

			botleft_lat = lat-delta_lat
			botleft_lon = lon+delta_lon

			botright_lat = lat-delta_lat
			botright_lon = lon-delta_lon

			print point,topleft_lat,topleft_lon,botright_lat,botright_lon

			within = inSide(point,(topleft_lat,topleft_lon),
								  (botright_lat,botright_lon))
			print within
			mask.append(within)
	return data[mask]

def makeJSON(data):
	output = {}
	for index,row in data.iterrows():
		singlerow = {}
		singlerow['lat'] = row['lat']
		singlerow['lon'] = row['lon']
		singlerow['mag'] = row['mag']
		singlerow['effective_radius'] = row['effective_radius']
		singlerow['title'] = row['title']
		singlerow['time'] = row['time']

		output[row['id']] = singlerow
	with open('pdata.json','w') as f:
		json.dump(output,f)

def readCities(fileName):
	f = codecs.open('china_cities_16.txt',encoding='utf-16-be')
	for line in f:
		with open ('unicode_test.txt','wb') as out:
			out.write(line.encode('utf16'))
	f.close()


temp_data = checkWithin((23.36,100.48),data)
readCities('china_cities_16.txt')





# into_postgres(data)

