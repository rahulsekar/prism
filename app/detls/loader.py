import sys
import datetime
import os

#locals
import utils, bsederiv, nsederiv, nseindex, nsewdm

def load(date):
    DETLs = [
        nseindex.NSEIndex,
        nsewdm.NSEWDM,
        bsederiv.BSEDeriv,
        nsederiv.NSEDeriv,
    ]

    for DETL in DETLs:
        obj = DETL(date)

        obj.check_do('download',
                     obj.is_ready_to_download,
                     obj.is_downloaded,
                     obj.clean_downloaded,
                     obj.download)

        obj.check_do('extract',
                     obj.is_ready_to_extract,
                     obj.is_extracted,
                     obj.clean_extracted,
                     obj.extract)

        obj.check_do('transform',
                     obj.is_ready_to_transform,
                     obj.is_transformed,
                     obj.clean_transformed,
                     obj.transform)
    
        utils.log(obj, 'loading...', end='')
        obj.check_load()
        utils.log(obj, 'done.', ctxt=False)
