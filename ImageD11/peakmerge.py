

# ImageD11_v0.4 Software for beamline ID11
# Copyright (C) 2005  Jon Wright
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA


"""
Class for reading peaksearch files, merging peaks on adjacent frames
and writing out the result...

TODO : Replace with the 3D blobsearchers - this algorithm uses a lot
of memory
"""

import Numeric
import time,sys


def roundfloat(x,tol):
   """
   Return the float nearest to x stepsize tol
   """
   return x.__divmod__(tol)[0]*tol

# print "Using omega tolerance of 1e-5"

class peak:
   """
   Represents a peak
   """
   def __init__(self,line,omega,threshold,num,tolerance):
      """
      line = line in the outputfile from peaksearch
      omega = omega rotation angle
      threshold = the threshold level when the peak was found
      tolerance = the distance (pixels) between peak centres for merging
      """
      self.TOLERANCE = tolerance # Pixel separation for combining peaks
      self.omegatol=1e-5
      self.omega=roundfloat(omega,self.omegatol) # round to nearest
      self.num=num
      self.line=line
      self.threshold=threshold
      v = [float(x) for x in line.split()]
      self.np=v[0]
      self.avg=v[1]
      self.x=v[2]
      self.y=v[3]
      self.xc=v[4]
      self.yc=v[5]
      self.sigx=v[6]
      self.sigy=v[7]
      self.covxy=v[8]
      self.forgotten=False
      
   def combine(self,other):
      """
      Combine this peak with another peak (eg merge!)
      #
      # If the thresholds are different, we see the same peaks
      # twice. We will just pick the one with the lower threshold
      # 
      # Otherwise we try to average them
      #
      """
      if self.threshold < other.threshold and self.omega==other.omega:
         other.forgotten=True
         return self
      else:
         if self.threshold > other.threshold and self.omega==other.omega:
            self.forgotten=True
            return other
         else:
            np = self.np + other.np
            threshold=self.threshold
            s = self.avg*self.np + other.avg*other.np
            avg = s/np
            omega = (self.omega*self.np*self.avg + other.omega*other.np*other.avg)/s
            num   = (self.num  *self.np*self.avg + other.num  *other.np*other.avg)/s
            x     = (self.x    *self.np*self.avg + other.x    *other.np*other.avg)/s
            y     = (self.y    *self.np*self.avg + other.y    *other.np*other.avg)/s
            xc    = (self.xc   *self.np*self.avg + other.xc   *other.np*other.avg)/s
            yc    = (self.yc   *self.np*self.avg + other.yc   *other.np*other.avg)/s
            sigx  = (self.sigx *self.np*self.avg + other.sigx *other.np*other.avg)/s
            sigy  = (self.sigy *self.np*self.avg + other.sigy *other.np*other.avg)/s
            covxy = (self.covxy*self.np*self.avg + other.covxy*other.np*other.avg)/s
            self.forgotten=True
            other.forgotten=True
            # Make a new line
            line = "%d  %f    %f %f   %f %f    %f %f %f"%(np,avg,x,y,xc,yc,sigx,sigy,covxy)
            return peak(line,omega,threshold,num,self.TOLERANCE)
         
   def __cmp__(self,other):
      """
      For sorting - depreciated by DSU
      """
      if self.omega - other.omega > self.omegatol:
         return 1
      if self.omega - other.omega < -self.omegatol:
         return -1
      if self.xc - other.xc > self.TOLERANCE:
         return -1
      if self.xc - other.xc < -self.TOLERANCE:
         return 1
      # xc within tol
      if self.yc - other.yc > self.TOLERANCE:
         return -1
      if self.yc - other.yc < -self.TOLERANCE:
         return 1
      return 0
      
   def __eq__(self,other):
      """
      For deciding if peaks overlap
      """
      try:
#           print "using __eq__"
           if abs(self.xc - other.xc) < self.TOLERANCE and abs(self.yc - other.yc) < self.TOLERANCE :
              return True
           else:
              return False
      except:
            print self,other
            raise

   def __str__(self):
      """
      for printing something
      """
      return "Peak xc=%f yc=%f omega=%f"%(self.xc,self.yc,self.omega)

   def __repr__(self):
      """
      Not sure that this is used, again, for printing
      """
      return "Peak xc=%f yc=%f omega=%f"%(self.xc,self.yc,self.omega)

