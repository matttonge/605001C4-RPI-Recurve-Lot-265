import tkinter as tk
from tkinter import ttk,Tk
import pathlib
import pygubu
from app_config import APP_SOFTWARE_MODEL_REV, DATA_DIR_NAME, STARTUP_JSON_NAME
from conversions import CONVERSIONS
import time
import datetime
import openpyxl 
import json
import platform 
import os

PROJECT_PATH = pathlib.Path(__file__).parent

class I_O:
    
    cone_flip = True
    Software_Model_Rev = APP_SOFTWARE_MODEL_REV
     
    if (platform.system()=="Windows"): 
        path_1 = str(DATA_DIR_NAME + '\\')
    else:
        path_1 = str(DATA_DIR_NAME + '/')
  #  path_1 = "/RC_Measurment_Sys_9_20_23/I_O/"

    def __init__(self, parent):
        self.parent = parent
       

    def load_xl_files(self,lot_number, treeview):
        workbook = openpyxl.load_workbook(I_O.path_1+lot_number+".xlsx")
        sheet= workbook.active
        list_values = list(sheet.values)
        lk=list_values[0]
        if(lk[1] =='Prox. OD (inch)'):
           I_O.cone_flip = 1
        else: I_O.cone_flip = 0
        self.clear_treeview(treeview)
       # for col_name in list_values[0]:
       #     treeview.heading(col_name, text=col_name)
        self.setup_tree()
        for item in treeview.get_children():
                treeview.delete(item)            
        for value_tuple in list_values[1:]:
            treeview.insert('', tk.END, values=value_tuple)

       
       
    def load_lot_number(self):
        directory = PROJECT_PATH / DATA_DIR_NAME
            # Get all filenames with .xlsx extension in the specified directory
        File_Names = [filename for filename in os.listdir(directory) if filename.endswith('.xlsx')]
        
        # Stripping file extensions
        self.entry1_['value'] = [os.path.splitext(filename)[0] for filename in File_Names]




    def write_xl_file(self, lot_num):
        
        workbook = openpyxl.Workbook()
        sheet= workbook.active
        header_text=[]
        for column in self.tree["columns"]:
            header_text.append(self.tree.heading(column)["text"])
        sheet.append(header_text)   
        row_lists = []
        for child_item in self.tree.get_children():
            row_values = self.tree.item(child_item)["values"]
            i=0
            for value in row_values:
                try: 
                    row_values[i] = float(row_values[i])
                except:
                    row_values[i] =""
                i+=1
            sheet.append(row_values)   
        if lot_num == "":
            fname= 'Temp_'+ datetime.datetime.now().strftime("%Y-%m-%d_%H_%M")
            workbook.save(I_O.path_1+fname+".xlsx")
        else:
            file_path = I_O.path_1+str(lot_num)+".xlsx"
            tmp_file_path = file_path
            if(os.path.exists(tmp_file_path)):
                n=1
                tmp_file_path = I_O.path_1+str(lot_num)+".bak"+str(n)
                while(os.path.exists(tmp_file_path)):
                    n=n+1
                    tmp_file_path = I_O.path_1+str(lot_num)+".bak"+str(n)
                os.rename(file_path, tmp_file_path)        
            workbook.save(file_path)
        I_O.load_lot_number(self)
           


class json_cls:

    def __init__(self,master):
      self.m = master

    def write_to_json(self,bal_pres,chuck_pres,bal_u,clamp_u,dia_u,pos_u,tree_file_name ):
        data = {
            'target_chuck_pressure': chuck_pres,
            'target_balloon_pressure': bal_pres,
            'cur_bal_units': bal_u,
            'cur_clamp_units': clamp_u,
            'cur_dia_units': dia_u,
            'cur_pos_units': pos_u,
            'cone_flip':I_O.cone_flip,
            'tree_file_name': tree_file_name
        }
        """
        Write data to a JSON file.
        
        Parameters:
        data (dict): The data to be written to the file.
        filename (str): The name of the file to write to.
        """
        with open(str(PROJECT_PATH / STARTUP_JSON_NAME), 'w') as f:
            json.dump(data, f, indent=4)

    def read_from_json(self):
        """
        Read data from a JSON file.
        
        Parameters:
        filename (str): The name of the file to read from.
        
        Returns:
        dict: The data read from the file.
        """
        with open(str(PROJECT_PATH / STARTUP_JSON_NAME), 'r') as f:
            data = json.load(f)
            I_O.cone_flip = data['cone_flip']
        return data

