import numpy as np
from sklearn.neighbors import KDTree
import scipy.sparse

def icp_refine(L1,L2,C,nit):
    """
    Refine a functional map with ICP

    Parameters
    --------------------
    L1 : (n1,k1') basis on the source shape. k1'>= k1
    L2 : (n2,k2') basis on the target shape. k2'>= k2
    C  : (k2,k1)  functional map between the two reduced basis
    nit : int - number of iterations

    Output
    ---------------------
    C_icp  : icp-refined functional map C
    """

    K2,K1 = C.shape
    
    C_icp = C.copy()
    L1_icp = L1[:,:K1].copy()
    L2_icp = L2[:,:K2].copy()
    
    for _ in range(nit):
        tree = KDTree((C_icp@L1_icp.T).T,leaf_size=20) # Tree on (n1,K2)
        matches = tree.query(L2_icp,k=1,return_distance=False).flatten() # (n2,)        
        W,_,_,_ = scipy.linalg.lstsq(L2_icp,L1_icp[matches]) # (K2,K1)
        U,_,VT = scipy.linalg.svd(W)
        C_icp = U@np.eye(K2,K1)@VT
    
    return C_icp


def zoomout_refine(L1,L2,A2,C,nit):
    """
    Refine a functional map with ZoomOut

    Parameters
    --------------------
    L1 : (n1,k1) with k1 >= K + nit
    L2 : (n2,k2) with k2 >= K + nit
    A2 : (n2,n2) sparse area matrix on target mesh
    C  : (K,K) Functional map from from L1[:,:K] to L2[:,:K]
    nit : int - number of iteration of zoomout

    Output
    --------------------
    C_zo : zoomout-refined functional map
    """
    
    assert C.shape[0] == C.shape[1], f"Zoomout input should be square not {C.shape}"
    
    
    n1 = L1.shape[0]
    n2 = L2.shape[0]
    
    kinit = C.shape[0]
    
    C_zo = C.copy()
    
    assert L1.shape[1] >= kinit+nit, f"Enough eigenvectors should be provided, here {kinit+nit} are needed when {L1.shape[1]} are provided"
    assert L2.shape[1] >= kinit+nit, f"Enough eigenvectors should be provided, here {kinit+nit} are needed when {L2.shape[1]} are provided"


    for k in range(kinit,kinit+nit):
        
        tree = KDTree((C_zo@L1[:,:k].T).T, leaf_size=20) # Tree on (n1,K2)
        matches = tree.query(L2[:,:k],k=1,return_distance=False).flatten() # (n2,)
        
        P = scipy.sparse.coo_matrix( (np.ones(n2),(np.arange(n2),matches)), shape=(n2,n1)).tocsc() # (N2,N1) point2point
        
        C_zo = L2[:,:k+1].T @ A2 @ P @ L1[:,:k+1] # (k+1,k+1)
        
    return C_zo