class pkimage:
   """
   Contains the header information from an image
   Also pointers to positions of lines in peaksearch output file
   """
   def __init__(self,name):
      """ name is the filename """
      self.name=name
      self.header={}
      self.header["File"]=name
   def addtoheader(self,headerline):
      """ 
      save header info in dict
      headerline is line starting with # in peaksearch output
      """
      if headerline.find("=")>0:
         h,v=headerline[1:].split("=")
         self.header[h.lstrip().rstrip()]=v
         if h.lstrip().rstrip() == "ANGLES":
            # Got the Bruker angles
            # map them to ImageD11 geometry
            vals = v.split()
            self.header["TWOTHETA"]=vals[0]
            self.header["THETA"] = vals[1]
            self.header["Omega"] = vals[2] # sorry
            self.header["CHI"]=vals[3]   
         return
      else:
         self.otherheaderstuff(headerline)

   def otherheaderstuff(self,headerline):
      """
      Hard to parse header info - called by addtoheader
      """
      if headerline.find("Processed")>0:
         return
      if headerline.find("Spatial")>0:
         return
      if headerline.find("Threshold")>0:
         return
      if headerline.find("SPLINE")>0:
         return
      if headerline.find("Number_of_pixels")>0:
         return
      else: # No equals sign means a threshold level or titles
         raise Exception("Cannot interpret %s"%(headerline))



class peakmerger:
   """
   The useful class - called by the gui to process peaksearch output
   into spots
   """
   def __init__(self,quiet="No"):
      """
      object to read in peaksearch output file and merge the peaks
      quiet arg decides if we spray stdout
      """
      self.quiet=quiet
      #print "I am in quiet mode",quiet
      self.lines=None
      self.allpeaks=None
      self.merged=None
      self.final=None
      self.tolerance=4.0

   def setpixeltolerance(self,tolerance=2):
      """ ah... if only """
      pass

   def readpeaks(self,filename,startom=0.,omstep=0.):
      """
      Read in the output from the peaksearching script
      Filename is the output file
      optionally startom and omstep fill in omega ONLY if missing in file
      """
      self.lines = open(filename,"r").readlines()
      # Get a list of filenames, omega angles
      self.images=[]
      i=-1
      for line in self.lines:
         i+=1
#         print line[0:5]
         if line[0:6]=="# File":
            name = line.split()[-1]
            currentimage=pkimage(name)
            self.images.append(currentimage)
            if name.find("edf")>-1:
               try:
                  imagenumber = int(name[-8:-4])
               except:
                  imagenumber = -1
            else:
               try:
                  imagenumber = int(name.split(".")[-1])
               except:
                  imagenumber=-1
            currentimage.linestart=i
            currentimage.imagenumber=imagenumber
            continue
         if line[0]=="#":
            currentimage.addtoheader(line)
            continue
      self.imagenumbers=Numeric.zeros(len(self.images),Numeric.Int)
      self.omegas      =Numeric.zeros(len(self.images),Numeric.Float)
      i=0
      while i < len(self.images):
         self.imagenumbers[i]=int(self.images[i].imagenumber)
         try:
            self.omegas[i]      =float(self.images[i].header["Omega"])
         except:
            # Oh dear, you have no Omega in your header
            #
            om = startom + i*omstep
            self.images[i].header["Omega"]=om
            self.omegas[i]=om
         i=i+1
      print "Found",len(self.images),"images"
                     
   def harvestpeaks(self, numlim=None, omlim=None, thresholds=None):
      """
      Harvests the peaks from the images within a range of 
      imagenumbers and/or omega
      eg: it actually reads the numbers now
      """
      # Check we have read in a file already
      if self.lines==None:
         # we have not read the file yet!
         raise Exception("You need to read in a peaksearch output file first!")
      start=time.time()
      peaks=[]
      # We now have the ranges in imagenumber and omega if requested
      if numlim is None:
         numinrange = lambda x : True
      else:
         numinrange = lambda x : x > min(numlim) and x < max(numlim)
      if omlim is None:
         ominrange = lambda x : True
      else:
         ominrange = lambda x : x > min(omlim) and x < max(omlim)
      if thresholds is None:
         thresholdsinrange = lambda x : True
      else:
         thresholdsinrange = lambda x : x > min(thresholds) and x < max(thresholds)
      i=0
      for image in self.images:
         # Check
         om=float(image.header["Omega"])
         #print "%50.40f %s"%(om,image.header["Omega"]),
         # print om
         if numinrange(image.imagenumber) and ominrange(om):
               # Read peaks
               i=image.linestart+1
               line=self.lines[i]
               maxi=len(self.lines)-1
               npks=0
               while line.find("# File") < 0 and i < maxi:
                  if line.find("Threshold")>0:
                     threshold=float(line.split()[-1])
                  if line[0]!='#' and len(line)>10 and thresholdsinrange(threshold):
                     p=peak(line, om, threshold, image.imagenumber, self.tolerance)
                     peaks.append(p)                     
                     npks=npks+1
                  i=i+1
                  line=self.lines[i]
         else:
            print "Rejected",numinrange(image.imagenumber), ominrange(om)
      print "Time to read into lists",time.time()-start
      start=time.time()
      # DSU - decorate, sort, undecorate
      sortable = [ (p.omega,p.xc,p.yc,p) for p in peaks ]
      sortable.sort()
      self.allpeaks = [ t[3] for t in sortable ]
      print "Time to DSU sort:",time.time()-start,len(peaks)      
