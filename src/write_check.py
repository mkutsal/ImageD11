
from __future__ import print_function, division

f = open("check_cpu_auto.c", "w")
h = open("check_cpu_auto.h", "w")

h.write("""

#ifndef _write_check_h
#define _write_check_h
void readcpuid( unsigned int leaf, unsigned int subleaf, unsigned int idBits[4] );

""")

f.write("""
/** 
 * This code was auto-generated by write_check.py. Do not edit here!
 * 
 * Utilities for checking the CPU instruction set
 *
 * https://en.wikipedia.org/wiki/CPUID
 *
 */

#include <stdio.h>

#ifdef _MSC_VER
    #include <intrin.h>
#else
    #include <cpuid.h>
#endif
#include "cImageD11.h"
#include "check_cpu_auto.h"

/* DO NOT Use static globals here 
 * Results of calls to cpuid 
 * Stuff to look for : EAX call, A|B|C|D, bit position 
 *  0  : {B,D,C} = name, A = maxcall
 *  1  :  4A, 5B, 6C, 7D
 *      A = Processor information
 *      B = Additional information
 *      C = Features
 *      D = Features
 *  2  : Cache and TLB Descriptor information
 *  3  : Processor Serial Number
 * EAX=4 and EAX=Bh: Intel thread/core and cache topology
 * EAX=7, ECX=0: Extended Features
 * EAX=80000000h: Get Highest Extended Function Implemented : 
 *                The highest calling parameter is returned in EAX.
 * EAX=80000001h: Extended Processor Info and Feature Bits
 * EAX=80000002h,80000003h,80000004h: Processor Brand String
 * EAX=80000005h: L1 Cache and TLB Identifiers
 * EAX=80000006h: Extended L2 Cache Features
 * EAX=80000007h: Advanced Power Management Information
 * EAX=80000008h: Virtual and Physical address Sizes
 * EAX=8FFFFFFFh: AMD Easter Egg
 */


/**
 * Calls cpuid and stores results of eax,ebx,ecx,edx in idBits[op*4:op*4+4]
 * __cpuid_count needed for > XXX
 */
void readcpuid( unsigned int leaf, unsigned int subleaf, unsigned int idBits[4] ) {
  int j;
  // MSVC and gcc both provide a __cpuid function
  for(j=0;j<4;j++) idBits[j]=0;
  #if defined(__GNUC__)
   __cpuid_count( leaf, subleaf, idBits[0], idBits[1], idBits[2], idBits[3]);
  #elif defined(_WIN32)
  __cpuidex( &idBits[0], leaf, subleaf );
  #endif
}


/**
 * Retrieve the processor name.
 * \param name Preallocated string containing at least room for 13 characters. Will
 *             contain the name of the processor.
 */
void cpuidProcessorName( char* name ){
  unsigned int idBits[4];
  readcpuid( 0, 0, idBits );
  name[0]  = (idBits[1]    ) & 0xFF;
  name[1]  = (idBits[1]>> 8) & 0xFF;
  name[2]  = (idBits[1]>>16) & 0xFF;
  name[3]  = (idBits[1]>>24) & 0xFF;
  name[4]  = (idBits[3]    ) & 0xFF;
  name[5]  = (idBits[3]>> 8) & 0xFF;
  name[6]  = (idBits[3]>>16) & 0xFF;
  name[7]  = (idBits[3]>>24) & 0xFF;
  name[8]  = (idBits[2]    ) & 0xFF;
  name[9]  = (idBits[2]>> 8) & 0xFF;
  name[10] = (idBits[2]>>16) & 0xFF;
  name[11] = (idBits[2]>>24) & 0xFF;
  name[12] = 0;
}



""")

for name, byte, bit in [
    ("SSE", 7, 25),
    ("SSE2", 7, 26),
    ("SSE3", 6, 0),
    ("FMA3",6,12),
    ("SSE41",6,19),
    ("SSE42",6,20),
    ("MOVBE",6,22),
    ("XSAVE", 6, 26),
    ("OSXSAVE",6,27),
    ("AVX",6,28),
    ("AVX2", 29,5),
    ("AVX512F",29,16),
    ]:
    func = "int flag_%s(){\n"%(name) + \
           " unsigned int idBits[4];\n" + \
           " readcpuid( %d , 0, idBits );\n"%(byte//4) + \
           " return (idBits[%d] & ( 1 << %d))>0;\n}\n"%(byte%4,bit)
    f.write(func)
    h.write("int flag_%s(void);\n"%(name))

h.write("int i_have_SSE2(void);\n")
h.write("int i_have_SSE42(void);\n")
h.write("int i_have_AVX(void);\n")
h.write("int i_have_AVX2(void);\n")
h.write("int i_have_AVX512F(void);\n")

f.write( """
int i_have_SSE2(){
  return (flag_SSE2()>0);
}
int i_have_SSE42(){
  return (flag_SSE42()>0);
}
int i_have_AVX(){
    return (flag_XSAVE()>0)&(flag_OSXSAVE()>0)&(flag_AVX()>0);
}
int i_have_AVX2(){
    return (flag_AVX()>0)&(flag_MOVBE()>0)&(flag_FMA3()>0)&(flag_AVX2()>0);
}
int i_have_AVX512F(){
    return (flag_OSXSAVE()>0)&(flag_AVX512F()>0);
}

""")

f.close()
h.write("#endif\n")
h.close()


