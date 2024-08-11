from  fem4inas.systems.system import System
import fem4inas.systems.sollibs as sollibs
import fem4inas.intrinsic.staticAD as static_ad
import fem4inas.intrinsic.dynamicAD as dynamic_ad
import fem4inas.intrinsic.postprocess as postprocess
import fem4inas.preprocessor.containers.intrinsicmodal as intrinsicmodal
import fem4inas.preprocessor.solution as solution
import fem4inas.intrinsic.initcond as initcond
import fem4inas.intrinsic.args as libargs
import fem4inas.intrinsic.objectives as objectives
from functools import partial
import jax
import jax.numpy as jnp

class IntrinsicADSystem(System, cls_name="AD_intrinsic"):

    def __init__(self,
                 name: str,
                 settings: intrinsicmodal.Dsystem,
                 fem: intrinsicmodal.Dfem,
                 sol: solution.IntrinsicSolution,
                 config):

        self.name = name
        self.settings = settings
        self.fem = fem
        self.sol = sol
        self.config = config
        #self._set_xloading()
        #self._set_generator()
        #self._set_solver()

    def set_ic(self, q0):
        if q0 is None:
            self.q0 = jnp.zeros(self.settings.num_states)
        else:
            self.q0 = q0

    def set_solver(self):
        
        match self.settings.ad.grad_type:
            case "grad":
                raise ValueError("Drop support for grad as it requires value-function output which prevents generalisations")                
                # self.eqsolver = jax.grad
                # obj_label = f"{self.settings.ad.objective_var}_{self.settings.ad.objective_fun.upper()}grad"
                # self.f_obj = objectives.factory(obj_label)
                
            case "value_grad":
                raise ValueError("Drop support for grad as it requires value-function output which prevents generalisations")
                # self.eqsolver = jax.value_and_grad
                # self.eqsolver = jax.grad
                # obj_label = f"{self.settings.ad.objective_var}_{self.settings.ad.objective_fun.upper()}grad"
                # self.f_obj = objectives.factory(obj_label)
            case "jacrev":
                self.eqsolver = jax.jacrev
                obj_label = f"{self.settings.ad.objective_var}_{self.settings.ad.objective_fun.upper()}"
                self.f_obj = objectives.factory(obj_label)
            case "jacfwd":
                self.eqsolver = jax.jacfwd
                obj_label = f"{self.settings.ad.objective_var}_{self.settings.ad.objective_fun.upper()}"
                self.f_obj = objectives.factory(obj_label)
            case "value":
                self.eqsolver = lambda func, *args, **kwargs: func
                obj_label = f"{self.settings.ad.objective_var}_{self.settings.ad.objective_fun.upper()}"
                self.f_obj = objectives.factory(obj_label)
            case _:
                raise ValueError(f"Incorrect solver {self.settings.ad.grad_type}")

    def solve(self):

        fprime = self.eqsolver(self.dFq, has_aux=True) # call to jax.grad..etc
        if self.settings.ad.grad_type == "value_grad":
            ((val, fout), jac) = fprime(self.settings.ad.inputs,
                                        q0=self.q0,
                                        config=self.config,
                                        f_obj=self.f_obj,
                                        obj_args=self.settings.ad.objective_args
                                        )
        else:
            jac, fout = fprime(self.settings.ad.inputs,
                               q0=self.q0,
                               config=self.config,
                               f_obj=self.f_obj,
                               obj_args=self.settings.ad.objective_args
                               )
        self.build_solution(jac, *fout)
        
    def save(self):
        pass

    def set_eta0(self):
        pass

    def set_states(self):
        self.settings.build_states(self.fem.num_modes, self.fem.num_nodes)

    def set_xloading(self):
        pass
    
class StaticADIntrinsic(IntrinsicADSystem, cls_name="staticAD_intrinsic"):

    def set_system(self):
        
        label_sys = self.settings.label
        label_ad = self.settings.ad.label
        label = f"main_{label_sys}_{label_ad}"
        print(f"***** Setting intrinsic Dynamic system with label {label}")
        self.dFq = getattr(static_ad, label)

    def build_solution(self, jac, objective, q, X1, X2, X3, ra, Cab, *args, **kwargs):

               
        self.sol.add_container('StaticSystem', label="_"+self.name,
                               jac=jac, q=q, X2=X2, X3=X3,
                               Cab=Cab, ra=ra, f_ad=objective)
        if self.settings.save:
            self.sol.save_container('StaticSystem', label="_"+self.name)

class DynamicADIntrinsic(IntrinsicADSystem, cls_name="dynamicAD_intrinsic"):

    def set_system(self):
        
        label_sys = self.settings.label
        label_ad = self.settings.ad.label
        label = f"main_{label_sys}_{label_ad}"
        print(f"***** Setting intrinsic Dynamic system with label {label}")
        self.dFq = getattr(dynamic_ad, label)

    def build_solution(self, jac, objective, q, X1, X2, X3, ra, Cab, *args, f_ad=None, **kwargs):

        self.sol.add_container('DynamicSystem', label="_"+self.name,
                               jac=jac, q=q, X1=X1, X2=X2, X3=X3, t=self.settings.t,
                               Cab=Cab, ra=ra, f_ad=objective)
        if self.settings.save:
            self.sol.save_container('DynamicSystem', label="_"+self.name)            
            
