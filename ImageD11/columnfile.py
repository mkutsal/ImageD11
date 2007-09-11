

# ImageD11_v1.0 Software for beamline ID11
# Copyright (C) 2005-2007  Jon Wright
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  0211-1307  USA


from ImageD11 import parameters

import numpy.oldnumeric as n

FLOATS = [
    "fc",
    "sc", 
    "omega",
    "f_raw",
    "s_raw",
    "sigf",
    "sigs",
    "covsf",
    "sigo",
    "covso",
    "covfo",
    "sum_intensity",
    "IMax_int",
    "IMax_o",
    "avg_intensity",
    "Min_o",
    "Max_o",
    "dety",
    "detz",
    ]

INTS = [
    "Number_of_pixels",
    "IMax_f",
    "IMax_s",
    "Min_f",
    "Max_f",
    "Min_s",
    "Max_s"
    ]
FORMATS = {}


# Make a dictionary for formatstrings when writing files
for f in FLOATS: 
    FORMATS[f] = "%.4f"
for f in INTS:
    FORMATS[f] = "%.0f"

def clean(sl): 
    """ trim whitespace from titles """
    return [s.lstrip().rstrip() for s in sl]

class columnfile:
    def __init__(self, filename):
        self.filename = filename
        self.readfile(filename)

    def writefile(self, filename):
        """
        write an ascii columned file
        """
        self.parameters.saveparameters(filename)
        fo = open(filename,"w+") # appending
        fo.write("#")
        fs = ""
        for t in self.titles:
            fo.write("  %s"%(t))
            try:
                fs += "  %s"%(FORMATS[t])
            except KeyError:
                fs += "  %f"
        fo.write("\n")
        fs += "\n"
        for i in range(self.nrows):
            fo.write(fs % tuple(self.bigarray[:,i]))
        fo.close()

    def readfile(self, filename):
        """
        Reads in an ascii columned file
        """
        self.titles = []
        self.bigarray = None
        self.ncols = 0
        self.nrows = 0
        self.parameters = parameters.parameters(filename=filename)
        data = []
        i = 0
        try:
            fileobj = open(filename,"r")
        except:
            raise Exception("Cannot open %s for reading"%(filename))
        for line in fileobj:
            i += 1
            if len(line.lstrip())==0:
                # skip blank lines
                continue
            if line[0] == "#":
                # title line
                if line.find("=") > -1:
                    # key = value line
                    name, value = clean(line[1:].split("="))
                    self.parameters.addpar(
                        parameters.par( name, value ) )
                else:
                    self.titles = clean(line[1:].split())
                    self.ncols = len(self.titles)
                continue
            # Assume a data line
            try:
                vals = [ float(v) for v in line.split() ]
            except:
                raise Exception("Non numeric data on line\n"+line)
            if len(vals) != self.ncols:
                raise Exception("Badly formatted column file\n"\
                                    "expecting %d columns, got %d\n"\
                                    " line %d in file %s"%
                                (self.nvalues,len(vals),
                                 i,self.filename))
            self.nrows += 1
            data.append(vals)
        self.bigarray=n.transpose(n.array(data))
        assert self.bigarray.shape == (self.ncols, self.nrows)
        self.set_attributes()

    def set_attributes(self):
        """
        Set object vars to point into the big array
        """
        for t,i in zip(self.titles,range(len(self.titles))):
            setattr(self, t, self.bigarray[i])
            assert getattr(self,t).shape == (self.nrows,)

    def filter(self, mask):
        """
        mask is an nrows long array of true/false
        """
        if len(mask) != self.nrows:
            raise Exception("Mask is the wrong size")
        self.nrows = n.sum(n.compress(mask, n.ones(len(mask))))
        self.bigarray = n.compress(mask, self.bigarray, axis = 1)
        assert self.bigarray.shape == (self.ncols, self.nrows)
        self.set_attributes()
 
    
                          
        
