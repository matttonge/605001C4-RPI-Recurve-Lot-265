
# from rcpage1b_addin import Parameter

from run_manual import Parameter
from io_ import I_O


class rs_auto:
    
    
    def __init__(self, master=None):  
        self.m = master 

        

        
    def callback_D(self):
        if(self.Zero_valid):           
            self.clear_BG()
            self.left_neck_od_D_lbl.config(background = "pale green")
            self.message_txt.delete(1.0,4.0)
            if(I_O.cone_flip):
                self.message_txt.insert(1.0," 1. Position the center of the proximal neck at the measurement line.\n")
                self.message_txt.insert(2.0," 2. When the gage is in position, press Right Chuck button or the Get Data button to record the diameter data.\n")
            else:    
                self.message_txt.insert(1.0," 1. Position the center of the distal neck at the measurement line.\n")
                self.message_txt.insert(2.0," 2. When the gage is in position, press Right Chuck button or the Get Data button to record the diameter data.\n")
            Parameter.selected_param = Parameter.LEFT_NECK_D

    def callback_F(self):
        if(self.Zero_valid):
            self.clear_BG()
            self.right_neck_od_F_lbl.config(background = "pale green")    
            self.message_txt.delete("1.0","end")
            if(I_O.cone_flip):
                self.message_txt.insert(1.0," 1. Position the center of the distal neck at the measurement line.\n")
                self.message_txt.insert(2.0," 2. When the gage is in position, press Right Chuck button or the Get Data button to record the diameter data.\n")
            else:    
                self.message_txt.insert(1.0," 1. Position the center of the proximal neck at the measurement line.\n")
                self.message_txt.insert(2.0," 2. When the gage is in position, press Right Chuck button or the Get Data button to record the diameter data.\n")
            Parameter.selected_param = Parameter.RIGHT_NECK_F

    def callback_A_dia_1(self):
        if(self.Zero_valid):
            self.clear_BG()
            self.A1_dia.config(background = "pale green")
            self.message_txt.insert(1.0,"Position the right side of the balloon body (A1) at the measurement positon and press the Righ Chuck button or the Get Data button ")
            Parameter.selected_param = Parameter.A1

        

    def callback_A_dia_2(self):
        if(self.Zero_valid):
            self.clear_BG()
            self.A2_dia.config(background = "pale green")
            self.message_txt.insert(1.0,"Position the center of the balloon body (A2) at the measurement positon and press the Righ Chuck button or the Get Data button ")
            Parameter.selected_param = Parameter.A2


    def callback_A_dia_3(self):
        if(self.Zero_valid):
            self.clear_BG()
            self.A3_dia.config(background = "pale green")
            self.message_txt.insert(1.0,"Position the left side of the balloon body (A3) at the measurement positon and press the Righ Chuck button or the Get Data button ")
            Parameter.selected_param = Parameter.A3


    def callback_0(self):
            if  Parameter.selected_param != Parameter.ZERO:
                self.clear_BG()
                self.left_neck_pos_lbl.config(background = "pale green")
                self.message_txt.delete(1.0,4.0)   
                if(I_O.cone_flip):            
                    self.message_txt.insert(1.0," 1. Position the proximal cone to neck tansition at the measurement line.\n")
                    self.message_txt.insert(2.0," 2. Press the ZERO button on the Mitutoyo position gage.\n") 
                    self.message_txt.insert(3.0," 3. When the gage is zero, press a Chuck button or the Get Data button to record the zero positon.\n")
                else:
                    self.message_txt.insert(1.0," 1. Position the distal cone to neck transition at the measurement line.\n")
                    self.message_txt.insert(2.0," 2. Press the ZERO button on the Mitutoyo position gage.\n") 
                    self.message_txt.insert(3.0," 3. When the gage is zero, press a Chuck button or the Get Data button to record the zero positon.\n")
                Parameter.selected_param = Parameter.ZERO
            else:
                self.clear_BG()
                self.message_txt.delete(1.0,4.0)
                Parameter.selected_param = None           


    def callback_left_Cone(self):
        if(self.Zero_valid):           
            self.clear_BG()
            self.left_cone_pos_lbl.config(background = "pale green")
            self.message_txt.delete(1.0,4.0)
            if(I_O.cone_flip):            
                self.message_txt.insert(1.0," 1. Position the balloon proximal cone to balloon body transition at the measurement line.\n")
                self.message_txt.insert(2.0," 2. When the gage is in position, press a Chuck button or the Get Data button to record the positon data.\n")
            else:    
                self.message_txt.insert(1.0," 1. Position the distal cone to balloon body transition at the measurement line.\n")
                self.message_txt.insert(2.0," 2. When the gage is in position, press a Chuck button or the Get Data button to record the positon data.\n")
            Parameter.selected_param = Parameter.LEFT_CONE
            
    def callback_right_Cone(self ):
        if(self.Zero_valid):           
            self.clear_BG()
            self.right_cone_pos_lbl.config(background = "pale green")
            self.message_txt.delete(1.0,4.0)
            if(I_O.cone_flip):
                self.message_txt.insert(1.0," 1. Position the distal cone to balloon body transition at the measurement line.\n")
                self.message_txt.insert(2.0," 2. When the gage is in position, press a Chuck button or the Get Data button to record the positon data.\n") 
            else:
                self.message_txt.insert(1.0," 1. Position the proximal cone to balloon body transition at the measurement line.\n")
                self.message_txt.insert(2.0," 2. When the gage is in position, press a Chuck button or the Get Data button to record the positon data.\n")
            Parameter.selected_param = Parameter.RIGHT_CONE
            
    

    def callback_right_neck(self):
        if(self.Zero_valid):           
            self.clear_BG()
            self.right_neck_pos_lbl.config(background = "pale green")
            self.message_txt.delete(1.0,4.0)
            if(I_O.cone_flip):
                self.message_txt.insert(1.0," 1. Position the proximal cone to proximal neck transition at the measurement line.\n")
                self.message_txt.insert(2.0," 2. When the gage is in position, press a Chuck button or the Get Data button to record the positon data.\n")
            else:
                self.message_txt.insert(1.0," 1. Position the distal cone to distal neck transition at the measurement line.\n")
                self.message_txt.insert(2.0," 2. When the gage is in position, press a Chuck button or the Get Data button to record the positon data.\n")
            Parameter.selected_param = Parameter.RIGHT_NECK
            

    

    def callback_get_data(self):
        if(Parameter.selected_param == Parameter.ZERO):            
            f_pos =float(self.cur_pos_str.get()) 
            if(f_pos == 0.00):
                self.params[Parameter.ZERO].dia = float(self.cur_dia_mm_str.get())
                self.params[Parameter.ZERO].pos = f_pos
                self.left_neck_pos_lbl.config(text = "{:3.2f}".format(f_pos))
                self.Zero_valid = True
                self.clear_BG()
                self.message_txt.delete(1.0,4.0)
                self.selected_mode.callback_D(self)
                return
            else:     
                #self.right_neck_pos_lbl.config(text = "Zero")
                self.message_txt.delete(1.0,4.0)
                self.message_txt.insert(2.0," The position gage must be zero\n") 
        
        if(Parameter.selected_param == Parameter.LEFT_CONE):
            f_pos =float(self.cur_pos_str.get()) 
            self.params[Parameter.LEFT_CONE].dia = float(self.cur_dia_mm_str.get())
            self.params[Parameter.LEFT_CONE].pos = f_pos
            self.left_cone_pos_lbl.config(text = "{:3.2f}".format(f_pos))
            self.clear_BG()
            self.message_txt.delete(1.0,4.0)
            self.Param_G()
            self.Param_B()
            self.Param_H()
            self.selected_mode.callback_A_dia_1(self)
            return

        if(Parameter.selected_param == Parameter.RIGHT_CONE):
            f_pos =float(self.cur_pos_str.get()) 
            self.params[Parameter.RIGHT_CONE].dia = float(self.cur_dia_mm_str.get())
            self.params[Parameter.RIGHT_CONE].pos = f_pos
            self.right_cone_pos_lbl.config(text = "{:3.2f}".format(f_pos))
            self.clear_BG()
            self.message_txt.delete(1.0,4.0)
            self.Param_G()
            self.Param_B()
            self.Param_H()
            self.selected_mode.callback_right_neck(self)
            return
        
        if(Parameter.selected_param == Parameter.RIGHT_NECK):
            f_pos =float(self.cur_pos_str.get()) 
            self.params[Parameter.RIGHT_NECK].dia = float(self.cur_dia_mm_str.get())
            self.params[Parameter.RIGHT_NECK].pos = f_pos
            self.right_neck_pos_lbl.config(text = "{:3.2f}".format(f_pos))
            self.clear_BG()
            self.message_txt.delete(1.0,4.0)
            self.Param_G()
            self.Param_B()
            self.Param_H()
            self.selected_mode.callback_F(self)
            return
        
        if(Parameter.selected_param == Parameter.RIGHT_NECK_F):
            f_dia =float((self.cur_dia_in_str.get().replace("(","")).replace(")",""))
            self.params[Parameter.RIGHT_NECK_F].dia = f_dia
            self.params[Parameter.RIGHT_NECK_F].pos = float(self.cur_pos_str.get())
            self.right_neck_od_F_lbl.config(text = "F {:1.3f} in".format(f_dia))
            self.clear_BG()
            self.message_txt.delete(1.0,4.0)
            return
         
        if(Parameter.selected_param == Parameter.LEFT_NECK_D):
    
            s = self.cur_dia_in_str.get()
            f_dia =float(s.replace("(","").replace(")","")) 
            self.params[Parameter.LEFT_NECK_D].dia = f_dia
            self.params[Parameter.LEFT_NECK_D].pos = float(self.cur_pos_str.get())
            self.left_neck_od_D_lbl.config(text = "D {:1.3f} in".format(f_dia))
            self.clear_BG()
            self.message_txt.delete(1.0,4.0)
            self.selected_mode.callback_left_Cone(self)
            return
            
            

        if(Parameter.selected_param == Parameter.A1):
            f_dia =float(self.cur_dia_mm_str.get()) 
            self.params[Parameter.A1].dia = f_dia
            self.params[Parameter.A1].pos = float(self.cur_pos_str.get())
            self.A1_dia.config(text = "A1 {:1.3f} mm".format(f_dia))
            self.clear_BG()
            self.message_txt.delete(1.0,4.0)
            self.selected_mode.callback_A_dia_2(self)
            return
        
        if(Parameter .selected_param == Parameter.A2):
            f_dia =float(self.cur_dia_mm_str.get()) 
            self.params[Parameter.A2].dia = f_dia
            self.params[Parameter.A2].pos = float(self.cur_pos_str.get())
            self.A2_dia.config(text = "A2 {:1.3f} mm".format(f_dia))
            self.clear_BG()
            self.message_txt.delete(1.0,4.0)
            self.selected_mode.callback_A_dia_3(self)
            return
        
        if(Parameter.selected_param == Parameter.A3):
            f_dia =float(self.cur_dia_mm_str.get()) 
            self.params[Parameter.A3].dia = f_dia
            self.params[Parameter.A3].pos = float(self.cur_pos_str.get())
            self.A3_dia.config(text = "A3 {:1.3f} mm".format( f_dia ))
            self.clear_BG()
            self.message_txt.delete(1.0,4.0)
            self.selected_mode.callback_right_Cone(self)
 
    def next_param(self):
        if(Parameter.selected_param == Parameter.ZERO):            
           self.selected_mode.callback_D(self)
           return
        
        if(Parameter.selected_param == Parameter.LEFT_CONE):
            self.selected_mode.callback_A_dia_1(self)
            return
           
        if(Parameter.selected_param == Parameter.RIGHT_CONE):
            self.selected_mode.callback_right_neck(self)
            return
        
        if(Parameter.selected_param == Parameter.RIGHT_NECK):
            self.selected_mode.callback_F(self)
            return
        
        if(Parameter.selected_param == Parameter.RIGHT_NECK_F):
            Parameter.selected_param = None
            self.clear_BG()
            return
         
        if(Parameter.selected_param == Parameter.LEFT_NECK_D):
            self.selected_mode.callback_left_Cone(self)
            return

        if(Parameter.selected_param == Parameter.A1):
            self.selected_mode.callback_A_dia_2(self)
            return
        
        if(Parameter .selected_param == Parameter.A2):
            self.selected_mode.callback_A_dia_3(self)
            return
        
        if(Parameter.selected_param == Parameter.A3):
            self.selected_mode.callback_right_Cone(self)

 
    

    