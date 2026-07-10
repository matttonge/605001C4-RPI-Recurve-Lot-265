class CONVERSIONS:
    

    def __init__(self,master=None):
        self.master = master
        self.CurDiaUnits = "mm"
        self.DiaUnits = "mm","inch"
        self.CurPosUnits = "mm"
        self.PosUnits = "mm","inch"
        self.CurBalUnits = "atm"
        self.BalUnits = "atm","bar","psi"
        self.CurClampUnits = "atm"
        self.ClampUnits = "atm","bar","psi"

        # Keep conversion factors centralized to reduce duplication and
        # make future calibration updates safer.
        self._lin_factors = {
            ("mm", "inch"): 0.03937008,
            ("inch", "mm"): 25.4,
        }

        self._press_factors = {
            ("atm", "bar"): 1.01325,
            ("atm", "psi"): 14.6959,
            ("bar", "atm"): 0.986923,
            ("bar", "psi"): 14.5038,
            ("psi", "atm"): 0.068046,
            ("psi", "bar"): 0.0689476094997927,
        }
    

    def cnvrt_lin_units(self, inpValue, fromU, toU):
        if fromU == toU:
            return inpValue
        factor = self._lin_factors.get((fromU, toU))
        if factor is None:
            return None
        return inpValue * factor


    def set_cur_dia_units(self, units):
        if(units in self.DiaUnits):
           self.CurDiaUnits = units
    
    def get_cur_dia_units(self):
        return  self.CurDiaUnits

    def to_cur_dia_units(self, value, units):
        return self.cnvrt_lin_units( value, units, self.CurDiaUnits)
       

    

    def set_cur_pos_units(self, units):
        if(units in self.PosUnits):
           self.CurPosUnits = units
    
    def get_cur_pos_units(self):
        return  self.CurPosUnits

    def to_cur_pos_units(self, value, units):
        return self.cnvrt_lin_units( value, units, self.CurPosUnits)




    def cnvrt_press_units(self, inpPress, fromU, toU):
        if fromU == toU:
            return inpPress
        factor = self._press_factors.get((fromU, toU))
        if factor is None:
            return None
        if fromU == "psi":
            inpPress = float(inpPress)
        return inpPress * factor
        
       
    def set_cur_bal_units(self, units):
        if(units in self.BalUnits):
           self.CurBalUnits = units
    
    def get_cur_bal_units(self):
        return  self.CurBalUnits

    def to_cur_bal_units(self, value, units):
        return self.cnvrt_press_units( value, units, self.CurBalUnits)


    def set_cur_clamp_units(self, units):
        if(units in self.ClampUnits):
           self.CurClampUnits = units
    
    def get_cur_clamp_units(self):
        return  self.CurClampUnits

    def to_cur_clamp_units(self, value, units):
        return self.cnvrt_press_units( value, units, self.CurClampUnits)



    def mit_val_to_position(self, mit_val, output_units):
        str1 = str(mit_val).strip("b.'").lstrip().rstrip()
        if(str1[-2:]=="mm"):
            str1=str1[:-2]
            if(output_units=="mm"):
                return  float(str1) 
            else:      
                return  float(str1)*0.0393701       
        if(str1[-2:]=="in"):
            str1=str1[:-2]
            if(output_units=="mm"):
                return  float(str1)*25.4 
            else:      
                return  float(str1)
        return None #float('-inf')  
    
       