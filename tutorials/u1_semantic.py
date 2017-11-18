"""
The most complex model in unit 1 of ACT-R tutorials, 'semantic'.
"""

import pyactr as actr

semantic = actr.ACTRModel()

actr.chunktype("property", ("object", "attribute", "value"))

actr.chunktype("isMember", ("object", "category", "judgment"))

chunk_dict = {}
chunk_dict['shark'] = actr.makechunk(nameofchunk='shark', typename="elem", elem="shark")
chunk_dict['dangerous'] = actr.makechunk(nameofchunk='dangerous', typename="elem", elem="dangerous")
chunk_dict['locomotion'] = actr.makechunk(nameofchunk='locomotion', typename="elem", elem="locomotion")
chunk_dict['swimming'] = actr.makechunk(nameofchunk='swimming', typename="elem", elem="swimming")
chunk_dict['fish'] = actr.makechunk(nameofchunk='fish', typename="elem", elem="fish")
chunk_dict['salmon'] = actr.makechunk(nameofchunk='salmon', typename="elem", elem="salmon")
chunk_dict['edible'] = actr.makechunk(nameofchunk='edible', typename="elem", elem="edible")
chunk_dict['breathe'] = actr.makechunk(nameofchunk='breathe', typename="elem", elem="breathe")
chunk_dict['gills'] = actr.makechunk(nameofchunk='gills', typename="elem", elem="gills")
chunk_dict['animal'] = actr.makechunk(nameofchunk='animal', typename="elem", elem="animal")
chunk_dict['moves'] = actr.makechunk(nameofchunk='moves', typename="elem", elem="moves")
chunk_dict['skin'] = actr.makechunk(nameofchunk='skin', typename="elem", elem="skin")
chunk_dict['canary'] = actr.makechunk(nameofchunk='canary', typename="elem", elem="canary")
chunk_dict['color'] = actr.makechunk(nameofchunk='color', typename="elem", elem="color")
chunk_dict['sings'] = actr.makechunk(nameofchunk='sings', typename="elem", elem="sings")
chunk_dict['bird'] = actr.makechunk(nameofchunk='bird', typename="elem", elem="bird")
chunk_dict['ostrich'] = actr.makechunk(nameofchunk='ostrich', typename="elem", elem="ostrich")
chunk_dict['flies'] = actr.makechunk(nameofchunk='flies', typename="elem", elem="flies")
chunk_dict['category'] = actr.makechunk(nameofchunk='category', typename="elem", elem="category")
chunk_dict['height'] = actr.makechunk(nameofchunk='height', typename="elem", elem="height")
chunk_dict['tall'] = actr.makechunk(nameofchunk='tall', typename="elem", elem="tall")
chunk_dict['wings'] = actr.makechunk(nameofchunk='wings', typename="elem", elem="wings")
chunk_dict['flying'] = actr.makechunk(nameofchunk='flying', typename="elem", elem="flying")
chunk_dict['yellow'] = actr.makechunk(nameofchunk='yellow', typename="elem", elem="yellow")
chunk_dict['true'] = actr.makechunk(nameofchunk='true', typename="tv", value="true")
chunk_dict['false'] = actr.makechunk(nameofchunk='false', typename="tv", value="false")
    
dm = semantic.decmem

dm.add(set(chunk_dict.values()))

