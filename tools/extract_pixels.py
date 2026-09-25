import json
g=json.load(open('grid.json'))
ref={'.':(107,132,148),'K':(0,0,0),'S':(169,141,103),'B':(157,113,57),'C':(118,35,176),'L':(168,101,212),'G':(150,217,218)}
def cl(v): return min(ref,key=lambda k:sum((a-b)**2 for a,b in zip(ref[k],v)))
A=[''.join(cl(v) for v in row) for row in g]
json.dump(A,open('ascii.json','w'))
for i,r in enumerate(A): print(f'{i:2d} {r}')
