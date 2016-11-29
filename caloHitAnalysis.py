from pyLCIO import IOIMPL, EVENT,UTIL
from pyLCIO.io.LcioReader import LcioReader
from array import array
from ROOT import *
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# pyLCIO analysis for SiD calorimeters
#
# A. Steinhebel, University of Oregon
# Nov. 2016
#
# Input: Reconstructed .slcio file
# Output: ROOT Histograms of the total energy deposited in each event, both for the entire calorimeter and individual layers
#
#
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

inFile='/home/Amanda/lcgeo/reco_200a.100GeV.0phi_2.slcio'

# if the layer info of each hit is necessary for the analysis, set to "True". If not, set to "False"
layerInfo=True

#create a reader
readerL = LcioReader(inFile)

# create a histograms for the hit energies
if layerInfo:
    nmbLayers=31
    layerHist=[0]*nmbLayers
    for i in range(nmbLayers):
        layerHist[i]=TH1D('DepositedEnergy','Energy per Event in Layer '+str(i)+';HCal Barrel Hit Energy [GeV];Entries',10,0,0.1)

hitEnergyHistogram = TH1D( 'TotalDepositedEnergy', 'Event Energy Deposit;HCAL Barrel Hit Energy [GeV];Entries', 100, 0., 1.)



if not layerInfo:
##### for basic analysis that only totals the deposits for each event #####

    # create a reader and open an LCIO file
    reader = IOIMPL.LCFactory.getInstance().createLCReader()
    reader.open( inFile )
    i=-1
    # loop over all events in the file
    for dep in reader:
        i+=1
        if i%10==0:
            print "Summing energy of event "+str(i)
        # initialize summing variables to total all the calorimeter hits in a given event
        hitTotal=0.	
        # get the collection from the event
        hitCollection = dep.getCollection( 'HCalBarrelHits' )#### ensure that this variable matches the variable used to record layer information
        # loop and sum over all hits in the event
        for hit in hitCollection:
            hitTotal+=hit.getEnergy()
        # fill histogram
        hitEnergyHistogram.Fill(hitTotal)
    reader.close()


if layerInfo:
##### for any analysis involving the layer number of a hit #####

    ##~~ record layers of each hit ~~##
    nmbEvents=1000
    #create array that contains an array for every event that sequentially records the layer number of each hit
    layerNos=[0]*nmbEvents
    for i in range(nmbEvents):
        layerNos[i]=[]
    print "Layer array created"

    eventNo=-1
    # loop over the events
    for event in readerL:
        eventNo+=1
        if eventNo%10==0:
            print "recording layers of event "+str(eventNo)
        # get a hit collection
        ecalHits = event.getCollection( 'HCalBarrelHits' ) ####can change to other variables, such as 'ECalBarrelHits', etc
        # get the cell ID encoding string from the collection parameters
        cellIdEncoding = ecalHits.getParameters().getStringVal( EVENT.LCIO.CellIDEncoding )
        # define a cell ID decoder for the collection
        idDecoder = UTIL.BitField64( cellIdEncoding )
        # loop over all hits in the collection
        for caloHit in ecalHits:
            # combine the two 32 bit cell IDs of the hit into one 64 bit integer
            cellID = long( caloHit.getCellID0() & 0xffffffff ) | ( long( caloHit.getCellID1() ) << 32 )
            # set up the ID decoder for this cell ID
            idDecoder.setValue( cellID )
            # access the field information using a valid field from the cell ID encoding string and place layer value in layerNos array
            layerNos[eventNo].append(idDecoder['layer'].value())


    # create a reader and open an LCIO file
    reader = IOIMPL.LCFactory.getInstance().createLCReader()
    reader.open( inFile )
    i=-1
    # loop over all events in the file
    for dep in reader:
        i+=1
        if i%10==0:
            print "Summing energy of event "+str(i)
        # initialize summing variables to total all the calorimeter hits in a given event
        hitTotal=0.	
        layerTotal=[0]*nmbLayers
        # get the collection from the event
        hitCollection = dep.getCollection( 'HCalBarrelHits' )#### ensure that this variable matches the variable used to record layer information
        # record which hit to find cooresponding hit layer value
        hitNo=0
        # loop and sum over all hits in the event
        for hit in hitCollection:
            hitTotal+=hit.getEnergy()
            layerTotal[int(layerNos[i][hitNo])]+=hit.getEnergy()
            hitNo+=1
        # fill the histograms with the sums
        hitEnergyHistogram.Fill(hitTotal)
        for m in range(nmbLayers):
            layerHist[m].Fill(layerTotal[m])
    reader.close()

##### plotting with ROOT #####

# define a fit function
#fitFunction = TF1( 'aFunction', 'landau', 0.05, 5. )
fitFunctionGauss=TF1('fitFnGauss','gaus',0.,0.25)
# change styling of the fit function
fitFunctionGauss.SetLineColor( kRed )
fitFunctionGauss.SetLineStyle( kDashed )
# fit the histogram
hitEnergyHistogram.Fit( fitFunctionGauss, 'R' )

# create a canvas for the total histogram
canvas = TCanvas( 'aCanvas', 'my Canvas', 800, 700 )
canvas.SetLogy()
# draw the histogram
hitEnergyHistogram.Draw()
# display fit and fit parameters
gStyle.SetOptFit(1)

if layerInfo:
    # create canvas for layer histograms
    canvas1=TCanvas('bCanvas','layers',1200,1200)
    canvas1.Divide(6,5)
    # draw the histograms
    for n in range(nmbLayers):
        canvas1.cd(n+1)
        layerHist[n].Draw()

