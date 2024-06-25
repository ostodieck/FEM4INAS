from pyNastran.op2.op2 import OP2
import fem4inas.plotools.nastranvtk.bdfdef as bdfdef
import fem4inas.plotools.interpolation as interpolation
from fem4inas.preprocessor import solution
import fem4inas.plotools.grid as grid
from pyNastran.bdf.bdf import BDF
import pandas as pd
import fem4inas.plotools.reconstruction as rec
import fem4inas.preprocessor.configuration as configuration
import jax.numpy as jnp

#op2 = OP2()
#op2.read_op2("./NASTRAN/runs/XRF1-144trim.op2")

loads = ['1','2','3','3_5', '4']

for li in loads:
    bdfdef.vtkSol_fromop2("./NASTRAN/XRF1-144trim.bdf", f"./NASTRAN/runs/XRF1-144trim{li}g.op2",
                          size_card=16, write_path=f'./nastrantrimVTK/{li}/', plot_ref=False)

# op2 = OP2()
# op2.read_op2("./NASTRAN/103/XRF1-103cfo.op2")