dm.add(actr.makechunk(typename="property", object=chunk_dict['shark'], attribute=chunk_dict['dangerous'], value=chunk_dict['true']))
dm.add(actr.makechunk(typename="property", object=chunk_dict['shark'], attribute=chunk_dict['locomotion'], value=chunk_dict['swimming']))
dm.add(actr.makechunk(typename="property", object=chunk_dict['shark'], attribute=chunk_dict['category'], value=chunk_dict['fish']))
dm.add(actr.makechunk(typename="property", object=chunk_dict['salmon'], attribute=chunk_dict['edible'], value=chunk_dict['true']))
dm.add(actr.makechunk(typename="property", object=chunk_dict['salmon'], attribute=chunk_dict['locomotion'], value=chunk_dict['swimming']))
dm.add(actr.makechunk(typename="property", object=chunk_dict['salmon'], attribute=chunk_dict['category'], value=chunk_dict['fish']))
dm.add(actr.makechunk(typename="property", object=chunk_dict['fish'], attribute=chunk_dict['breathe'], value=chunk_dict['gills']))
dm.add(actr.makechunk(typename="property", object=chunk_dict['fish'], attribute=chunk_dict['locomotion'], value=chunk_dict['swimming']))
dm.add(actr.makechunk(typename="property", object=chunk_dict['fish'], attribute=chunk_dict['category'], value=chunk_dict['animal']))
dm.add(actr.makechunk(typename="property", object=chunk_dict['animal'], attribute=chunk_dict['moves'], value=chunk_dict['true']))
dm.add(actr.makechunk(typename="property", object=chunk_dict['animal'], attribute=chunk_dict['skin'], value=chunk_dict['true']))
dm.add(actr.makechunk(typename="property", object=chunk_dict['canary'], attribute=chunk_dict['color'], value=chunk_dict['yellow']))
dm.add(actr.makechunk(typename="property", object=chunk_dict['canary'], attribute=chunk_dict['sings'], value=chunk_dict['true']))
dm.add(actr.makechunk(typename="property", object=chunk_dict['canary'], attribute=chunk_dict['category'], value=chunk_dict['bird']))
dm.add(actr.makechunk(typename="property", object=chunk_dict['ostrich'], attribute=chunk_dict['flies'], value=chunk_dict['false']))
dm.add(actr.makechunk(typename="property", object=chunk_dict['ostrich'], attribute=chunk_dict['height'], value=chunk_dict['tall']))
dm.add(actr.makechunk(typename="property", object=chunk_dict['ostrich'], attribute=chunk_dict['category'], value=chunk_dict['bird']))
dm.add(actr.makechunk(typename="property", object=chunk_dict['bird'], attribute=chunk_dict['wings'], value=chunk_dict['true']))
dm.add(actr.makechunk(typename="property", object=chunk_dict['bird'], attribute=chunk_dict['locomotion'], value=chunk_dict['flying']))
dm.add(actr.makechunk(typename="property", object=chunk_dict['bird'], attribute=chunk_dict['category'], value=chunk_dict['animal']))

actr.chunktype("isMember", ("object", "category", "judgment"))

#you can vary what will appear in goal buffer

#semantic.goal.add(actr.makechunk(typename="isMember", object=chunk_dict['canary'], category=chunk_dict['bird']))
semantic.goal.add(actr.makechunk(typename="isMember", object=chunk_dict['canary'], category=chunk_dict['animal']))
#semantic.goal.add(actr.makechunk(typename="isMember", object=chunk_dict['canary'], category=chunk_dict['fish']))

semantic.productionstring(name="initialRetrieve", string="""
        =g>
        isa     isMember
        object  =obj
        category =cat
        judgment None
        ==>
        =g>
        isa     isMember
        judgment 'pending'
        +retrieval>
        isa     property
        object  =obj
        attribute category""")

semantic.productionstring(name="directVerify", string="""
        =g>
        isa     isMember
        object  =obj
        category =cat
        judgment 'pending'
        =retrieval>
        isa     property
        object  =obj
        attribute category
        value   =cat
        ==>
        =g>
        isa     isMember
        judgment 'yes'""")

semantic.productionstring(name="chainCategory", string="""
        =g>
        isa     isMember
        object  =obj1
        category    =cat
        judgment    'pending'
        =retrieval>
        isa     property
        object  =obj1
        attribute   category
        value   =obj2
        value   ~=cat
        ==>
        =g>
        isa     isMember
        object  =obj2
        +retrieval>
        isa     property
        object  =obj2
        attribute category""")

semantic.productionstring(name="fail", string="""
        =g>
        isa     isMember
        object  =obj1
        category    =cat
        judgment    'pending'
        ?retrieval>
        state   error
        ==>
        =g>
        isa     isMember
        judgment 'no'""")

if __name__ == "__main__":
    x = semantic.simulation()
    x.run(1)
    print(semantic.goal.pop())

