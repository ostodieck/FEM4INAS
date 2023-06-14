"""FEM4INAS main"""
import argparse
import fem4inas.drivers

def main(input_file=None, input_dict=None, input_obj=None):
    """
    Main ``FEM4INAS`` routine

    """
    if input_dict is None and input_obj is None:
        parser = argparse.ArgumentParser(prog='FEM4INAS', description=
        """This is the executable of Fininte-Element Models for Intrinsic Nonlinear Aeroelastic Simulations.""")
        parser.add_argument('input_file', help='path to the *.yml input file', type=str, default='')
        if input_file is not None:
            args = parser.parse_args(input_file)
        else:
            args = parser.parse_args()

    driver = fem4inas.drivers.factory(settings)
    
    driver.run()

