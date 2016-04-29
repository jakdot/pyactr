"""
Example 3, semantics. Corresponds to semantic in ACT-R tutorials, Unit 1.
"""

from pyactr.model import ACTRModel

semantic = ACTRModel()

semantic.chunktype("property", ("object", "attribute", "value"))

semantic.chunktype("isMember", ("object", "category", "judgment"))

chunk_dict = {}
chunk_dict['shark'] = semantic.Chunk("elem", elem="shark")
chunk_dict['dangerous'] = semantic.Chunk("elem", elem="dangerous")
chunk_dict['locomotion'] = semantic.Chunk("elem", elem="locomotion")
chunk_dict['swimming'] = semantic.Chunk("elem", elem="swimming")
chunk_dict['fish'] = semantic.Chunk("elem", elem="fish")
chunk_dict['salmon'] = semantic.Chunk("elem", elem="salmon")
chunk_dict['edible'] = semantic.Chunk("elem", elem="edible")
chunk_dict['breathe'] = semantic.Chunk("elem", elem="breathe")
chunk_dict['gills'] = semantic.Chunk("elem", elem="gills")
chunk_dict['animal'] = semantic.Chunk("elem", elem="animal")
chunk_dict['moves'] = semantic.Chunk("elem", elem="moves")
chunk_dict['skin'] = semantic.Chunk("elem", elem="skin")
chunk_dict['canary'] = semantic.Chunk("elem", elem="canary")
chunk_dict['color'] = semantic.Chunk("elem", elem="color")
chunk_dict['sings'] = semantic.Chunk("elem", elem="sings")
chunk_dict['bird'] = semantic.Chunk("elem", elem="bird")
chunk_dict['ostrich'] = semantic.Chunk("elem", elem="ostrich")
chunk_dict['flies'] = semantic.Chunk("elem", elem="flies")
chunk_dict['category'] = semantic.Chunk("elem", elem="category")
chunk_dict['height'] = semantic.Chunk("elem", elem="height")
chunk_dict['tall'] = semantic.Chunk("elem", elem="tall")
chunk_dict['wings'] = semantic.Chunk("elem", elem="wings")
chunk_dict['flying'] = semantic.Chunk("elem", elem="flying")
chunk_dict['yellow'] = semantic.Chunk("elem", elem="yellow")
chunk_dict['true'] = semantic.Chunk("tv", value="true")
chunk_dict['false'] = semantic.Chunk("tv", value="false")
    
dm = semantic.DecMem()

dm.add(set(chunk_dict.values()))

dm.add(semantic.Chunk("property", object=chunk_dict['shark'], attribute=chunk_dict['dangerous'], value=chunk_dict['true']))
dm.add(semantic.Chunk("property", object=chunk_dict['shark'], attribute=chunk_dict['locomotion'], value=chunk_dict['swimming']))
dm.add(semantic.Chunk("property", object=chunk_dict['shark'], attribute=chunk_dict['category'], value=chunk_dict['fish']))
dm.add(semantic.Chunk("property", object=chunk_dict['salmon'], attribute=chunk_dict['edible'], value=chunk_dict['true']))
dm.add(semantic.Chunk("property", object=chunk_dict['salmon'], attribute=chunk_dict['locomotion'], value=chunk_dict['swimming']))
dm.add(semantic.Chunk("property", object=chunk_dict['salmon'], attribute=chunk_dict['category'], value=chunk_dict['fish']))
dm.add(semantic.Chunk("property", object=chunk_dict['fish'], attribute=chunk_dict['breathe'], value=chunk_dict['gills']))
dm.add(semantic.Chunk("property", object=chunk_dict['fish'], attribute=chunk_dict['locomotion'], value=chunk_dict['swimming']))
dm.add(semantic.Chunk("property", object=chunk_dict['fish'], attribute=chunk_dict['category'], value=chunk_dict['animal']))
dm.add(semantic.Chunk("property", object=chunk_dict['animal'], attribute=chunk_dict['moves'], value=chunk_dict['true']))
dm.add(semantic.Chunk("property", object=chunk_dict['animal'], attribute=chunk_dict['skin'], value=chunk_dict['true']))
dm.add(semantic.Chunk("property", object=chunk_dict['canary'], attribute=chunk_dict['color'], value=chunk_dict['yellow']))
dm.add(semantic.Chunk("property", object=chunk_dict['canary'], attribute=chunk_dict['sings'], value=chunk_dict['true']))
dm.add(semantic.Chunk("property", object=chunk_dict['canary'], attribute=chunk_dict['category'], value=chunk_dict['bird']))
dm.add(semantic.Chunk("property", object=chunk_dict['ostrich'], attribute=chunk_dict['flies'], value=chunk_dict['false']))
dm.add(semantic.Chunk("property", object=chunk_dict['ostrich'], attribute=chunk_dict['height'], value=chunk_dict['tall']))
dm.add(semantic.Chunk("property", object=chunk_dict['ostrich'], attribute=chunk_dict['category'], value=chunk_dict['bird']))
dm.add(semantic.Chunk("property", object=chunk_dict['bird'], attribute=chunk_dict['wings'], value=chunk_dict['true']))
dm.add(semantic.Chunk("property", object=chunk_dict['bird'], attribute=chunk_dict['locomotion'], value=chunk_dict['flying']))
dm.add(semantic.Chunk("property", object=chunk_dict['bird'], attribute=chunk_dict['category'], value=chunk_dict['animal']))

retrieval = semantic.dmBuffer("retrieval", dm)
    
g = semantic.goal("g")

semantic.chunktype("isMember", ("object", "category", "judgment"))

#you can vary what will appear in goal buffer

#g.add(semantic.Chunk("isMember", object=chunk_dict['canary'], category=chunk_dict['bird']))
#g.add(semantic.Chunk("isMember", object=chunk_dict['canary'], category=chunk_dict['animal']))
g.add(semantic.Chunk("isMember", object=chunk_dict['canary'], category=chunk_dict['fish']))

#production rules follow; they are methods that create generators: first yield yields buffer tests, the second yield yields buffer changes;
def initialRetrieve():
    yield {"=g":semantic.Chunk("isMember", object="=obj", category="=cat", judgment=None)}
    yield {"=g":semantic.Chunk("isMember", judgment="pending"), "+retrieval": semantic.Chunk("property", object="=obj", attribute=chunk_dict['category'])}

def directVerify():
    yield {"=g": semantic.Chunk("isMember", object="=obj", category="=cat", judgment="pending"), "=retrieval": semantic.Chunk("property", object="=obj", attribute=chunk_dict['category'], value="=cat")}
    yield {"=g": semantic.Chunk("isMember", judgment="yes")}

def chainCategory():
    yield {"=g": semantic.Chunk("isMember", object="=obj1", category="=cat", judgment="pending"), "=retrieval": semantic.Chunk("property", object="=obj1", attribute=chunk_dict['category'], value="=obj2~=cat")}
    yield {"=g":semantic.Chunk("isMember", object="=obj2"), "+retrieval": semantic.Chunk("property", object="=obj2", attribute=chunk_dict['category'])}

def fail():
    yield {"=g": semantic.Chunk("isMember", object="=obj1", category="=cat", judgment="pending"), "?retrieval": {'state':'error'}}
    yield {"=g": semantic.Chunk("isMember", judgment="no")}

semantic.productions(initialRetrieve, directVerify, chainCategory, fail)

if __name__ == "__main__":
    x = semantic.simulation()
    x.run(1)

