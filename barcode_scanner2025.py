from pyzbar.pyzbar import decode
from PIL import Image
from pdf2image import convert_from_path
import os, glob
import re
import json
import subprocess
import time
import datetime

Image.MAX_IMAGE_PIXELS = None

#If there is no data file (.json),
#the program must create one with
#the following files:

#regex.txt:
#1st line -> the regex for valid bar codes

#paths.txt:
#1st line -> full path to folder to process
#2nd line -> full path to folder for failed scans
#3rd line -> full path to folder for successful scans

#department.txt:
#1st line -> name of the department

#barcodes.csv:
#1st line, n-1 elements -> all valid barcode types separated by commas
#1st line n-th element -> delimiter: this determines the naming convention for folders
#ie: AS25012345, delimiter=2 -> folder name "AS"
#ie: AS25012345, delimiter=4 -> folder name "AS25"

def getData():

	d = {}

	def find_json():
	
		json_f = {}
    
		try:
			with open(f"{CWD}\\data.json", "r") as f:
				json_f = json.load(f)
			return json_f
		except FileNotFoundError:
			print("JSON file not found. Generating from data files...")
			return False
		except json.JSONDecodeError:
			print("JSON issue")
			return False

	def find_conf():

		json_conf = {}

		try:
			regx_file = open(f"{CWD}\\regex.txt", "r")
			regx = regx_file.readline()
			path_file = open(f"{CWD}\\paths.txt", "r")
			paths = []
			dprt_file = open(f"{CWD}\\department.txt", "r")
			dprt = dprt_file.readline()
			bar_types_file = open(f"{CWD}\\barcodes.csv", "r")
			bar_types = bar_types_file.readline()
			while True:
				line = path_file.readline()
				line = line.replace('\n', '')
				if (line == ''):
					break
				paths.append(line)

		except FileNotFoundError:
			print("No data file found.")
			return False

		else:

			json_conf['regex'] = regx.strip()
			json_conf['to_process'] = paths[0].strip()
			json_conf['failed'] = paths[1].strip()
			json_conf['success'] = paths[2].strip()
			json_conf['dprt'] = dprt.strip()
			types = bar_types.strip().split(',')
			json_conf['bar_types'] = types[:-1]
			json_conf['delimiter'] = int(types[-1])

			regx_file.close()
			path_file.close()
			dprt_file.close()
			bar_types_file.close()

			json_file = json.dumps(json_conf, indent=4)
			with open(f"{CWD}\\data.json", "w") as output:
				output.write(json_file)
            
			return json_conf
	
	d = find_json()

	if not d:
		d = find_conf()

	return d 

def process(index, filename, f_ex):

	try:
		print(filename)
		if (f_ex == 'pdf'):
			doc = convert_from_path(filename, dpi=300, poppler_path=POPPLER_PATH)
		elif (f_ex == 'tif'):
			doc = [Image.open(filename).convert('RGB')]
	except Exception as e:
		
		print(e)
		ind = 1
		print("Couldn't read.")
		if not os.path.isfile("%s\\UNREADABLE.pdf" % DATA['failed']):
			os.rename(filename, "%s\\UNREADABLE.pdf" % DATA['failed'])
		else:
			while os.path.isfile("%s\\UNREADABLE%i.pdf" % (DATA['failed'], ind)):
				ind += 1
			os.rename(filename, "%s\\UNREADABLE%s.pdf" % (DATA['failed'], ind))
		return index-1
	else:
		print('Scanning...')
		doc_len = len(doc)
		page_num = 1

		while len(doc) > 0:
			
			page = doc.pop(0)
			#page.show()
			if resample(page):
				print(f"Scanned {page_num} of {doc_len} pages.")
				page_num += 1
				page.close()
			else:
				print("Could not read page. Sending to review folder.")
				
				fn = filename.split("\\")[-1][:-4]
				f_ext = filename.split("\\")[-1][-4:]
				indexSave(page, f"{DATA['failed']}\\{fn} ({page_num}){f_ext}")

		print("Removed {}".format(filename))
		os.remove(filename)
		return index-1