#      # Sort by omega, then x, then y
#      peaks.sort()
#      print "Time to sort:",time.time()-start,len(peaks)      
#      self.allpeaks=peaks
                        
   def mergepeaks(self):
      """
      Merges peaks together - if they overlap and are on adjacent frames

      More complex than initially planned
      """
      if self.allpeaks==None:
         self.harvestpeaks()
      if self.allpeaks==None:
         raise Exception("There are no peaks to merge yet (read+harvest first)")
      start=time.time()
      npeaks=len(self.allpeaks)
      print "len(self.allpeaks)",len(self.allpeaks)
      merge1=[self.allpeaks[0]]
      i=1
      while i < npeaks:
         # merge peaks with same omega values
         if self.allpeaks[i] == merge1[-1] and abs(self.allpeaks[i].omega - merge1[-1].omega) < merge1[-1].omegatol:
            merge1[-1]=merge1[-1].combine(self.allpeaks[i])
         else:
            merge1.append(self.allpeaks[i])
         i=i+1
      peaks=merge1
      npeaks=len(peaks)
      print "After merging equivalent omegas",npeaks,time.time()-start
      # Now merge the same peak on adjacent omega angles.
      # First make a list of unique omega angles
      i=0
      start=time.time()
      uniq={}
      olast = -1e9
      while i < npeaks:
         omega = peaks[i].omega
         if omega > olast:
            olast=omega
            uniq[omega]=i
         else:
            pass
            #ok
            #raise Exception("Peaks apparently not sorted by omegas!!! "+str(i)+" "+str(peaks[i].omega)+" "+str(peaks[i-1].omega))
         i=i+1
      # 
      nomega=len(uniq.keys())
      print "Number of different omegas=",nomega,time.time()-start
      # Now merge peaks with adjacent omega angles
      # Need to find peaks which match each other
      # Different threshold levels should already have been merged
      start=time.time()
      i=0
      merged=[]
      keys=uniq.keys()
      keys.sort()
      #print keys
      prevframe=[]
      while i < nomega-2:
         first=uniq[keys[i]]
         last =uniq[keys[i+1]]
         if last < first:
            raise Exception("Keysort problem")
         #print first,last
         #
         # Active peaks are present on the current frame
         # These can merge with the next frame
         #
         active=peaks[first:last]
         check=len(active)+len(prevframe)
         ncarry=len(prevframe)
         active=active+prevframe
         prevframe=[]
         if len(active) != check:
            raise "Problem here - lost something"
         nextlast =uniq[keys[i+2]]
         nextframe=peaks[last:nextlast]
         om=keys[i]
         print "Setting %-5d  %8f with %-6d peaks on this and %-5d peaks on next, %-5d in buffer\r"%(i,om,last-first,nextlast-last,ncarry),
         sys.stdout.flush()
         for peak1 in active:
            m=0
            if peak1.forgotten:
               continue
            for peak2 in nextframe:            
                if peak2.forgotten:
                   continue
                if peak1==peak2:
                   newpeak=peak1.combine(peak2)
                   m=1
                   break # Hope we would only overlap one peak
            if m==0:
               # This peak is no longer active, it did not overlap
               merged.append(peak1)
            else:
               # This peak did overlap, we need to add it for scanning the next frame
               prevframe.append(newpeak)
         i=i+1
      # Now we finished the loop
      # the last frame just needs to merge with anything in prevframe
      print
      print "final frame"      
      if nomega == 2:
         active=peaks[keys[0]:keys[1]]
         first=uniq[keys[1]]
         last=uniq[keys[2]]
      if nomega > 2:
         first=uniq[keys[i]]
         last =uniq[keys[i+1]]
         active=prevframe
      if nomega >= 2:
         for peak1 in active:
            m=0
            if peak1.forgotten:
               continue
            for peak2 in peaks[first:last]:
               if peak2.forgotten:
                  continue
               if peak1 == peak2:
                  newpeak=peak1.combine(peak2)
                  m=1
                  break
            if m==1:
               merged.append(newpeak)
            else:
               merged.append(peak1)
      else:
         merged=peaks
      # Everything ought to be covered here
      merged.sort()
      self.merged=merged
      print "Finished merging peaks","You have a total of "+str(len(self.merged))+" after merging"
      print "That took",time.time()-start
      return

   def filter(self):
      """
      Does nothing really, just makes a self.finalpeaks array

      TODO: pass functions to filter/compress finalpeaks
      """
      if self.merged is None:
         self.mergepeaks()
      if self.merged is None:
         raise Exception("Nothing to filter")
      # Eventually we should offer filters based on shape/intensity/x/y etc
      #
      # For now just throw everything into an array
      biglist=[]
      for peak in self.merged:
         biglist.append(
            [ peak.xc,peak.yc,peak.omega,
              peak.np,peak.avg,peak.x,peak.y,peak.sigx,peak.sigy,peak.covxy]
            )
      # Need to filter based on x,y
      # also based on intensity
      # also based on shape
      self.finalpeaks=Numeric.array(Numeric.transpose(biglist))
      
   def savepeaks(self,filename):
      """
      # Write out minimal information
      # list of xcorr,ycorr,omega, try to keep intensity now
      """
      f=open(filename,"w")
      f.write("# xc yc omega npixels avg_intensity x_raw y_raw sigx sigy covxy\n")
      p =  self.finalpeaks
      for i in range(p.shape[1]):
         for j in range(p.shape[0]):
            f.write("%f "%(p[j,i]))
         f.write("\n")
      f.close()
               

   def slow(self,filename=None):
      """
      Old version of code - it was slower I guess
      """
      if filename == None:
         filename = parent.opener.show(title="Name of raw peaks file")
      self.images=[]
      self.npix=[]
      self.avg=[]
      self.xraw=[]
      self.yraw=[]
      self.xc = []
      self.yc = []
      self.sig_x=[]
      self.sig_y=[]
      self.cov_xy=[]
      for line in open(filename,"r").xreadlines():
