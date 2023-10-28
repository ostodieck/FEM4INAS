from fem4inas.drivers.driver import Driver

import fem4inas.simulations
from fem4inas.preprocessor import solution, configuration
import fem4inas.intrinsic.modes as modes
import fem4inas.intrinsic.couplings as couplings
import fem4inas.systems

class IntrinsicDriver(Driver, cls_name="intrinsic"):
    """Driver for the modal intrinsic theory

    Creates simulation, systems and solution data objects and calls
    the pre-simulation and the simulation public methods

    Parameters
    ----------
    config : config.Config
         Configuration object

    Attributes
    ----------
    _config : see Parameters
    simulation :
    sol :
    systems :

    """

    def __init__(self, config: configuration.Config):
        """

        Parameters
        ----------
        config : config.Config
            Configuration object

        """

        self._config = config
        self.simulation = None
        self.sol = None
        self.systems = None
        self.num_systems = 0
        self._set_sol()        
        self._set_systems()
        self._set_simulation()

    def pre_simulation(self):
        # TODO: here the RFA for aerodynamics should be included
        # TODO: condensation methods of K and M should be included
        if self._config.driver.compute_fem:
            self._compute_modalshapes()
            self._compute_modalcouplings()
            if self._config.driver.save_fem:
                self.sol.save_container("Modes")
                self.sol.save_container("Couplings")
        else:
            self._load_modalshapes()
            self._load_modalcouplings()

        if self._config.driver.compute_modalaero:
            self._compute_modalaero()
            if self._config.driver.save_modalaero:
                approx = self._config.aero.approx
                self.sol.save_container(f"ModalAero{approx}")
        elif self._config.driver.load_modalaero:
            self._load_modalaero()

    def run_case(self):
        if self.num_systems == 0:
            print("no systems in the simulation")
        else:
            self.simulation.trigger()

    def _set_simulation(self):
        # Configure the simulation
        if hasattr(self._config, "simulation"):
            cls_simulation = fem4inas.simulations.factory(
                self._config.simulation.typeof
            )
            self.simulation = cls_simulation(
                self.systems, self.sol, self._config.simulation
            )
        else:
            print("no simulation settings")

    def _set_systems(self):
        print("***** Setting systems *****")
        self.systems = dict()
        if hasattr(self._config, "systems"):
            for k, v in self._config.systems.mapper.items():
                print(f"***** Initialising system {k} *****")
                cls_sys = fem4inas.systems.factory(f"{v.solution}_intrinsic")
                self.systems[k] = cls_sys(k, v, self._config.fem, self.sol, self._config)
                print(f"***** Initialised {v.solution}_intrinsic *****")
        self.num_systems = len(self.systems)

    def _set_sol(self):
        # Configure the simulation
        self.sol = solution.IntrinsicSolution(self._config.driver.sol_path)

    def _compute_eigs(self):
        eig_funcs = dict(scipy=modes.compute_eigs_scipy,
                         jax_custom=modes.compute_eigs,
                         inputs=modes.compute_eigs_load)

        eig_type = self._config.fem.eig_type
        eig_solver = eig_funcs[self._config.fem.eig_type]
        eigenvals, eigenvecs = eig_solver(Ka=self._config.fem.Ka,
                                          Ma=self._config.fem.Ma,
                                          num_modes=self._config.fem.num_modes,
                                          path=self._config.fem.folder,
                                          eig_names=self._config.fem.eig_names)
        print(f"***** Computing eigen problem from {eig_type} *****")
        return eigenvals, eigenvecs

    def _compute_modalshapes(self):

        eigenvals, eigenvecs = self._compute_eigs()
        modal_analysis = modes.shapes(
            self._config.fem.X.T, self._config.fem.Ka, self._config.fem.Ma,
            eigenvals, eigenvecs, self._config
        )
        modal_analysis_scaled = modes.scale(*modal_analysis)
        self.sol.add_container("Modes", *modal_analysis_scaled)

    def _compute_modalcouplings(self):
        # if self._config.numlib == "jax":

        # elif self._config.numlib == "numpy":
        #    import fem4inas.intrinsic.couplings_np as couplings
        alpha1, alpha2 = modes.check_alphas(self.sol.data.modes.phi1,
                                            self.sol.data.modes.psi1,
                                            self.sol.data.modes.phi2l,
                                            self.sol.data.modes.psi2l,
                                            self.sol.data.modes.X_xdelta,
                                            tolerance=self._config.jax_np.allclose
        )
        gamma1 = couplings.f_gamma1(self.sol.data.modes.phi1,
                                    self.sol.data.modes.psi1)
        gamma2 = couplings.f_gamma2(
            self.sol.data.modes.phi1ml,
            self.sol.data.modes.phi2l,
            self.sol.data.modes.psi2l,
            self.sol.data.modes.X_xdelta,
        )

        self.sol.add_container("Couplings", alpha1, alpha2, gamma1, gamma2)

    def _compute_modalaero(self):

        approx = self._config.aero.approx
        container = dict()
        if self._config.aero.Qk_struct is not None:
            
            if len(self._config.aero.Qk_struct[0]) == 1: # steady
                A0 = self._config.aero.Qk_struct[1]
                container.update(A0=A0)
        if self._config.aero.Qk_controls is not None:

            if len(self._config.aero.Qk_controls[0]) == 1: # steady
                B0 = self._config.aero.Qk_controls[1]
                container.update(B0=B0)

        if self._config.aero.M0_rigid is not None:
            C0 = self._config.aero.Q0_rigid
            container.update(C0=C0)

        # TODO: set roger, lowner etc.
        self.sol.add_container(f"ModalAero{approx}",
                               #label="init",
                               **container)

    def _load_modalshapes(self):
        self.sol.load_container("Modes")

    def _load_modalcouplings(self):
        self.sol.load_container("Couplings")

    def _load_modalaero(self):
        approx = self._config.aero.approx
        self.sol.load_container(f"ModalAero{approx}")
