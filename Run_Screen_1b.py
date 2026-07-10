import tkinter as tk
from tkinter import ttk,Tk
import pathlib
import pygubu
import time
import platform 
import os
import openpyxl 
from app_config import (
    UI_SCREEN1_FILE,
    DATA_DIR_NAME,
    DEFAULT_TREE_FILE_NAME,
    COLOR_ACTIVE,
    COLOR_INACTIVE,
    COLOR_DEFAULT,
    MODE_LOAD,
    MODE_AUTO,
    MODE_MANUAL,
)
from serial_transfer import COM_DATA
from keyboardlib import VirtualKeyboard
from conversions import CONVERSIONS
from run_manual import rs_manual, Parameter
from run_auto import rs_auto

from screen_2_app import RcSetupPage2App
from io_ import I_O,json_cls
from touch_numeric_keypad import TouchNumericKeypad
from inline_numeric_keypad import InlineNumericKeypad
from keypad_layout import (
    configure_linux_kiosk_window,
    install_linux_keyboard_field,
    prepare_linux_kiosk_for_hide,
    prime_linux_kiosk_keyboard,
)





 

 

PROJECT_PATH = pathlib.Path(__file__).parent
PROJECT_UI = PROJECT_PATH / UI_SCREEN1_FILE



class rs_load:
    pass

class rs_none:
    pass



