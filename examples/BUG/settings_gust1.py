# [[file:modelgeneration.org::*Run][Run:1]]
import pathlib
import jax.numpy as jnp
import feniax.preprocessor.configuration as configuration  # import Config, dump_to_yaml
from feniax.preprocessor.inputs import Inputs
import feniax.feniax_main

label_gaf = "Dd1c7F1Scao-50"
num_poles = 5
Dhj_file = f"D{label_gaf}p{num_poles}"
Ahh_file = f"A{label_gaf}p{num_poles}"
Poles_file = f"Poles{label_gaf}p{num_poles}"

inp = Inputs()
inp.engine = "intrinsicmodal"
inp.fem.eig_type = "inputs"

inp.fem.connectivity = dict(# FusWing=['RWing',
                            #          'LWing'],
                            FusBack=['FusTail',
                                     'VTP'],
                            FusFront=None,
                            RWing=None,
                            LWing=None,
                            FusTail=None,
                            VTP=['HTP', 'VTPTail'],
                            HTP=['RHTP', 'LHTP'],
                            VTPTail=None,
                            RHTP=None,
                            LHTP=None,
                            )

inp.fem.grid = "structuralGridclamped"
inp.fem.folder = pathlib.Path('./FEM/')
inp.fem.eig_names = ["eigenvals_50.npy", "eigenvecs_50.npy"]
inp.fem.num_modes = 50
inp.driver.typeof = "intrinsic"

#inp.driver.sol_path = pathlib.Path(
#    f"./results_{datetime.datetime.now().strftime('%Y-%m-%d_%H:%M:%S')}")
inp.driver.sol_path = pathlib.Path(
    "./results1gust")
inp.simulation.typeof = "single"
inp.system.name = "s1"
inp.system.solution = "dynamic"
inp.system.t1 = 7.5
inp.system.tn = 4001
inp.system.solver_library = "runge_kutta"
inp.system.solver_function = "ode"
inp.system.solver_settings = dict(solver_name="rk4")
inp.system.xloads.modalaero_forces = True
inp.system.q0treatment = 2
inp.system.aero.c_ref = 3.0
inp.system.aero.u_inf = 180.
inp.system.aero.rho_inf = 1.
inp.system.aero.poles = f"./AERO/{Poles_file}.npy"
inp.system.aero.A = f"./AERO/{Ahh_file}.npy"
inp.system.aero.D = f"./AERO/{Dhj_file}.npy"
inp.system.aero.gust_profile = "mc"
inp.system.aero.gust.intensity = 0.01 # 14.0732311562*0.001
inp.system.aero.gust.length = 30.
inp.system.aero.gust.step = 0.05
inp.system.aero.gust.shift = 0.
inp.system.aero.gust.panels_dihedral = jnp.load("./AERO/Dihedral_d1c7.npy")
inp.system.aero.gust.collocation_points = "./AERO/Collocation_d1c7.npy"

config =  configuration.Config(inp)
sol1 = feniax.feniax_main.main(input_obj=config)

# Run:1 ends here
