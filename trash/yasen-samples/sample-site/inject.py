import json, sys
d = json.load(open(sys.argv[1])); t = open('template.html').read()
open(sys.argv[2], 'w').write(t.replace('/*DATA*/null', json.dumps(d, separators=(',', ':'))))
