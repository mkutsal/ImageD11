#!/usr/bin/env fable.python

from ImageD11.indexing import readubis, write_ubi_file
from ImageD11.refinegrains import refinegrains
import sys, os


def makemap(options):

    o = refinegrains()
    o.loadparameters(options.parfile)
    print "got pars"
    o.loadfiltered(options.fltfile)
    print "got filtered"
    o.readubis(options.ubifile)
    if options.symmetry is not "triclinic":
        # Grainspotter will have already done this
        print "transform to uniq"
        o.makeuniq(options.symmetry)
    print "got ubis"
    o.tolerance = float(options.tol)
    print "generating"
    o.generate_grains()
    print "Refining posi too"
    o.refineubis(quiet = False , scoreonly = True)
    print "Refining positions too"
    o.refinepositions()
    print "Done refining positions too"    
    o.refineubis(quiet = False , scoreonly = True)
    ul = [ o.grains[(g,options.fltfile)].ubi for g in o.grainnames ]
    write_ubi_file(options.newubifile, ul)


if __name__ == "__main__":
    import logging, sys
    
    console = logging.StreamHandler(sys.stdout)
    # set a format which is simpler for console use
    formatter = logging.Formatter('%(levelname)-8s : %(message)s')
    # tell the handler to use this format
    console.setFormatter(formatter)
    # add the handler to the root logger
    console.setLevel(logging.DEBUG)
    root = logging.getLogger('')
    root.addHandler(console)
    root.setLevel(logging.DEBUG) # should we process everything...?

    from optparse import OptionParser

    parser = OptionParser()
  
    
    parser.add_option("-p",  "--parfile", action="store",
                      dest="parfile", type="string",
                      help="Name of parameter file")
    parser.add_option("-u",  "--ubifile", action="store",
                      dest="ubifile", type="string",
                      help="Name of ubi file")
    parser.add_option("-U",  "--newubifile", action="store",
                      dest="newubifile", type="string",
                      help="Name of new ubi file to output")
    parser.add_option("-f",  "--fltfile", action="store",
                      dest="fltfile", type="string",
                      help="Name of flt file")
    parser.add_option("-t", "--tol", action="store",
                      dest="tol", type="float",
                      default =   0.5,
                      help="Tolerance to use in peak assignment")
    lattices = ["cubic", "hexagonal", "trigonal",
                "tetragonal", "orthorhombic", "monoclinic_a",
                "monoclinic_b","monoclinic_c","triclinic"]
    parser.add_option("-s", "--sym", action="store",
                      dest="symmetry", type="choice",
                      default = "triclinic",
                      choices = lattices,
                      help="Lattice symmetry for choosing orientation")


    
    options, args = parser.parse_args()

    for name in ["parfile" , 
                 "ubifile", 
                 "newubifile",
                 "fltfile"]:
        if getattr(options, name) is None:
            parser.print_help()
            logging.error("Missing option "+name)
            import sys
            sys.exit()

        
    try:
        makemap(options)
    except:
        parser.print_help()
        import traceback
        logging.error("An error occurred, details follow")
        traceback.print_exc()