class RcPage1bApp:
    

    
            


    def __init__(self,my_cd, master=None):


        self.cv = CONVERSIONS(self)

        self.master = master
         
        self.Zero_valid = False

        self.NONE = rs_none
        self.LOAD = rs_load
        self.AUTO = rs_auto
        self.MANUAL = rs_manual
        self.selected_mode = None
        self._target_keypad_win = None
        self._target_keypad_var = None
        self._target_keypad_apply = None
        self._keypad_parent = None
     
        #self.cd = COM_DATA(self)
        self.cd = my_cd

        self.builder = builder = pygubu.Builder()

        self.SP = Parameter
        

        builder.add_resource_path(PROJECT_PATH)
        builder.add_from_file(PROJECT_UI)


        # Main widget
        self.balloonwindow = builder.get_object("SetupFrame", master)
        configure_linux_kiosk_window(self.balloonwindow)
        # Borderless (overrideredirect) Toplevel must accept focus, otherwise
        # USB keyboard events have nowhere to be delivered. Match Screen 2's
        # behaviour and force focus onto the main window after creation.
        try:
            self.balloonwindow.configure(takefocus=True)
            self.balloonwindow.after(50, self.balloonwindow.focus_force)
        except Exception:
            pass

        
        

        self.entry1_text = None
        self.balloon_press_str = None
        self.cur_dia_mm_str = None
        self.cur_dia_in_str = None
        self.cur_pos_str = None
        self.chuck_press_str = None
        self.input_press_str = None
        builder.import_variables(self,
                                 ['entry1_text',
                                  'balloon_press_str',
                                  'cur_dia_mm_str',
                                  'cur_dia_in_str',
                                  'cur_pos_str',
                                  'chuck_press_str',
                                  'input_press_str'])
        


        self.SetupFrame = self.builder.get_object('SetupFrame')
        self._keypad_parent = self.builder.get_object('main_frm')

        directory = PROJECT_PATH / DATA_DIR_NAME
            # Get all filenames with .xlsx extension in the specified directory
        self.File_Names = [filename for filename in os.listdir(directory) if filename.endswith('.xlsx')]
        

        self.entry1_ = self.builder.get_object('entry1_')
        self.bn_setup = self.builder.get_object('bn_setup')
        I_O.load_lot_number(self)
        # Stripping file extensions
        #self.entry1_['value'] = [os.path.splitext(filename)[0] for filename in self.File_Names]



        self.bal_track_btn = self.builder.get_object('bal_track_btn')
        self.chuck_track_btn = self.builder.get_object('chuck_track_btn')
        
        self.dist_chuck_btn = self.builder.get_object('dist_chuck_btn')
        self.prox_chuck_btn = self.builder.get_object('prox_chuck_btn')
        self.dist_clamp_btn = self.builder.get_object('dist_clamp_btn')
        self.prox_clamp_btn = self.builder.get_object('prox_clamp_btn')
        self.tree =  self.builder.get_object('treeview1')

        self.balloon_press_str.set("")
        self.chuck_press_str.set("")
        self.input_press_str.set("")

        self.cur_dia_in_str.set("")
        self.cur_dia_mm_str.set("")
        self.cur_pos_str.set("")

        self.message_txt = self.builder.get_object('message_txt',master)
        
        self.bal_press_frm = self.builder.get_object('bal_press_frm')
        self.chuck_press_frm = self.builder.get_object('chuck_press_frm')
        self.input_press_frm = self.builder.get_object('input_press_frm')
        self.pos_mm_frm = self.builder.get_object('pos_mm_frm')
        
        self.A1_dia = self.builder.get_object('body_A_Left_lbl', self)
        self.A2_dia = self.builder.get_object('body_A_mid_lbl', self)
        self.A3_dia = self.builder.get_object('body_A_right_lbl', self)
        
        self.left_neck_pos_lbl = self.builder.get_object('zero_pos_lbl', self) # right neck start zero
        self.left_cone_pos_lbl = self.builder.get_object('dis_cone_pos_lbl', self)
        
        self.right_cone_pos_lbl = self.builder.get_object('prox_cone_pos_lbl', self)
        self.right_neck_pos_lbl = self.builder.get_object('prox_neck_pos_lbl', self)
        
        self.cone_G_lbl = self.builder.get_object('cone_G_lbl',self)
        self.body_B_lbl = self.builder.get_object('body_B_lbl',self)
        self.cone_H_lbl = self.builder.get_object('cone_H_lbl',self)

        self.left_neck_od_D_lbl = self.builder.get_object('distal_neck_od_D_lbl',self)
        self.right_neck_od_F_lbl = self.builder.get_object('prox_neck_od_F_lbl',self)
        
        self.Load_Balloon_btn = self.builder.get_object('Load_Balloon_btn',self)
        
        self.Auto_btn = self.builder.get_object('Auto_btn',self)
        self.Manual_btn = self.builder.get_object('Manual_btn',self)
        self.message_txt = self.builder.get_object('message_txt',self)

        self.tree_scrollbar = self.builder.get_object('tree_scrollbar',self)
        self.i_o = I_O(self) 
        self.j = json_cls(self)
        read_data = self.j.read_from_json()

        self.setup_pic_Labels()
       
        self.setup_ttk_styles()
        self.tree.config(yscrollcommand = self.tree_scrollbar.set)
        
        self.clear_params()
        self.clear_Buttons()
        
        
        builder.connect_callbacks(self)
        self._configure_touch_screen_buttons()

        self.cd.set_master(self)
        self.tree_scrollbar.config(command=self.tree.yview)
        
        #self.j = json_cls(self)

        #self.j.write_to_json(COM_DATA.target_balloon_pressure, COM_DATA.target_chuck_pressure, self.cv.CurBalUnits,self.cv.CurClampUnits, self.cv.CurDiaUnits, self.cv.CurPosUnits)

        #read_data = self.j.read_from_json()
        self.TreeFileName =""
     
        COM_DATA.target_balloon_pressure=read_data['target_balloon_pressure'] 
        COM_DATA.target_chuck_pressure=read_data['target_chuck_pressure']
        self.cv.CurBalUnits=read_data['cur_bal_units']
        self.cv.CurClampUnits=read_data['cur_clamp_units']
        self.cv.CurDiaUnits=read_data['cur_dia_units']
        self.cv.CurPosUnits=read_data['cur_pos_units']
        self.TreeFileName = read_data['tree_file_name']   

        self.entry1_.configure(state="normal")
        try:
            self.entry1_.configure(takefocus=True)
        except tk.TclError:
            pass
        install_linux_keyboard_field(self.entry1_)
        self.bn_setup.bind(
            "<ButtonPress-1>",
            lambda _e: prepare_linux_kiosk_for_hide(self.balloonwindow, self.entry1_),
            add="+",
        )
        self.entry1_.bind("<Return>", self.on_change)
        self.entry1_.bind("<KP_Enter>", self.on_change)
        self.entry1_.bind("<FocusOut>", self.on_change)
        self.entry1_.set(DEFAULT_TREE_FILE_NAME)
        self.TreeFileName = DEFAULT_TREE_FILE_NAME
        


        I_O.load_xl_files(self,self.TreeFileName, self.tree)
      


    


    def callback_tree_scroll(self, mode=None, value=None, units=None):
        pass

            
    def on_change(self,event):
        if(self.entry1_.get() != self.TreeFileName):
            self.TreeFileName=self.entry1_.get()
            I_O.load_xl_files(self,self.TreeFileName, self.tree)


    def clear_treeview(self,tree):
        # Clearing all the rows
        for item in tree.get_children():
            tree.delete(item)
        
        # Clearing all the columns
        tree.configure(columns=())
     

    def setup_tree(self):   
     #   cols = ("Dist. OD\n (inch)","Dist. Cone Length (mm)","Body Length (mm)","ΦA1 (mm)","ΦA2 (mm)","ΦA3 (mm)","Prox. Cone\nLength (mm)","Prox.OD\n (inch)")
        if(I_O.cone_flip):
            cols = ("Index", "Prox. OD (inch)","Prox. Cone Length (mm)","Body Length (mm)","ΦA1 (mm)","ΦA2 (mm)","ΦA3 (mm)","Dist. Cone Length (mm)","Dist.OD (inch)")
        else:    
            cols = ("Index", "Dist. OD (inch)","Dist. Cone Length (mm)","Body Length (mm)","ΦA1 (mm)","ΦA2 (mm)","ΦA3 (mm)","Prox. Cone Length (mm)","Prox.OD (inch)")
        colswidth = (30,110,150,110,100,100,100,150,115)
        #colswidth = (115,100)
        self.tree['columns'] = cols

       # self.setup_ttk_styles()
       # style = ttk.Style()
       # print(self.tree.winfo_class())
       # print(style.layout('MyTView.Treeview.Heading'))


        self.tree.column('#0', width = 0, anchor = 'center', stretch = 'NO')
        i=0
        for n in cols:
            self.tree.column(str(n), width = colswidth[i], anchor='center' )
            if(i==0):
                self.tree.heading(str(n), text="")
            else:
                self.tree.heading(str(n), text=n)
            i+=1
        
    def setup_pic_Labels(self):      
        if(I_O.cone_flip):
            # ZERO=0    LEFT_CONE=1   RIGHT_CONE=2    RIGHT_NECK=3    A1=4      A2=5    A3=6    LEFT_NECK_D=7    RIGHT_NECK_F = 8    CONE_G=9    BODY_B=10    CONE_H=11
            self.params = [ Parameter( self.left_neck_pos_lbl, " Zero ",self ),                      #ZERO=0 
                                    Parameter( self.left_cone_pos_lbl, "Prox Cone",self ),   #DISTAL_CONE=1     
                                    Parameter( self.right_cone_pos_lbl, "Dist Cone",self ),  #PROX_CONE=2
                                    Parameter( self.right_neck_pos_lbl, "Dist Neck",self ),  #PROX_NECK=3
                                    Parameter( self.A1_dia, " A-1 ",self ),                  #A1=4   
                                    Parameter( self.A2_dia, " A-2 ",self ),                  #A2=5
                                    Parameter( self.A3_dia, " A-3 ",self ),                  #A3=6
                                    Parameter( self.left_neck_od_D_lbl, " D ",self ),     #DISTAL_NECK_D=7 
                                    Parameter( self.right_neck_od_F_lbl, " F ",self ),       #PROX_NECK_F=8     
                                    Parameter( self.cone_G_lbl, " G ",self ),               #CONE_G=9
                                    Parameter( self.body_B_lbl, " B ",self ),               #BODY_B=10
                                    Parameter( self.cone_H_lbl, " H ",self )                #CONE_H=11
            ]
        else:    
         #DISTAL_CONE=1 #PROX_CONE=2  PROX_NECK=3 #A1=4 #A2=5 #A3=6 #DISTAL_NECK_D=7 #PROX_NECK_F = 8    #CONE_G=9        #BODY_B=10        #CONE_H=11
    
            self.params = [ Parameter( self.left_neck_pos_lbl, " Zero ",self ),                      #ZERO=0 
                                    Parameter( self.left_cone_pos_lbl, "Dist Cone",self ),   #DISTAL_CONE=1     
                                    Parameter( self.right_cone_pos_lbl, "Prox Cone",self ),  #PROX_CONE=2
                                    Parameter( self.right_neck_pos_lbl, "Prox Neck",self ),  #PROX_NECK=3
                                    Parameter( self.A1_dia, " A-1 ",self ),                  #A1=4   
                                    Parameter( self.A2_dia, " A-2 ",self ),                  #A2=5
                                    Parameter( self.A3_dia, " A-3 ",self ),                  #A3=6
                                    Parameter( self.left_neck_od_D_lbl, " D ",self ),     #DISTAL_NECK_D=7 
                                    Parameter( self.right_neck_od_F_lbl, " F ",self ),       #PROX_NECK_F=8     
                                    Parameter( self.cone_G_lbl, " G ",self ),               #CONE_G=9
                                    Parameter( self.body_B_lbl, " B ",self ),               #BODY_B=10
                                    Parameter( self.cone_H_lbl, " H ",self )                #CONE_H=11
            ]    




    def callback_dist_chuck(self):
        COM_DATA.left_chuck = 1

    def callback_prox_chuck(self):
        COM_DATA.right_chuck = 1

    def callback_dist_clamp(self):
        COM_DATA.left_clamp = 1

    def callback_prox_clamp(self):
        COM_DATA.right_clamp = 1

    def callback_save_data(self):
        I_O.write_xl_file(self , self.entry1_.get())
    
    def callback_clear_data(self):
        # Clearing all the rows
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Clearing all the columns
        self.tree.configure(columns=())
    #    I_O.cone_flip = not I_O.cone_flip
        self.setup_tree()
        self.setup_pic_Labels()
        self.clear_params()
      
        

    def add_line_tree(self):   
        my_index = len(self.tree.get_children())+1
        self.tree.insert(parent='',index = 'end' , iid=my_index, values=(my_index,
                                                              self.params[Parameter.LEFT_NECK_D].name,
                                                              self.params[Parameter.CONE_G].name,
                                                              self.params[Parameter.BODY_B].name,
                                                              self.params[Parameter.A1].name,
                                                              self.params[Parameter.A2].name,
                                                              self.params[Parameter.A3].name,
                                                              self.params[Parameter.CONE_H].name,
                                                              self.params[Parameter.RIGHT_NECK_F].name))
        
        #print(self.tree.get_children())
   
    #s1=s.replace("$","")
    def float_check(self, value,text):
        if(value==None): 
            return text
        else: 
            return "{:1.3f}".format(value)

    def update_tree(self):
            selected = self.tree.get_children()[-1]
            
            value = self.tree.item(selected, 'values' )
           # print(self.tree.get_children())
           # print(selected)
       #     my_value = (self.params[Parameter.DISTAL_NECK_D].obj.cget("text"),
       #                 self.params[Parameter.CONE_G].obj.cget("text"),
       #                 self.params[Parameter.BODY_B].obj.cget("text"),
       #                 self.params[Parameter.A1].obj.cget("text"),
       #                 self.params[Parameter.A2].obj.cget("text"),
       #                 self.params[Parameter.A3].obj.cget("text"),
       #                 self.params[Parameter.CONE_H].obj.cget("text"),
       #                 self.params[Parameter.PROX_NECK_F].obj.cget("text")
       #             )

            my_value= ( value[0], 
                        self.float_check(self.params[Parameter.LEFT_NECK_D].dia,value[1]),
                        self.float_check(self.params[Parameter.CONE_G].pos,value[2]),
                        self.float_check(self.params[Parameter.BODY_B].pos,value[3]),
                        self.float_check(self.params[Parameter.A1].dia,value[4]),
                        self.float_check(self.params[Parameter.A2].dia,value[5]),
                        self.float_check(self.params[Parameter.A3].dia,value[6]),
                        self.float_check(self.params[Parameter.CONE_H].pos,value[7]),
                        self.float_check(self.params[Parameter.RIGHT_NECK_F].dia,value[8])
                      )
           

            """
            my_value=(  if(self.params[Parameter.DISTAL_NECK_D].dia==None): "{:1.3f}".format(self.params[Parameter.DISTAL_NECK_D].dia),
                        "{:1.3f}".format(self.params[Parameter.CONE_G].pos),
                        "{:1.3f}".format(self.params[Parameter.BODY_B].pos),
                        "{:1.3f}".format(self.params[Parameter.A1].dia),
                        "{:1.3f}".format(self.params[Parameter.A2].dia),
                        "{:1.3f}".format(self.params[Parameter.A3].dia),
                        "{:1.3f}".format(self.params[Parameter.CONE_H].pos),
                        "{:1.3f}".format(self.params[Parameter.PROX_NECK_F].dia)
                     )
            """

            #print(my_value)
            selected = self.tree.get_children()[-1] 
            self.tree.item(selected,text=str(selected), values = my_value)  



    
    def run(self):
        self.balloonwindow.mainloop()
    
    def _configure_touch_screen_buttons(self):
        """Prevent bottom-row tk buttons from staying sunken/pressed on touch."""
        bottom_buttons = (
            "Load_Balloon_btn",
            "Auto_btn",
            "Manual_btn",
            "bn_exit",
            "bn_setup",
            "get_data_btn",
            "set_bal_target_btn",
            "set_chuck_target_btn",
            "button_save_data",
            "button1",
            "dist_chuck_btn",
            "prox_chuck_btn",
            "dist_clamp_btn",
            "prox_clamp_btn",
        )

        def _reset_button(button):
            try:
                bg = button.cget("background")
                fg = button.cget("foreground")
                if not bg:
                    bg = COLOR_DEFAULT
                button.config(
                    background=bg,
                    activebackground=bg,
                    activeforeground=fg,
                    relief=tk.RAISED,
                    highlightthickness=0,
                    takefocus=0,
                )
            except tk.TclError:
                pass

        for oid in bottom_buttons:
            btn = self.builder.get_object(oid)
            _reset_button(btn)

            def _on_release(event=None, button=btn):
                _reset_button(button)
                button.after_idle(lambda b=button: _reset_button(b))
                button.after(120, lambda b=button: _reset_button(b))

            btn.bind("<ButtonRelease-1>", _on_release, add="+")
            btn.bind("<Leave>", _on_release, add="+")

    def setup_ttk_styles(self):
        # ttk styles configuration
        style = ttk.Style()

  
        #style.theme_use("forest-light")  
        optiondb = style.master



        style.configure("MyTView.Treeview.Heading",font=(None, 8), background="green2", foreground="black")
        #style.configure("Treeview.Heading", font=(None, 5))
        #load_data()


    def btn_exit(self):
        self.cd.deinit() 
        self.master.destroy()
    # self.balloonwindow.destroy()        
        

    def btn_setup(self):
        prepare_linux_kiosk_for_hide(self.balloonwindow, self.entry1_)
        try:
            self.balloonwindow.withdraw()
        except tk.TclError:
            pass
        setup_win = RcSetupPage2App(self.cd, self.cv, self, self.master)
        setup_win.run()
        try:
            self.balloonwindow.deiconify()
        except tk.TclError:
            pass
        prime_linux_kiosk_keyboard(self.balloonwindow)
        try:
            self.entry1_.configure(state="normal")
        except tk.TclError:
            pass

    @staticmethod
    def _parse_float(s):
        if s is None:
            return None
        try:
            return float(str(s).strip())
        except (TypeError, ValueError):
            return None

    def _target_keypad_class(self):
        return InlineNumericKeypad if platform.system() == "Linux" else TouchNumericKeypad

    def _format_target_display(self, target_kind):
        if target_kind == "balloon":
            v = self.cv.to_cur_bal_units(COM_DATA.target_balloon_pressure, "psi")
            if self.cv.CurBalUnits == "psi":
                return "{:3.1f} ".format(v)
            return "{:2.1f} ".format(v)
        v = self.cv.to_cur_clamp_units(COM_DATA.target_chuck_pressure, "psi")
        if self.cv.CurClampUnits == "psi":
            return "{:3.0f} ".format(v)
        return "{:2.1f} ".format(v)

    def _target_keypad_title(self, target_kind):
        if target_kind == "balloon":
            return "Balloon Pressure Target ({})".format(self.cv.get_cur_bal_units())
        return "Chuck Pressure Target ({})".format(self.cv.get_cur_clamp_units())

    def _open_target_keypad(self, target_kind):
        if self._target_keypad_var is None:
            self._target_keypad_var = tk.StringVar(self.master)

        if target_kind == "balloon":
            apply_fn = self._apply_balloon_target_from_keypad
        else:
            apply_fn = self._apply_chuck_target_from_keypad
        self._target_keypad_apply = apply_fn
        title = self._target_keypad_title(target_kind)

        def on_exit():
            if self._target_keypad_apply is not None:
                self._target_keypad_apply()
            self._target_keypad_win = None
            self._target_keypad_apply = None

        if self._target_keypad_win is not None:
            try:
                if self._target_keypad_win.winfo_exists():
                    side = "left" if target_kind == "balloon" else "right"
                    self._target_keypad_win.set_target(
                        self._target_keypad_var, on_exit=on_exit, side=side, title=title
                    )
                    self._target_keypad_win.lift()
                    return
            except tk.TclError:
                pass
            self._target_keypad_win = None

        keypad_cls = self._target_keypad_class()
        side = "left" if target_kind == "balloon" else "right"
        self._target_keypad_win = keypad_cls(
            self._keypad_parent, self._target_keypad_var, on_exit=on_exit, side=side, title=title
        )

    def _apply_balloon_target_from_keypad(self):
        v = self._parse_float(self._target_keypad_var.get())
        if v is None:
            return
        psi = self.cv.cnvrt_press_units(v, self.cv.CurBalUnits, "psi")
        if psi is None:
            return
        COM_DATA.target_balloon_pressure = max(0.0, min(150.0, round(psi * 10.0) / 10.0))

    def _apply_chuck_target_from_keypad(self):
        v = self._parse_float(self._target_keypad_var.get())
        if v is None:
            return
        psi = self.cv.cnvrt_press_units(v, self.cv.CurClampUnits, "psi")
        if psi is None:
            return
        COM_DATA.target_chuck_pressure = max(0.0, min(150.0, float(round(psi))))

    def callback_set_balloon_target(self):
        self._open_target_keypad("balloon")

    def callback_set_chuck_target(self):
        self._open_target_keypad("chuck")



    def clear_params(self):    
        self.selected_param = None
        for param in self.params:
            param.obj.config(background = COLOR_DEFAULT, text = param.name)
            param.dia = None
            param.pos = None

                
    def clear_G_B_H(self):
        i = Parameter.LEFT_CONE
        while i <= Parameter.RIGHT_NECK:
            param = self.params[i]  
            param.obj.config(background = COLOR_DEFAULT, text = param.name)
            param.dia = None
            param.pos = None
            i = i + 1
        self.Param_G()
        self.Param_B()
        self.Param_H() 


    def clear_BG(self):    
        for param in self.params:
            param.obj.config(background = COLOR_DEFAULT)  

    def clear_Buttons(self):    
        self.Auto_btn.config(background = COLOR_DEFAULT,activebackground=COLOR_DEFAULT)
        self.Manual_btn.config(background = COLOR_DEFAULT,activebackground=COLOR_DEFAULT)
        self.Load_Balloon_btn.config(background = COLOR_DEFAULT,activebackground=COLOR_DEFAULT)
        self.message_txt.delete(1.0,4.0)               


    def set_cur_press(self, cur_press_psi):
        if cur_press_psi is None:
            myStr = ""
        elif(self.cv.CurBalUnits=='psi'):
            myStr = "{:3.1f} ".format(self.cv.to_cur_bal_units(cur_press_psi,'psi'))
        else:
            myStr = "{:2.2f} ".format(self.cv.to_cur_bal_units(cur_press_psi,'psi'))
        if self.balloon_press_str.get()!=myStr:
            self.bal_press_frm.config(text="Balloon Pressure  "+self.cv.get_cur_bal_units())
            self.balloon_press_str.set(myStr)

    def set_cur_clamp_press(self, cur_press_psi):
        if cur_press_psi is None:
            myStr = ""
        elif(self.cv.CurClampUnits=='psi'):
            myStr = "{:3.1f} ".format(self.cv.to_cur_clamp_units(cur_press_psi,'psi'))
        else:
            myStr = "{:2.2f} ".format(self.cv.to_cur_clamp_units(cur_press_psi,'psi'))        
        if self.chuck_press_str.get()!=myStr:
            self.chuck_press_frm.config(text="Chuck Pressure  "+self.cv.get_cur_clamp_units())
            self.chuck_press_str.set(myStr)

    def set_cur_input_press(self, cur_press_psi):
        if(self.cv.CurBalUnits=='psi'):
            myStr = "{:3.1f} ".format(self.cv.to_cur_bal_units(cur_press_psi,'psi'))
        else:
            myStr = "{:2.2f} ".format(self.cv.to_cur_bal_units(cur_press_psi,'psi'))
        if self.input_press_str.get()!=myStr:
            self.input_press_frm.config(text="Input Pressure  "+self.cv.get_cur_bal_units())
            self.input_press_str.set(myStr)


    '''
    def set_cur_press(self, cur_press_psi):
        myStr = "{:3.1f} ".format(self.cv. cur_press_psi*0.068046)
        if self.balloon_press_str.get()!=myStr:
            self.balloon_press_str.set(myStr)
    
    def set_cur_clamp_press(self,cur_clamp_psi):
        myStr = "{:3.1f} ".format(cur_clamp_psi*0.068046)
        if self.chuck_press_str.get()!=myStr:
            self.chuck_press_str.set(myStr)
    '''
             
    def set_cur_dia(self, cur_dia_mm):
        if cur_dia_mm is None:
            myStr = ""
            inchStr = ""
        else:
            myStr = "{:3.2f}".format(cur_dia_mm)
            inchStr = " ({:2.3f})".format(cur_dia_mm * 0.03937007874)
        if self.cur_dia_mm_str.get() != myStr:
            self.cur_dia_mm_str.set(myStr)
        if self.cur_dia_in_str.get() != inchStr:
            self.cur_dia_in_str.set(inchStr)
    
    def set_cur_pos(self, cur_pos_mm):
        if cur_pos_mm is None:
            myStr = ""
        else:
            if self.cv.CurPosUnits == 'inch':
                myStr = "{:2.3f}".format(self.cv.to_cur_pos_units(cur_pos_mm, "mm"))
            else:
                myStr = "{:3.2f}".format(self.cv.to_cur_pos_units(cur_pos_mm, 'mm'))

        if self.cur_pos_str.get() != myStr:
            self.pos_mm_frm.config(text="Position  "+self.cv.get_cur_pos_units())
            self.cur_pos_str.set(myStr)

    def callback_G(self, event=None):
            pass

    def callback_B(self, event=None):
            pass

    def callback_H(self, event=None):
           pass
    
    def callback_D(self, event=None):
        if(self.selected_mode==self.MANUAL):
            self.selected_mode.callback_D(self)
        if(self.selected_mode==self.AUTO):
            self.selected_mode.callback_D(self)

    def callback_F(self, event=None):
        if(self.selected_mode==self.MANUAL):
            self.selected_mode.callback_F(self)

    def callback_A_dia_1(self, event=None):
        if(self.selected_mode==self.MANUAL):
            self.selected_mode.callback_A_dia_1(self)

    def callback_A_dia_2(self, event=None):
        if(self.selected_mode==self.MANUAL):
            self.selected_mode.callback_A_dia_2(self)
     
    def callback_A_dia_3(self, event=None):
        if(self.selected_mode==self.MANUAL):
            self.selected_mode.callback_A_dia_3(self)

    def callback_0(self, event=None):
        if(self.selected_mode==self.MANUAL):
            self.selected_mode.callback_0(self)

    def callback_left_Cone(self, event=None):
        if(self.selected_mode==self.MANUAL):
            self.selected_mode.callback_left_Cone(self)
        

    def callback_right_Cone(self, event=None):
        if(self.selected_mode==self.MANUAL):
            self.selected_mode.callback_right_Cone(self)
    

    def callback_right_neck(self, event=None):
        if(self.selected_mode==self.MANUAL):
            self.selected_mode.callback_right_neck(self)
       
    def callback_get_data(self):
        try:
            selected = self.tree.get_children()[-1]
        except:
            return
        if(self.selected_mode==self.MANUAL):
            self.selected_mode.callback_get_data(self)
        if(self.selected_mode==self.AUTO):
            self.selected_mode.callback_get_data(self)
        self.update_tree()


    
        
  
    def Param_G(self):
        try:
            self.params[Parameter.CONE_G].dia = None
            self.params[Parameter.CONE_G].pos = self.params[Parameter.LEFT_CONE].pos-self.params[Parameter.ZERO].pos  
            self.cone_G_lbl.config(text = "G {:3.2f} mm".format( self.params[Parameter.CONE_G].pos))
            return
        except:
            param=self.params[Parameter.CONE_G]
            param.obj.config(background = "white", text = param.name)

           

    def Param_B(self):
        try:
            self.params[Parameter.BODY_B].dia = None
            self.params[Parameter.BODY_B].pos = self.params[Parameter.RIGHT_CONE].pos-self.params[Parameter.LEFT_CONE].pos
            self.body_B_lbl.config(text = "B {:3.2f} mm".format( self.params[Parameter.BODY_B].pos))
            return
        except:
            param=self.params[Parameter.BODY_B]
            param.obj.config(background = "white", text = param.name)

    def Param_H(self):
        try:
            self.params[Parameter.CONE_H].dia = None
            self.params[Parameter.CONE_H].pos = self.params[Parameter.RIGHT_NECK].pos-self.params[Parameter.RIGHT_CONE].pos
            self.cone_H_lbl.config(text = "H {:3.2f} mm".format( self.params[Parameter.CONE_H].pos))
            return
        except:
            param=self.params[Parameter.CONE_H]
            param.obj.config(background = "white", text = param.name)



    def callback_lot_number_bp(self, event=None):
       # entry = self.builder.get_object('entry1', self.master)
       # VirtualKeyboard(entry)
       pass 

    def file_name_cb(self, event=None):
        pass

    def callback(self, event=None):
        pass

    def callback_NEXT(self, event=None):
        pass

    def bal_btn_bg(self):
        if(COM_DATA.enable_balloon_tracking):
            self.bal_track_btn.config( bg = COLOR_ACTIVE,activebackground=COLOR_ACTIVE)
        else:
            self.bal_track_btn.config( bg = COLOR_INACTIVE,activebackground= COLOR_INACTIVE)

   # def callback_bal_track_btn_(self, event=None):
    #    self.callback_bal_track_btn()

    def callback_bal_track_btn(self):
        COM_DATA.enable_balloon_tracking = not COM_DATA.enable_balloon_tracking
        self.bal_btn_bg()
            

    def set_cur_rt_chuck(self, right_clamp_state):
        self.prox_chuck_bg(right_clamp_state)

    def set_cur_lft_chuck(self, left_clamp_state):
        self.distal_chuck_bg(left_clamp_state)
   
    def set_cur_rt_clamp(self,mitutoyo_button):
            self.prox_clamp_bg(mitutoyo_button)

    def set_cur_lft_clamp(self,diameter_button):
            self.distal_clamp_bg(diameter_button)
                    

    def test_bal_track(self):
        if(self.selected_mode == self.LOAD):
            
            if COM_DATA.left_chuck_state and COM_DATA.right_chuck_state and COM_DATA.right_chuck == 0 and COM_DATA.left_chuck == 0:
                 COM_DATA.enable_balloon_tracking = True
                 self.bal_btn_bg()
            else:
                 COM_DATA.enable_balloon_tracking = False
                 self.bal_btn_bg()

    def _set_toggle_btn_state(self, btn, active):
        color = COLOR_ACTIVE if active else COLOR_INACTIVE
        btn.config(bg=color, activebackground=color, relief=tk.RAISED)

    def distal_chuck_bg(self, sol):
        self._set_toggle_btn_state(self.dist_chuck_btn, sol)
        self.test_bal_track()

    def prox_chuck_bg(self, sol):
        self._set_toggle_btn_state(self.prox_chuck_btn, sol)
        self.test_bal_track()

    def distal_clamp_bg(self, sol):
        self._set_toggle_btn_state(self.dist_clamp_btn, sol)

    def prox_clamp_bg(self, sol):
        self._set_toggle_btn_state(self.prox_clamp_btn, sol)

    def chuck_btn_bg(self):
        if(COM_DATA.enable_chuck_tracking):
            self.chuck_track_btn.config( bg = COLOR_ACTIVE,activebackground=COLOR_ACTIVE)
        else:
            self.chuck_track_btn.config( bg = COLOR_INACTIVE,activebackground=COLOR_INACTIVE)

    def callback_chuck_track_btn(self):
        COM_DATA.enable_chuck_tracking = not COM_DATA.enable_chuck_tracking
        self.chuck_btn_bg()
        
       

    def callback_Load_Button(self, event=None):
        if self.selected_mode != self.LOAD:
            self.clear_params()
            self.clear_Buttons()
            self.Load_Balloon_btn.config( bg = COLOR_ACTIVE, activebackground= COLOR_ACTIVE)
            self.selected_mode = self.LOAD  # load balloon  
            self.message_txt.delete(1.0,4.0)               
            self.message_txt.insert(1.0," 1. Load the balloon, then press the right and left chuck buttons.\n")
            self.message_txt.insert(2.0," 2. Position and press the left clamp button.\n")
            self.message_txt.insert(3.0," 3. Wait from the balloon to reach the target pressure, then press then press the rightsd rail clamp button.\n")

            if(COM_DATA.right_chuck_state):
                COM_DATA.right_chuck = 1
            if(COM_DATA.left_chuck_state):
                COM_DATA.left_chuck = 1
            if(COM_DATA.right_clamp_state):
                COM_DATA.right_clamp = 1
            if(COM_DATA.left_clamp_state):
                COM_DATA.left_clamp = 1
            COM_DATA.enable_chuck_tracking = True
            self.chuck_btn_bg()
            COM_DATA.enable_balloon_tracking = False
            self.bal_btn_bg()
        

            self.Zero_valid = False
            COM_DATA.mode = MODE_LOAD
            self.add_line_tree()
  
        else:
            self.clear_Buttons()
            self.selected_mode = None
            self.cd.mode 



    def callback_Auto(self, event=None):
        if self.selected_mode != self.AUTO:
            self.clear_Buttons()
            self.Auto_btn.config( bg = COLOR_ACTIVE, activebackground= COLOR_ACTIVE)
            if self.selected_mode == self.MANUAL: # Auto take data
                self.selected_mode = self.AUTO  # Auto take data
                if(Parameter.last_selected_param==None):
                    Parameter.selected_param == self.params[Parameter.ZERO].selected_param
                else:  
                    Parameter.selected_param = Parameter.last_selected_param
                COM_DATA.mode = MODE_AUTO
                self.selected_mode.next_param(self)
            else:
                self.selected_mode = self.AUTO  # Auto take data
                if(self.params[Parameter.ZERO].name==" Zero "):
                    Parameter.selected_param == self.params[Parameter.ZERO].selected_param
                    COM_DATA.mode = MODE_AUTO
                    self.selected_mode.callback_0(self)
        else:
            self.clear_Buttons()
            self.selected_mode = None
            COM_DATA.mode = MODE_LOAD
       

    def callback_Manual(self, event=None):
        if self.selected_mode != self.MANUAL:
            Parameter.last_selected_param=None
            #Parameter.selected_param = None
            self.clear_Buttons()
            self.Manual_btn.config( bg = COLOR_ACTIVE, activebackground=COLOR_ACTIVE)
            self.message_txt.delete(1.0,4.0)               
            if(not self.Zero_valid):
                self.message_txt.insert(1.0," Zero postion not set.  You must set Zero position to start taking data.\n")
                self.message_txt.insert(2.0," Press the ""Zero"" label to start.\n")
            self.selected_mode = self.MANUAL  # Manual take data   
            COM_DATA.mode = MODE_MANUAL
        else:
            self.clear_Buttons()
            self.selected_mode = None
            COM_DATA.mode = MODE_LOAD
       
   
 
                
    
if __name__ == "__main__":
   
    root = tk.Tk()
    from keypad_layout import configure_linux_app_root
    configure_linux_app_root(root)
  #  I_O.cone_flip = False
    cd = COM_DATA(root)

    app = RcPage1bApp(cd,root)
    app.run()
    
    
        
        

        