#         print line[0:5]
         if line[0:6]=="# File":
            name = line.split()[-1]
            currentimage=pkimage(name)
            self.images.append(currentimage)
            imagenumber = int(name[-8:-4])
            continue
         if line.find("Threshold")>0:
            threshold = float(line.split()[-1])
            continue
         if line.find(" Omega")>0:
            omega = float(line.split()[-1])
            continue
         if line[0]=="#":
            currentimage.addtoheader(line)
            continue
         if len(line)>5:
#            print line
            values = [float(x) for x in line.split()]
            self.npix.append(values[0])
            self.avg.append(values[1])
            self.xraw.append(values[2])
            self.yraw.append(values[3])
            self.xc.append(values[4])
            self.yc.append(values[5])
            self.sig_x.append(values[6])
            self.sig_y.append(values[7])
            self.cov_xy.append(values[8])
      start=time.time()
      self.npix  = array(self.npix)
      self.avg   = array(self.avg)
      self.xraw  = array(self.xraw)
      self.yraw  = array(self.yraw)
      self.xc    = array(self.xc)
      self.yc    = array(self.yc)
      self.sig_x = array(self.sig_x)
      self.sig_y = array(self.sig_y)
      self.cov_xy= array(self.cov_xy)
      print time.time()-start
                  
 
 
if __name__=="__main__":
   import sys,time,optparse
   testfile=sys.argv[1]
   fltfile=sys.argv[2]
   
   object = peakmerger()
   object.readpeaks(testfile)
   object.harvestpeaks()
   object.mergepeaks()
   object.filter()
   object.savepeaks(fltfile)
   sys.exit(0)
   start=time.time()
   import profile
   profile.run('object.readpeaks(testfile)','readpeaks.prof')
#   object.readpeaks(testfile)
   print "That took",time.time()-start,"/s"
   profile.run('object.harvestpeaks()','harvestpeaks.prof')
   profile.run('object.mergepeaks()','mergepeaks.prof')
   profile.run('object.filter()','filterpeaks.prof')
   profile.run('object.savepeaks(fltfile)','savepeaks.prof')