def resample(d):
    
	pages = [];
	
	for i in range(0, 105, 15):
		pages.append(d.rotate(i, expand=True, fillcolor='white'))

	scans = [decode(scan) for scan in pages]

	p = pages[0]; pages = pages[1:]

	for page in pages:
		page.close()
	del pages

	return analyze(scans, p)

def analyze(s, p):

	mem = []; codes = [];

	for scan in s:
		for code in scan:
			if code.data not in [c.data for c in codes]:
				codes.append(code)
				print(code.data.decode('utf-8'))
    
	for code in codes:
		data = code.data.decode('utf-8').lower()
		if code.type not in DATA['bar_types']:
			print('%s -> Error: invalid type: %s' % (data, code.type))
			mem.append(code)
		elif (re.search(DATA['regex'], data) == None):
			print('%s -> Error: invalid pattern.' % data)
			mem.append(code)
		else:
			print("SUCCESS")

	for element in mem:
		codes.remove(element)
	
	print(list([code.data.decode('utf-8').lower() for code in codes]))
	print(list([el.data.decode('utf-8').lower() for el in mem]))
	return saveReq(codes, mem, p)

def indexSave(f, path):

	i = 2

	try:
		if not os.path.isfile("%s.pdf" % path):
			f.save("%s.pdf" % path, 'PDF')
		else:
			while os.path.isfile("%s%i.pdf" % (path, i)):
				i += 1
			f.save("%s%i.pdf" % (path, i), 'PDF')
	except:
		print("Could not save file.")
		f.close()
		return False
	else:
		f.close()
		return True

def createFolder(path):

	if not os.path.isdir(path):
		os.makedirs(path)

def saveReq(c, m, p):
    
	if not c:
		print("No %s label identified" % DATA['dprt'])
		for el in m:
			print(el.data)
			print(el.type)
		if not m:
			return indexSave(p, "%s\\UNLABELED" % DATA['failed'])
		else:
			name = re.sub(r'\W', '_', m[0].data.decode('utf-8'))
			try:
				return indexSave(p, "%s\\UNLABELED_%s" % (DATA['failed'], name))
			except:
				return indexSave(p, "%s\\UNLABELED" % DATA['failed'])
                
	elif len(set([code.data.decode('utf-8') for code in c])) > 1:
        
		print("Multiple %s labels identified. Please review." % DATA['dprt'])
		try:
			return indexSave(p, "%s\\MULTIPLE_%s_LABELS" % (DATA['failed'], DATA['dprt'].upper()))
		except:
			p.close()
			return False

	else:
        	
		case_type = c[0].data.decode('utf-8')[:DATA['delimiter']].upper()
		case_num = re.sub(r'\W', '_', c[0].data.decode('utf-8').upper())

		try:
			createFolder("%s\\%s" % (DATA['success'], case_type))
			if not os.path.isfile("%s\\%s\\%s.pdf" % (DATA['success'], case_type, case_num)):
				p.save("%s\\%s\\%s.pdf" % (DATA['success'], case_type, case_num), 'PDF')
			else:
				multi_page = convert_from_path("%s\\%s\\%s.pdf" % (DATA['success'], case_type, case_num), dpi=300, poppler_path=POPPLER_PATH)
				size = multi_page[0].size
				multi_page = [page.resize(size, resample=0) for page in multi_page]
				p.save("%s\\%s\\%s.pdf" % (DATA['success'], case_type, case_num), 'PDF', save_all=True, append_images=multi_page)
				for page in multi_page: page.close()
		except Exception as e:
			print(e)
			return False
		else:
			p.close()
			return True

CWD = os.path.dirname(os.path.realpath(__file__))
TIME = datetime.datetime.fromtimestamp(time.time()).strftime("%Y-%S-%d.%X")
print(TIME)
DATA = getData()
if (DATA == False):
	exit()

ind = 12000
POPPLER_PATH = f"{CWD}\\poppler\\Library\\bin"
createFolder(DATA['failed'])

pdfs = glob.glob('%s\*.pdf' % DATA['to_process'])
tifs = glob.glob('%s\*.tif' % DATA['to_process'])

print(DATA)

while ind > 0:
	if pdfs:
		ind = process(ind, pdfs.pop(), 'pdf')
	elif tifs:
		ind = process(ind, tifs.pop(), 'tif')
	else:
		break
