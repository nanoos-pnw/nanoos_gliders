def get_min_max(inarr, Tolerance, expPts):
    """Find start and end points for each segment of the glider path
        Input:
     	    inarr - input array of longitudes, no NaNs allowed in the array
     	    Tolerance - value which determines that new segment is started
            expPts - number of expected endpoints for the full glider path
        Output:
    	    ind_min_max - array of indices denoting sequential endpoints for the glider path segments
    """

    Npoints = len(inarr)-1
    k = 1
    while k <= Npoints:
        if  abs(inarr[k]-inarr[0]) > Tolerance: 
            break
        k += 1
    
    if k > Npoints:
        k = Npoints

    ln_ind = [None] * expPts
    ln_ind[0] = 0
    minmax = 1

    if inarr[k] > inarr[0]:
        trace = 'MAX' 
        maxz = inarr[k]
        ln_ind[minmax] = k
    else:
        trace = 'MIN'
        minz = inarr[k]
        ln_ind[minmax] = k

    for j in range(k, Npoints):
        if trace == 'MAX':
            if inarr[j] >= maxz:
                maxz = inarr[j]
                ln_ind[minmax] = j
            else:
                if Tolerance <= abs(maxz - inarr[j]):
                    minz = inarr[j]
                    minmax += 1
                    ln_ind[minmax] = j
                    trace = 'MIN'
        elif trace == 'MIN':
            if inarr[j] <= minz:
                minz = inarr[j]
                ln_ind[minmax] = j
            else:
                if Tolerance <= abs(inarr[j] - minz):
                    maxz = inarr[j]
                    minmax += 1
                    ln_ind[minmax] = j
                    trace = 'MAX'
    
    # to remove None values in list
    good_ln_ind = list(filter(None, ln_ind))
    good_ln_ind.insert(0,0)
    if good_ln_ind[-1] < Npoints and len(good_ln_ind)<expPts:
        good_ln_ind.append(Npoints)
    else:
        good_ln_ind[-1] = Npoints

    ind_min_max = good_ln_ind
    return ind_min_max  
