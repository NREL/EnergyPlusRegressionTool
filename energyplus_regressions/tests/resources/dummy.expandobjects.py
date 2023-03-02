#!/usr/bin/env python3

file_contents = open('in.idf').read().upper()

if 'HVACTEMPLATE' in file_contents:
    open('expanded.idf', 'w').write('HI')
    open('BasementGHTIn.idf', 'w').write('HI')
    open('GHTIn.idf', 'w').write('HI')
    open('EPObjects.TXT', 'w').write('HI')
    open('RunINPUT.TXT', 'w').write('HI')
    open('RunDEBUGOUT.TXT', 'w').write('HI')
    open('EPObjects.TXT', 'w').write('HI')
    open('BasementGHTIn.idf', 'w').write('HI')
    open('MonthlyResults.csv', 'w').write('HI')
    open('BasementGHT.idd', 'w').write('HI')
    open('SLABINP.TXT', 'w').write('HI')
    open('GHTIn.idf', 'w').write('HI')
    open('SLABSurfaceTemps.TXT', 'w').write('HI')
    open('SLABSplit Surface Temps.TXT', 'w').write('HI')
    open('SlabGHT.idd', 'w').write('HI')
